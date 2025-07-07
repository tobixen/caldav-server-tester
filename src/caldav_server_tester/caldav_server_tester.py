#!/usr/bin/env python
import click
from caldav.davclient import get_davclient
from .checks import ServerQuirkChecker

@click.command()
@click.option("--name", type=str, help="Choose a server by name", default=None)
@click.option("--verbose/--quiet", default=None, help="More output")
@click.option("--json/--text", help="JSON output.  Overrides verbose")
## TODO: lines below has been copied from the plann library.
## TODO: the list is also incomplete
## TODO: Should probably consider to consolidate a bit
#@_set_conn_options ## defined in the caldav_server_tester_old.py file, but needs refactoring.
@click.option('--caldav-url', help="Full URL to the caldav server", metavar='URL')
@click.option('--caldav-username', '--caldav-user', help="Full URL to the caldav server", metavar='URL')
@click.option('--caldav-password', '--caldav-pass', help="Password for the caldav server", metavar='URL')
#@click.option("--test-features", help="List of features to test")
def check_server_compatibility(verbose, json, name, **kwargs):
    click.echo("WARNING: this script is not production-ready")

    ## Remove empty keys
    conn_keys = {}
    for x in kwargs:
        if x.startswith('caldav_') and kwargs[x]:
            conn_keys[x[7:]] = kwargs[x]
    with get_davclient(name=name, testconfig=True, **conn_keys) as conn:
        obj = ServerQuirkChecker(conn)
        obj.check_all()
    obj.report(verbose=verbose, json=json)

if __name__ == "__main__":
    check_server_compatibility()
