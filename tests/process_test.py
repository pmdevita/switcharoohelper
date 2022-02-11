import pytest
import praw
import json
from pathlib import Path

from switcharoo.config.credentials import CredentialsLoader
cred_file = Path(__file__).parent.parent / "credentials.ini"
credentials = CredentialsLoader().get_credentials(cred_file)


from switcharoo.core.history import SwitcharooLog
from switcharoo.config import constants as consts
from switcharoo.core.action import ModAction
from switcharoo.core.process import process


@pytest.fixture(scope="module")
def reddit():
    cred_file = Path(__file__).parent.parent / "credentials.ini"
    credentials = CredentialsLoader().get_credentials(cred_file)
    reddit_creds = credentials["reddit"]
    reddit = praw.Reddit(client_id=reddit_creds["client_id"],
                         client_secret=reddit_creds["client_secret"],
                         user_agent=consts.user_agent,
                         username=reddit_creds["username"],
                         password=reddit_creds["password"])
    return reddit


@pytest.fixture(scope="function")
def last_switcharoo(reddit):
    last_switcharoo = SwitcharooLog(reddit, {"type": "sqlite", "db_file": ":memory:"})
    last_switcharoo.sync_issues()
    return last_switcharoo


@pytest.fixture(scope="function")
def action(reddit):
    return ModAction(reddit)


def reddit_request_filter(data):
    body = data["body"]["string"].decode("utf-8")
    try:
        token = json.loads(body)
        if isinstance(token, dict):
            if token.get("access_token", False):
                token["access_token"] = ";)"
        data["body"]["string"] = json.dumps(token).encode("utf-8")
    except json.decoder.JSONDecodeError:
        pass

    return data


@pytest.fixture(scope='module')
def vcr_config():
    return {
        # Replace the Authorization request header with "DUMMY" in cassettes
        "filter_headers": [('authorization', 'Bearer NoToken4U')],
        "filter_query_parameters": ["password", "username"],
        "filter_post_data_parameters": ["password", "username"],
        "decode_compressed_response": True,
        "before_record_response": reddit_request_filter
    }


class TestProcess:
    @pytest.mark.vcr()
    def test_normal(self, reddit, last_switcharoo, action):
        print(reddit, last_switcharoo)
        first = reddit.submission("soig3l")
        second = reddit.submission("somyfp")
        process(reddit, first, last_switcharoo, action)
        process(reddit, second, last_switcharoo, action)

        assert True is True

