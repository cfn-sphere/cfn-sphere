import logging
import sys

import boto3
import click
from botocore.exceptions import ClientError, BotoCoreError

from cfn_sphere import StackActionHandler
from cfn_sphere import __version__
from cfn_sphere.aws.cfn import CloudFormation
from cfn_sphere.aws.kms import KMS
from cfn_sphere.exceptions import CfnSphereException
from cfn_sphere.file_loader import FileLoader
from cfn_sphere.stack_configuration import Config
from cfn_sphere.template.transformer import CloudFormationTemplateTransformer
from cfn_sphere.util import convert_file, get_logger, get_latest_version, kv_list_to_dict

LOGGER = get_logger(root=True)


def get_first_account_alias_or_account_id():
    try:
        return boto3.client('iam').list_account_aliases()["AccountAliases"][0]
    except IndexError:
        return boto3.client('sts').get_caller_identity()["Arn"].split(":")[4]
    except (BotoCoreError, ClientError) as e:
        LOGGER.error(e)
        sys.exit(1)
    except Exception as e:
        LOGGER.error("Unknown error occurred loading users account alias")
        LOGGER.exception(e)
        LOGGER.info("Please report at https://github.com/cfn-sphere/cfn-sphere/issues!")
        sys.exit(1)


def check_update_available():
    latest_version = get_latest_version()
    if latest_version and __version__ != latest_version:
        click.confirm(
            "There is an update available (v: {0}).\n"
            "Changelog: https://github.com/cfn-sphere/cfn-sphere/issues?q=milestone%3A{0}+\n"
            "Do you want to continue?".format(latest_version), abort=True)


@click.group(help="This tool manages AWS CloudFormation templates "
                  "and stacks by providing an application scope and useful tooling.")
@click.version_option(version=__version__)
def cli():
    pass


@cli.command(help="Sync AWS resources with definition file")
@click.argument('config', type=click.Path(exists=True))
@click.option('--parameter', '-p', default=None, envvar='CFN_SPHERE_PARAMETERS', type=click.STRING, multiple=True,
              help="Stack parameter to overwrite, eg: --parameter stack1.p1=v1")
