import click
from zonefile_migrate.to_cloudformation import command


@click.group
def main():
    """
    Migrate DNS managed zones
    """
    pass


main.add_command(command)

if __name__ == "__main__":
    main()
