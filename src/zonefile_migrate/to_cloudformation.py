import click
import re
from slugify import slugify
from encodings import idna
import encodings.idna

from pathlib import Path
from ruamel.yaml import YAML, CommentedMap
from zonefile_migrate.logger import log
from easyzone import easyzone
from zonefile_migrate.dns_record_set import create_from_zone
from zonefile_migrate.utils import (
    get_all_zonefiles_in_path,
    convert_zonefiles,
    target_file,
)


def logical_resource_id(name: str):
    """
    create a CloudFormation logical resource id for `name`, ignoring non letters or digits.

    >>> logical_resource_id('asample.org')
    'AsampleOrg'
    >>> logical_resource_id('v-r-v.com')
    'VRVCom'
    >>> logical_resource_id('chapter9.com')
    'Chapter9Com'
    >>> logical_resource_id('/is/this/not/pretty?')
    'IsThisNotPretty'
    """
    return re.sub(r"\W+", " ", name).title().replace(" ", "")


def generate_unique_logical_resource_id(prefix: str, resources: dict) -> str:
    """
    generates a unique logical resource id using `prefix` as a key into `resources`. This
    is to avoid potential name clashes in the CloudFormation Resource section.
    >>> generate_unique_logical_resource_id('key', {})
    'key'
    >>> generate_unique_logical_resource_id('key', {'key': 'value'})
    'key1'
    >>> generate_unique_logical_resource_id('key', {'key': 'value', 'key1': 'value1'})
    'key2'
    """
    same_prefix = set(filter(lambda n: n.startswith(prefix), resources.keys()))
    if not same_prefix:
        return prefix

    count = 1
    while f"{prefix}{count}" in same_prefix:
        count = count + 1
    return f"{prefix}{count}"


def convert_to_cloudformation(zone: easyzone.Zone, maximum_ttl: int) -> dict:
    """
    Converts the zonefile into a CloudFormation template.
    """
    ttl = zone.root.ttl
    domain_name = zone.domain
    idna_domain_name = domain_name.encode("idna").decode("ascii")

    result = CommentedMap()
    result["AWSTemplateFormatVersion"] = "2010-09-09"
    resources = CommentedMap()
    resources["HostedZone"] = CommentedMap(
        {"Type": "AWS::Route53::HostedZone", "Properties": {"Name": idna_domain_name}}
    )
    result["Resources"] = resources

    for record_set in create_from_zone(zone):
        if record_set.name in [zone.domain, idna_domain_name]:
            if record_set.rectype in ["NS", "SOA"]:
                log.debug("ignoring %s records for origin %s", record_set.rectype, zone.domain)
                continue

        logical_name = generate_unique_logical_resource_id(
            re.sub(
                r"[^0-9a-zA-Z]",
                "",
                logical_resource_id(
                    re.sub(
                        r"^\*",
                        "wildcard",
                        record_set.name.removesuffix("." + zone.domain)
                        if record_set.name != zone.domain
                        else "Origin",
                    )
                ),
            )
            + record_set.rectype
            + "Record",
            resources,
        )

        resources[logical_name] = CommentedMap(
            {
                "Type": "AWS::Route53::RecordSet",
                "Properties": {
                    "Name": record_set.name,
                    "Type": record_set.rectype,
                    "ResourceRecords": record_set.rrdatas,
                    "TTL": maximum_ttl
                    if maximum_ttl and record_set.ttl > maximum_ttl
                    else record_set.ttl,
                    "HostedZoneId": {"Ref": "HostedZone"},
                },
            }
        )

    return result


def common_parent(one: Path, other: Path) -> Path:
    """
    returns the commons parent of two paths
    >>> common_parent(Path('/a/b/c'), Path('/a/e/f')).as_posix()
    '/a'
    >>> common_parent(Path('/one/b/c'), Path('/other/f')).as_posix()
    '/'
    >>> common_parent(Path('/usr/share/var/lib/one'), Path('/usr/share/var/lib/other')).as_posix()
    '/usr/share/var/lib'
    """
    one_parts = one.absolute().parts
    other_parts = other.absolute().parts
    for i, part in enumerate(one_parts):
        if i >= len(other_parts):
            break
        if part != other_parts[i]:
            break

    return Path(*one_parts[:i])


