import click
from zonefile_migrate.to_cloudformation import command as to_cfn
from zonefile_migrate.to_terraform import command as to_tf


@click.group
def main():
    """
    Migrate DNS managed zones
    """
    pass


main.add_command(to_cfn)
main.add_command(to_tf)

if __name__ == "__main__":
    main()
