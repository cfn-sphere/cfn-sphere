#!/usr/bin/python

import sys
import logging

import boto
import click

from boto.exception import NoAuthHandlerFound, BotoServerError

from cfn_sphere.template.transformer import CloudFormationTemplateTransformer
from cfn_sphere.util import convert_file, get_logger, get_latest_version
from cfn_sphere.stack_configuration import Config
from cfn_sphere import StackActionHandler
from cfn_sphere.exceptions import CfnSphereException
from cfn_sphere.file_loader import FileLoader
from cfn_sphere import __version__

LOGGER = get_logger(root=True)
logging.getLogger('boto').setLevel(logging.FATAL)


def get_current_account_alias():
    try:
        return boto.connect_iam().get_account_alias().account_aliases[0]
    except NoAuthHandlerFound as e:
        click.echo("Authentication error! Please check credentials: {0}".format(e))
        sys.exit(1)
    except BotoServerError as e:
        click.echo("AWS API Error: {0}".format(e))
        sys.exit(1)
    except Exception as e:
        click.echo("Unknown error occurred loading users account alias: {0}".format(e))
        sys.exit(1)


def check_update_available():
    latest_version = get_latest_version()
    if latest_version and __version__ != latest_version:
        click.confirm(
            "There is an update available (v: {0}). Do you want to continue?".format(latest_version),
            abort=True)


@click.group(help="This tool manages AWS CloudFormation templates "
                  "and stacks by providing an application scope and useful tooling.")
@click.version_option(version=__version__)
def cli():
    pass


@cli.command(help="Sync AWS resources with definition file")
@click.argument('filename', type=click.Path(exists=True))
@click.option('--parameters', '-p', is_flag=True, default=False,
              help="List of params to be overwritten; these have highest priority."
                   "eg: --parameters stack1:p1=v1,stack2:p2=v2")
@click.option('--debug', '-d', is_flag=True, default=False, envvar='CFN_SPHERE_DEBUG', help="Debug output")
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")

def sync(filename, parameters, debug, confirm):
    if debug:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)

    if not confirm:
        check_update_available()
        click.confirm('This action will modify AWS infrastructure in account: {0}\nAre you sure?'.format(
            get_current_account_alias()), abort=True)

    try:

        config = Config(config_file=filename, config_dict=parameters)
        StackActionHandler(config).create_or_update_stacks()
    except CfnSphereException as e:
        LOGGER.error(e)
        if debug:
            LOGGER.exception(e)
        sys.exit(1)
    except Exception as e:
        LOGGER.error("Failed with unexpected error".format(e))
        LOGGER.exception(e)
        LOGGER.info("Please report at https://github.com/cfn-sphere/cfn-sphere/issues!")
        sys.exit(1)


@cli.command(help="Delete all stacks in a stack configuration")
@click.argument('filename', type=click.Path(exists=True))
@click.option('--debug', '-d', is_flag=True, default=False, envvar='CFN_SPHERE_DEBUG', help="Debug output")
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")
def delete(filename, debug, confirm):
    if debug:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)

    if not confirm:
        check_update_available()
        click.confirm('This action will delete all stacks in {0} from account: {1}\nAre you sure?'.format(
            filename, get_current_account_alias()), abort=True)

    try:

        config = Config(filename)
        StackActionHandler(config).delete_stacks()
    except CfnSphereException as e:
        LOGGER.error(e)
        if debug:
            LOGGER.exception(e)
        sys.exit(1)
    except Exception as e:
        LOGGER.error("Failed with unexpected error".format(e))
        LOGGER.exception(e)
        LOGGER.info("Please report at https://github.com/cfn-sphere/cfn-sphere/issues!")
        sys.exit(1)


@cli.command(help="Convert JSON to YAML or vice versa")
@click.argument('filename', type=click.Path(exists=True))
@click.option('--debug', '-d', is_flag=True, default=False, envvar='CFN_SPHERE_DEBUG', help="Debug output")
def convert(filename, debug):
    check_update_available()

    if debug:
        LOGGER.setLevel(logging.DEBUG)

    try:
        click.echo(convert_file(filename))
    except Exception as e:
        LOGGER.error("Error converting {0}:".format(filename))
        LOGGER.exception(e)
        sys.exit(1)


@cli.command(help="Render template as it would be used to create/update a stack")
@click.argument('filename', type=click.Path(exists=True))
@click.option('--parameters', '-p', is_flag=True, default=False,
              help="List of params to be overwritten; these have highest priority."
                   "eg: --parameters stack1:p1=v1,stack2:p2=v2")
def render_template(filename):
    check_update_available()

    loader = FileLoader()
    # TODO implement template parameter migration
    template = loader.get_file_from_url(filename, None)
    template = CloudFormationTemplateTransformer.transform_template(template)
    click.echo(template.get_template_json())


def main():
    cli()
