from datetime import datetime

import pytest

import switcharoo.core
from switcharoo.config.credentials import CredentialsLoader
from switcharoo.core.history import SwitcharooLog
from tests.mock import praw


@pytest.fixture(scope="function")
def reddit(mocker):
    # Monkeypatch in the mock praw library
    import switcharoo.core.process
    mocker.patch.object(switcharoo.core.process, "praw", praw)
    mocker.patch.object(switcharoo.core.parse, "praw", praw)

    reddit = praw.Reddit(username="switcharoohelper")
    return reddit


@pytest.fixture(scope="function")
def last_switcharoo(reddit):
    last_switcharoo = SwitcharooLog(reddit, {"type": "sqlite", "db_file": ":memory:"})
    last_switcharoo.sync_issues()
    yield last_switcharoo
    last_switcharoo.unbind()


@pytest.fixture(scope="function")
def mock_creds(mocker):
    mocker.patch.object(CredentialsLoader, 'config', {
        "general": {
            "dry_run": "true"
        },
        "reddit": {
            "username": "switcharoohelper"
        }
    })


@pytest.fixture(scope="function")
def action(reddit, mock_creds):
    from switcharoo.core.action import ModAction
    return ModAction(reddit)


@pytest.fixture(scope="function")
def first_roo(reddit, last_switcharoo, action):
    import switcharoo.core.process
    first = reddit.submission("firsts", link_post=False, content=None,
                              date=datetime(2020, 1, 1, 1), author="otheruser",
                              subreddit="subreddit1")
    first_comment = reddit.comment("firstc", first,
                                   f"Ah the old reddit [switcharoo](https://reddit.com/r/subreddit0/comments/aaaaa/_/?context=3)",
                                   "user1",
                                   date=datetime(2020, 1, 1, 2))
    first_submission = reddit.submission("firstr", link_post=True, date=datetime(2020, 1, 1, 3), author="user1",
                                         content=first_comment.get_link_and_context(3),
                                         subreddit="switcharoo")
    switcharoo.core.process.process(reddit, first_submission, last_switcharoo, action)
    return first_comment