@click.option('--debug', '-d', is_flag=True, default=False, envvar='CFN_SPHERE_DEBUG', help="Debug output")
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")
@click.option('--yes', '-y', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes (alias for -c/--confirm")
def sync(config, parameter, debug, confirm, yes):
    confirm = confirm or yes
    if debug:
        LOGGER.setLevel(logging.DEBUG)
        boto3.set_stream_logger(name='boto3', level=logging.DEBUG)
        boto3.set_stream_logger(name='botocore', level=logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)

    if not confirm:
        check_update_available()
        click.confirm('This action will modify AWS infrastructure in account: {0}\nAre you sure?'.format(
            get_first_account_alias_or_account_id()), abort=True)

    try:

        config = Config(config_file=config, cli_params=parameter)
        StackActionHandler(config).create_or_update_stacks()
    except CfnSphereException as e:
        LOGGER.error(e)
        if debug:
            LOGGER.exception(e)
        sys.exit(1)
    except Exception as e:
        LOGGER.error("Failed with unexpected error")
        LOGGER.exception(e)
        LOGGER.info("Please report at https://github.com/cfn-sphere/cfn-sphere/issues!")
        sys.exit(1)


@cli.command(help="Delete all stacks in a stack configuration")
@click.argument('config', type=click.Path(exists=True))
@click.option('--debug', '-d', is_flag=True, default=False, envvar='CFN_SPHERE_DEBUG', help="Debug output")
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")
@click.option('--yes', '-y', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes (alias for -c/--confirm")
def delete(config, debug, confirm, yes):
    confirm = confirm or yes
    if debug:
        LOGGER.setLevel(logging.DEBUG)
    else:
        LOGGER.setLevel(logging.INFO)

    if not confirm:
        check_update_available()
        click.confirm('This action will delete all stacks in {0} from account: {1}\nAre you sure?'.format(
            config, get_first_account_alias_or_account_id()), abort=True)

    try:

        config = Config(config)
        StackActionHandler(config).delete_stacks()
    except CfnSphereException as e:
        LOGGER.error(e)
        if debug:
            LOGGER.exception(e)
        sys.exit(1)
    except Exception as e:
        LOGGER.error("Failed with unexpected error")
        LOGGER.exception(e)
        LOGGER.info("Please report at https://github.com/cfn-sphere/cfn-sphere/issues!")
        sys.exit(1)


@cli.command(help="Convert JSON to YAML or vice versa")
@click.argument('template_file', type=click.Path(exists=True))
@click.option('--debug', '-d', is_flag=True, default=False, envvar='CFN_SPHERE_DEBUG', help="Debug output")
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")
@click.option('--yes', '-y', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes (alias for -c/--confirm")
def convert(template_file, debug, confirm, yes):
    confirm = confirm or yes
    if not confirm:
        check_update_available()

    if debug:
        LOGGER.setLevel(logging.DEBUG)

    try:
        click.echo(convert_file(template_file))
    except Exception as e:
        LOGGER.error("Error converting {0}:".format(template_file))
        LOGGER.exception(e)
        sys.exit(1)


@cli.command(help="Render template as it would be used to create/update a stack")
@click.argument('template_file', type=click.Path(exists=True))
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")
@click.option('--yes', '-y', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes (alias for -c/--confirm")
def render_template(template_file, confirm, yes):
    confirm = confirm or yes
    if not confirm:
        check_update_available()

    loader = FileLoader()
    template = loader.get_cloudformation_template(template_file, None)
    template = CloudFormationTemplateTransformer.transform_template(template)
    click.echo(template.get_pretty_template_json())


@cli.command(help="Validate template with CloudFormation API")
@click.argument('template_file', type=click.Path(exists=True))
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")
@click.option('--yes', '-y', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes (alias for -c/--confirm")
def validate_template(template_file, confirm, yes):
    confirm = confirm or yes
    if not confirm:
        check_update_available()

    try:
        loader = FileLoader()
        template = loader.get_cloudformation_template(template_file, None)
        template = CloudFormationTemplateTransformer.transform_template(template)
        CloudFormation().validate_template(template)
        click.echo("Template is valid")
    except CfnSphereException as e:
        LOGGER.error(e)
        sys.exit(1)
    except Exception as e:
        LOGGER.error("Failed with unexpected error")
        LOGGER.exception(e)
        LOGGER.info("Please report at https://github.com/cfn-sphere/cfn-sphere/issues!")
        sys.exit(1)


@cli.command(help="Encrypt a given string with AWS Key Management Service")
@click.argument('region', type=str)
@click.argument('keyid', type=str)
@click.argument('cleartext', type=str)
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")
@click.option('--context', '-c', default=None, envvar='CFN_SPHERE_CONTEXT', type=click.STRING, multiple=True,
              help="Context for encryption, passed as kv pairs, e.g. --context key=value")
@click.option('--yes', '-y', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes (alias for -c/--confirm")
def encrypt(region, keyid, cleartext, context, confirm, yes):
    confirm = confirm or yes
    if not confirm:
        check_update_available()

    try:
        cipertext = KMS(region).encrypt(keyid, cleartext, kv_list_to_dict(context))
        click.echo("Ciphertext: {0}".format(cipertext))
    except CfnSphereException as e:
        LOGGER.error(e)
        sys.exit(1)
    except Exception as e:
        LOGGER.error("Failed with unexpected error")
        LOGGER.exception(e)
        LOGGER.info("Please report at https://github.com/cfn-sphere/cfn-sphere/issues!")
        sys.exit(1)


@cli.command(help="Decrypt a given ciphertext with AWS Key Management Service")
@click.argument('region', type=str)
@click.argument('ciphertext', type=str)
@click.option('--context', '-c', default=None, envvar='CFN_SPHERE_CONTEXT', type=click.STRING, multiple=True,
              help="Context for decryption, passed as kv pairs, e.g. --context key=value")
@click.option('--confirm', '-c', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes")
@click.option('--yes', '-y', is_flag=True, default=False, envvar='CFN_SPHERE_CONFIRM',
              help="Override user confirm dialog with yes (alias for -c/--confirm")
def decrypt(region, ciphertext, context, confirm, yes):
    confirm = confirm or yes
    if not confirm:
        check_update_available()

    try:
        cleartext = KMS(region).decrypt(ciphertext, kv_list_to_dict(context))
        click.echo("Cleartext: {0}".format(cleartext))
    except CfnSphereException as e:
        LOGGER.error(e)
        sys.exit(1)
    except Exception as e:
        LOGGER.error("Failed with unexpected error")
        LOGGER.exception(e)
        LOGGER.info("Please report at https://github.com/cfn-sphere/cfn-sphere/issues!")
        sys.exit(1)


def main():
    cli()
