# global config
from collections import namedtuple

Target = namedtuple('Target', ['knora', 'sipi'])


class ConfigException(Exception):
    pass


class Config:

    targets = dict(local=Target('http://localhost:3333', 'http://localhost:1024'),
                   test=Target('http://knora-test.unil.ch:80', 'http://sipi-test.unil.ch:80'),
                   demo=Target('http://knora-demo.unil.ch:80', 'http://sipi-demo.unil.ch:80'),
                   prod=Target("http://knora.unil.ch:80", 'http://sipi.unil.ch:80'))

    def __init__(self, target, use_sipi_session=True, dry_run=False, source=None):

        self.dry_run = dry_run

        self.target = Config.targets.get(target)
        if self.target is None:
            raise ConfigException("bad target: " + target)

        self.use_sipi_session = use_sipi_session

        self.source = source


