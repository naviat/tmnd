import logging
import sys

import click

from tmnd import display
from tmnd import __version__
from tmnd.configuration import Configuration

logger = logging.getLogger('tmnd')
docker_url = None


@click.group(help=('Tomo fullnode (tmnd) is a cli tool to help you run a Tomo'
                   'chain fullnode'))
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--docker', metavar='URL', help='Url to the docker server')
@click.version_option(version=__version__)
def main(debug: bool, docker: str) -> None:
    "Cli entrypoint"
    global docker_url
    if debug:
        logger.setLevel('DEBUG')
        logger.debug('Debugging enabled')
    docker_url = docker


@click.command(help='Display TomoChain documentation link')
def docs() -> None:
    "Link to the documentation"
    display.link_docs()


@click.command(help='Start your TomoChain fullnode')
@click.option('--name', metavar='NAME', help='Your fullnode\'s name')
@click.option('--net', type=click.Choice(['mainnet', 'testnet', 'devnet']),
              help='The environment your fullnode will connect to')
@click.option('--pkey', metavar='KEY', help=('Private key of the account your '
                                             'fullnode will collect rewards '
                                             'on'))
@click.option('--api', is_flag=True)
def start(name: str, net: str, pkey: str, api: bool) -> None:
    "Start the containers needed to run a fullnode"
    configuration = Configuration(name=name, net=net, pkey=pkey, start=True,
                                  docker_url=docker_url, api=api)
    if configuration.force_recreate:
        display.error_breaking_change()
        sys.exit('\n')
    display.title_start_fullnode(configuration.name)
    # volumes
    display.subtitle_create_volumes()
    for _, value in configuration.volumes.items():
        display.step_create_volume(value.name)
        if value.create():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # networks
    display.subtitle_create_networks()
    for _, value in configuration.networks.items():
        display.step_create_network(value.name)
        if value.create():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # container
    # create
    display.subtitle_create_containers()
    for _, value in configuration.services.items():
        display.step_create_container(value.name)
        if value.create():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # start
    for _, value in configuration.services.items():
        display.step_start_container(value.name)
        if value.start():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()


@click.command(help='Stop your TomoChain fullnode')
def stop() -> None:
    "Stop the fullnode containers"
    configuration = Configuration(docker_url=docker_url)
    if configuration.force_recreate:
        display.error_breaking_change()
        sys.exit('\n')
    display.title_stop_fullnode(configuration.name)
    for _, service in configuration.services.items():
        display.step_stop_container(service.name)
        if service.stop():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()


@click.command(help='Show the status of your TomoChain fullnode')
def status() -> None:
    "Show the status of the fullnode containers"
    configuration = Configuration(docker_url=docker_url)
    if configuration.force_recreate:
        display.error_breaking_change()
        sys.exit('\n')
    display.title_status_fullnode(configuration.name)
    for _, service in configuration.services.items():
        status = service.status()
        if status and status == 'absent':
            display.status(
                name=service.name
            )
        if status and status in ['running']:
            display.status(
                name=service.name,
                status=status,
                id=service.container.short_id,
                status_color='green'
            )
        elif status:
            display.status(
                name=service.name,
                status=status,
                id=service.container.short_id,
            )
        else:
            display.status(
                name=service.name,
                status='error'
            )
    display.newline()


@click.command(help='Show details about your TomoChain fullnode')
def inspect() -> None:
    "Show details about the tomochain fullnode"
    configuration = Configuration(docker_url=docker_url)
    if configuration.force_recreate:
        display.error_breaking_change()
        sys.exit('\n')
    display.title_inspect_fullnode(configuration.name)
    identity = configuration.services['tomochain'].execute(
        'echo $IDENTITY'
    ) or 'container not running'
    display.detail_identity(identity)
    display.newline()
    coinbase = configuration.services['tomochain'].execute(
        'tomo account list --keystore keystore 2> /dev/null | head -n 1 | cut '
        '-d"{" -f 2 | cut -d"}" -f 1'
    )
    if coinbase:
        coinbase = '0x{}'.format(coinbase)
    else:
        coinbase = 'container not running'
    display.detail_coinbase(coinbase)
    display.newline()


@click.command(help='Update your fullnode')
def update() -> None:
    "Update the tomochain fullnode with the lastest images"
    configuration = Configuration(docker_url=docker_url)
    if configuration.force_recreate:
        display.error_breaking_change()
        sys.exit('\n')
    display.title_update_fullnode(configuration.name)
    display.subtitle_remove_containers()
    # containers
    # stop
    for _, service in configuration.services.items():
        display.step_stop_container(service.name)
        if service.stop():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # remove
    for _, service in configuration.services.items():
        display.step_remove_container(service.name)
        if service.remove():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # create
    for _, value in configuration.services.items():
        display.step_create_container(value.name)
        if value.create():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # start
    for _, value in configuration.services.items():
        display.step_start_container(value.name)
        if value.start():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()


@click.command(help='Remove your TomoChain fullnode')
@click.option('--confirm', is_flag=True)
def remove(confirm: bool) -> None:
    "Remove the fullnode (containers, networks volumes)"
    configuration = Configuration(docker_url=docker_url)
    if not confirm:
        display.warning_remove_fullnode(configuration.name)
        sys.exit('\n')
    display.title_remove_fullnode(configuration.name)
    display.subtitle_remove_containers()
    # containers
    # stop
    for _, service in configuration.services.items():
        display.step_stop_container(service.name)
        if service.stop():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # remove
    for _, service in configuration.services.items():
        display.step_remove_container(service.name)
        if service.remove():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # networks
    display.subtitle_remove_networks()
    for _, network in configuration.networks.items():
        display.step_remove_network(network.name)
        if network.remove():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    # volumes
    display.subtitle_remove_volumes()
    for _, volume in configuration.volumes.items():
        display.step_remove_volume(volume.name)
        if volume.remove():
            display.step_close_ok()
        else:
            display.step_close_nok()
    display.newline()
    configuration.remove()


main.add_command(docs)
main.add_command(start)
main.add_command(stop)
main.add_command(status)
main.add_command(inspect)
main.add_command(update)
main.add_command(remove)
