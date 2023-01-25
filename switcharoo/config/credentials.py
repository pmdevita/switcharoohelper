import os
from pathlib import Path
import configparser


def get_credentials(file=None):
    path = "credentials.ini"
    if file:
        path = file

    config = configparser.ConfigParser()
    config.read(path)

    if len(config.sections()) != 1:
        raise Exception("config file is wrong")
    creds = config[config.sections()[0]]
    return creds


class CredentialsLoader:
    config = None
    path = Path(os.getcwd()) / "credentials.ini"

    @classmethod
    def get_credentials(cls, file=None):
        if not cls.config:
            if file:
                cls.path = file

            cls.config = configparser.ConfigParser()
            cls.config.read(cls.path)

            if len(cls.config.sections()) < 1:
                raise Exception("config file is wrong")
        return cls.config

    @classmethod
    def set_credential(cls, section, name, value):
        cls.config.set(section, name, value)
        with open(cls.path, "w") as f:
            cls.config.write(f)