def template_in_sceptre_project(
    template_path: Path, sceptre_config_directory: Path
) -> bool:
    """
    determines whether the template directory is in the sceptre project directory.

    >>> template_in_sceptre_project(Path('example/templates/cfn-template-name'), Path('example/config/dns'))
    True
    >>> template_in_sceptre_project(Path('example/templates/cfn-template-name'), Path('somewhere-else/config/dns'))
    False
    >>> template_in_sceptre_project(Path('templates/cfn-template-name'), Path('example/config/dns'))
    False
    """
    parent = common_parent(template_path, sceptre_config_directory)
    sceptre_dir = sceptre_config_directory.absolute().relative_to(parent)
    templates_dir = template_path.absolute().relative_to(parent)
    return sceptre_dir.parts[0] == "config" and templates_dir.parts[0] == "templates"


def generate_sceptre_configuration(
    zone: easyzone.Zone, template: Path, config_directory: Path
):
    """
    generates a sceptre stack config for the CloudFormation template for the zone.
    """
    stack_name = "zone-" + re.sub(
        r"-{2,}", "-", re.sub(r"[^\w]+", "-", slugify(zone.domain))
    ).strip("-")
    stack_config = config_directory.joinpath(Path(stack_name).with_suffix(".yaml"))

    # create empty stack group configuration file
    config_directory.mkdir(parents=True, exist_ok=True)
    group_config = config_directory.joinpath("config.yaml")
    if not group_config.exists():
        with group_config.open("w") as file:
            pass

    # create stack configuration file
    config = None
    if stack_config.exists():
        with stack_config.open("r") as file:
            config = YAML().load(file)

    if not config:
        config = {}

    parent = common_parent(config_directory, template)
    template_path = (
        template.absolute().relative_to(parent.joinpath("templates")).as_posix()
    )
    if config.get("template_path") != template_path:
        config["template_path"] = template_path

        with stack_config.open("w") as file:
            YAML().dump(config, file)


@click.command(name="to-cloudformation")
@click.option(
    "--sceptre-group",
    required=False,
    type=click.Path(file_okay=False),
    help="to write sceptre stack group configuration",
)
@click.option(
    "--maximum-ttl",
    required=False,
    type=int,
    help="maximum TTL of domain name records",
)
@click.argument("src", nargs=-1, type=click.Path())
@click.argument("dst", nargs=1, type=click.Path())
def command(sceptre_group, maximum_ttl, src, dst):
    """
    Converts one or more `SRC` zonefiles into AWS CloudFormation templates in `DST`.
    Optionally generates the Sceptre stack config for each of the templates in the
    `--sceptre-group` directoru.

    Each generated CloudFormation template contains a single Route53 HostedZone and all
    associated ResourceRecordSet. The SOA and NS records for the origin domain are not
    copied into the template.

    The zonefiles must contain a $ORIGIN and $TTL statement. If the SRC points to a directory
    all files which contain one of these statements will be converted. If a $ORIGIN is missing,
    the name of the file will be used as the domain name.

    You may override the maximum TTL of records through the option --maximum-ttl
    """
    if sceptre_group:
        sceptre_group = Path(sceptre_group)

    if not src:
        raise click.UsageError("no source files were specified")

    inputs = get_all_zonefiles_in_path(src)

    if len(inputs) == 0:
        click.UsageError("no zonefiles were found")

    dst = Path(dst)
    if len(inputs) > 1:
        if dst.exists() and not dst.is_dir():
            raise click.UsageError(f"{dst} is not a directory")
        if not dst.exists():
            dst.mkdir(parents=True, exist_ok=True)

    outputs = list(map(lambda d: target_file(d, dst, ".yaml"), inputs))

    def transform_to_cloudformation(zone: easyzone.Zone, output: Path):
        with output.open("w") as file:
            YAML().dump(convert_to_cloudformation(zone, maximum_ttl), stream=file)
            if sceptre_group:
                generate_sceptre_configuration(zone, output, sceptre_group)

    convert_zonefiles(inputs, outputs, transform_to_cloudformation)


if __name__ == "__main__":
    command()
