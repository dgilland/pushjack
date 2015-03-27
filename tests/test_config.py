
from pushjack.config import Config

from .fixtures import parametrize


def test_config():
    config = Config({
        'FOO': 'foo',
        'ignored': ''
    })

    assert config['FOO'] == 'foo'
    assert not hasattr(config, 'ignored')

    class TestConfig(object):
        BAR = 'bar'
        ignored_again = ''

    assert not hasattr(config, 'BAR')

    config.from_object(TestConfig)

    assert config['BAR'] == TestConfig.BAR
    assert not hasattr(config, 'ignored_again')
