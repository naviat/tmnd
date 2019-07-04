import pytest

import docker

import tmnd as package

client = docker.from_env()


@pytest.fixture
def runner():
    from click.testing import CliRunner
    runner = CliRunner()
    return runner


@pytest.fixture
def tmnd():
    from tmnd import tmnd
    from tmnd.environments import environments
    from tmnd import configuration
    environments['devnet'] = {
        'tomochain': {
            'BOOTNODES': (
                'test'
            ),
            'NETSTATS_HOST': 'test.com',
            'NETSTATS_PORT': '443',
            'NETWORK_ID': '90',
            'WS_SECRET': (
                'test'
            )
        },
        'metrics': {
            'METRICS_ENDPOINT': 'https://test.com'
        }
    }
    environments['testnet'] = environments['devnet']
    configuration.resources.init('tomochain', 'tomo_tests')
    return tmnd


def _clean(tmnd):
    from tmnd import configuration
    try:
        client.containers.get('test1_tomochain').remove(force=True)
    except Exception:
        pass
    try:
        client.containers.get('test1_metrics').remove(force=True)
    except Exception:
        pass
    try:
        client.volumes.get('test1_chaindata').remove(force=True)
    except Exception:
        pass
    try:
        client.networks.get('test1_tmnd').remove()
    except Exception:
        pass
    configuration.resources.init('tomochain', 'tomo_tests')
    configuration.resources.user.delete('id')
    configuration.resources.user.delete('name')
    configuration.resources.user.delete('net')


def test_version(runner, tmnd):
    version = '0.5.0'
    result = runner.invoke(tmnd.main, ['--version'])
    assert result.output[-6:-1] == version
    assert package.__version__ == version


def test_error_docker(runner, tmnd):
    result = runner.invoke(tmnd.main, ['--docker', 'unix://test', 'docs'])
    assert '! error: could not access the docker daemon\nNone\n'
    assert result.exit_code == 0


def test_command(runner, tmnd):
    result = runner.invoke(tmnd.main)
    assert result.exit_code == 0


def test_command_docs(runner, tmnd):
    result = runner.invoke(tmnd.main, ['docs'])
    msg = 'Documentation on running a masternode:'
    link = 'https://docs.tomochain.com/masternode/tmnd/\n'
    assert result.output == "{} {}".format(msg, link)
    assert result.exit_code == 0


def test_command_start_init_devnet(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    lines = result.output.splitlines()
    assert 'Starting fullnode test1:' in lines
    for line in lines:
        assert '✗' not in line
    _clean(tmnd)


def test_command_start_init_testnet(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'testnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    lines = result.output.splitlines()
    assert 'Starting fullnode test1:' in lines
    for line in lines:
        assert '✗' not in line
    _clean(tmnd)


def test_command_start_init_mainnet(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'mainnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    lines = result.output.splitlines()
    assert 'Starting fullnode test1:' in lines
    for line in lines:
        assert '✗' not in line
    _clean(tmnd)


def test_command_start_init_invalid_name(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--name', 'tes', '--net', 'devnet', '--pkey', '1234'])
    lines = result.output.splitlines()
    assert 'error' in lines[1]
    assert '! error: --name is not valid' in lines
    _clean(tmnd)


def test_command_start_init_no_pkey(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net', 'devnet'])
    lines = result.output.splitlines()
    assert ('! error: --pkey is required when starting a new '
            'fullnode') in lines
    _clean(tmnd)


def test_command_start_init_invalid_pkey_len(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net', 'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890'])
    lines = result.output.splitlines()
    assert '! error: --pkey is not valid' in lines
    _clean(tmnd)


def test_command_start_init_no_net(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'])
    lines = result.output.splitlines()
    assert '! error: --net is required when starting a new fullnode' in lines
    _clean(tmnd)


def test_command_start_init_no_name(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'])
    lines = result.output.splitlines()
    assert ('! error: --name is required when starting a new '
            'fullnode') in lines
    _clean(tmnd)


def test_command_start(runner, tmnd):
    runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    result = runner.invoke(tmnd.main, ['start'])
    lines = result.output.splitlines()
    assert 'Starting fullnode test1:' in lines
    for line in lines:
        assert '✗' not in line
    _clean(tmnd)


def test_command_start_ignore(runner, tmnd):
    result = runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    result = runner.invoke(tmnd.main, ['start', '--name', 'test'])
    lines = result.output.splitlines()
    assert '! warning: fullnode test1 is already configured' in lines
    _clean(tmnd)


def test_command_stop(runner, tmnd):
    runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    result = runner.invoke(tmnd.main, ['stop'])
    lines = result.output.splitlines()
    assert 'Stopping fullnode test1:' in lines
    for line in lines:
        assert '✗' not in line
    _clean(tmnd)


def test_command_status(runner, tmnd):
    runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    result = runner.invoke(tmnd.main, ['status'])
    lines = result.output.splitlines()
    assert 'fullnode test1 status:' in lines
    _clean(tmnd)


def test_command_inspect(runner, tmnd):
    runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    result = runner.invoke(tmnd.main, ['inspect'])
    lines = result.output.splitlines()
    assert 'fullnode test1 details:' in lines
    _clean(tmnd)


def test_command_update(runner, tmnd):
    runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    result = runner.invoke(tmnd.main, ['update'])
    lines = result.output.splitlines()
    assert 'Updating fullnode test1:' in lines
    for line in lines:
        assert '✗' not in line
    _clean(tmnd)


def test_command_remove(runner, tmnd):
    runner.invoke(tmnd.main, [
        'start', '--name', 'test1', '--net',
        'devnet', '--pkey',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ])
    result = runner.invoke(tmnd.main, ['remove', '--confirm'])
    lines = result.output.splitlines()
    assert 'Removing fullnode test1:' in lines
    for line in lines:
        assert '✗' not in line
    _clean(tmnd)
