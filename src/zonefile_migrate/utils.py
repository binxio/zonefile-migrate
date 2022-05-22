import re
from pathlib import Path
from typing import Callable, List
from easyzone import easyzone
from zonefile_migrate.logger import log


def is_zonefile(path: Path) -> bool:
    """
    returns true if the file pointed to by `path` contains a $ORIGIN or $TTL pragma, otherwise False
    """
    if path.exists() and path.is_file():
        with path.open("r") as file:
            for line in file:
                if re.search(r"^\s*\$(ORIGIN|TTL)\s+", line, re.IGNORECASE):
                    return True
    return False


def get_all_zonefiles_in_path(src: [Path]) -> [Path]:
    """
    creates a list of filenames of zonefiles from a list of paths. If the path
    is not a directory, the path will be added as is. If the path points to a
    directory, the files of the directory will be scanned to determined if they
    are a zonefile (see is_zonefile)
    """
    inputs = []
    for filename in map(lambda s: Path(s), src):
        if not filename.exists():
            raise ValueError(f"{filename} does not exist")

        if filename.is_dir():
            inputs.extend(
                [f for f in filename.iterdir() if f.is_file() and is_zonefile(f)]
            )
        else:
            inputs.append(filename)
    return inputs


def convert_zonefiles(
    inputs: [Path], outputs: [Path], transform: Callable[[easyzone.Zone, Path], None]
):
    for i, input in enumerate(map(lambda s: Path(s), inputs)):
        with input.open("r") as file:
            content = file.read()
            found = re.search(
                r"\$ORIGIN\s+(?P<domain_name>.*)\s*",
                content,
                re.MULTILINE | re.IGNORECASE,
            )
            if found:
                domain_name = found.group("domain_name")
            else:
                domain_name = input.name.removesuffix(".zone")
                log.warning(
                    "could not find $ORIGIN from zone file %s, using %s",
                    input,
                    domain_name,
                )

            try:
                log.info("reading zonefile %s", input.as_posix())
                zone = easyzone.zone_from_file(domain_name, input.as_posix())
                transform(zone, outputs[i])
            except SyntaxError as error:
                log.error(error)
                exit(1)


def target_file(src: Path, dst: Path, extension: str) -> Path:
    if dst.is_file():
        return dst

    if src.suffix == ".zone":
        return dst.joinpath(src.name).with_suffix(extension)

    return dst.joinpath(src.name + extension)
