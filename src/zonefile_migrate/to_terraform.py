import click
import json
import logging
import re
import sys
import os
import pkgutil
from zonefile_migrate.utils import convert_zonefiles, target_file


from pathlib import Path
from ruamel.yaml import YAML, CommentedMap
from zonefile_migrate.logger import logging
from easyzone import easyzone
from dns.exception import SyntaxError
from zonefile_migrate.dns_record_set import create_from_zone
from jinja2 import Template
from zonefile_migrate.utils import get_all_zonefiles_in_path

tf_managed_zone_template = """
module managed_zone_{{ resource_name }} {
  source               = "./{{ provider }}-managed-zone"
  domain_name          = "{{ domain_name }}"
  resource_record_sets = [{% for record in resource_record_sets %}
    {
       name = "{{ record.name }}"
       type = "{{ record.rectype }}"
       ttl  = {{ record.ttl }}
       rrdatas = [{% for rrdata in record.rrdatas %}
         "{{ rrdata.strip('"') }}",{% endfor %}
       ]
    },{% endfor %}
  ]
}
"""


def convert_to_terraform(zone: easyzone.Zone, provider: str) -> str:
    """
    Converts the zonefile into a terraform tempalte for Google
    """
    domain_name = zone.domain
    resource_name = re.sub(r"\.", "_", zone.domain.removesuffix("."))
    resource_record_sets = list(
        filter(
            lambda r: not (
                r.rectype == "SOA" or (r.rectype == "NS" and r.name == zone.domain)
            ),
            create_from_zone(zone),
        )
    )
    template = Template(tf_managed_zone_template)

    return template.render(
        {
            "domain_name": domain_name,
            "resource_name": resource_name,
            "provider": provider,
            "resource_record_sets": resource_record_sets,
        }
    )


@click.command(name="to-terraform")
@click.option(
    "--provider",
    required=False,
    default="google",
    help="name of provider to generate the managed zone for (google)",
)
@click.argument("src", nargs=-1, type=click.Path())
@click.argument("dst", nargs=1, type=click.Path())
def command(provider, src, dst):
    """
    Converts one or more `SRC` zonefiles into Terraform templates in `DST`.

    Each generated Terraform  template contains a single hosted zone and all
    associated resource record sets. The SOA and NS records for the origin domain are not
    copied into the template.

    The zonefiles must contain a $ORIGIN and $TTL statement. If the SRC points to a directory
    all files which contain one of these statements will be converted. If a $ORIGIN is missing,
    the name of the file will be used as the domain name.
    """
    tf_module_template = Path(__file__).parent.joinpath(
        f"terraform-modules/{provider}-managed-zone.tf"
    )
    if not tf_module_template.exists():
        raise click.UsageError(f"provider {provider} is not supported")

    if not src:
        raise click.UsageError("no source files were specified")

    try:
        inputs = get_all_zonefiles_in_path(src)
        if len(inputs) == 0:
            raise click.UsageError("no zonefiles were found")
    except ValueError as error:
        raise click.UsageError(error)

    dst = Path(dst)
    if len(inputs) > 1:
        if dst.exists() and not dst.is_dir():
            raise click.UsageError(f"{dst} is not a directory")
        if not dst.exists():
            dst.mkdir(parents=True, exist_ok=True)

    outputs = list(map(lambda d: target_file(d, dst, ".tf"), inputs))

    if dst.is_dir():
        main_path = dst.joinpath(f"{provider}-managed-zone/main.tf")
        if not main_path.exists():
            main_path.parent.mkdir(exist_ok=True)
            main_path.write_bytes(tf_module_template.read_bytes())

    def _transform_to_terraform(zone: easyzone.Zone, output: Path):
        with output.open("w") as file:
            file.write(convert_to_terraform(zone, provider))

    convert_zonefiles(inputs, outputs, _transform_to_terraform)


if __name__ == "__main__":
    command()
