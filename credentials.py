import json


def get_credentials(file=None):
    path = "credentials.json"
    if file:
        path = file

    with open(path, "r") as f:
        credentials = json.load(f)

    return credentials
