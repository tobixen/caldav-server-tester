#!/usr/bin/env python

"""
This is the CLI - the "click" application
"""

import click
from caldav.davclient import get_davclient
from .checker import ServerQuirkChecker

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
@click.option("--test-checks", help="List of checks to run", multiple=True)
def check_server_compatibility(verbose, json, name, test_checks, **kwargs):
    click.echo("WARNING: this script is not production-ready")

    ## Remove empty keys
    conn_keys = {}
    for x in kwargs:
        if x.startswith('caldav_') and kwargs[x]:
            conn_keys[x[7:]] = kwargs[x]
    with get_davclient(name=name, testconfig=True, **conn_keys) as conn:
        obj = ServerQuirkChecker(conn)
        if not test_checks:
            obj.check_all()
        for check in test_checks:
            obj.check_one(check)
    click.echo(obj.report(verbose=verbose, return_what='json' if json else str))

if __name__ == "__main__":
    check_server_compatibility()
