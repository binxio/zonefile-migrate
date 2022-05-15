import click
from zonefile_migrate.zone_to_cfn import command


@click.group
def main():
    """
    Migrate Route53 managed zones
    """
    pass


main.add_command(command)

if __name__ == "__main__":
    main()
