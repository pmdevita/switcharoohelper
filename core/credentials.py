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