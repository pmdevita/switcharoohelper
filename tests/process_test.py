from datetime import datetime

import pytest

from switcharoo.config.issues import IssueTracker
from tests.mock import praw
from switcharoo.core.history import SwitcharooLog
from switcharoo.config.credentials import CredentialsLoader
from switcharoo.config import constants as consts


@pytest.fixture(scope="function")
def reddit():
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
def process(mocker):
    import switcharoo.core.process
    mocker.patch.object(switcharoo.core.process, "praw", praw)


@pytest.fixture(scope="function")
def first_roo(reddit, process, last_switcharoo, action):
    import switcharoo.core.process
    first = reddit.submission("firsts", link_post=False, body=None,
                              date=datetime(2020, 1, 1, 1), author="otheruser",
                              subreddit="subreddit1")
    first_comment = reddit.comment("firstc", first,
                                   f"Ah the old reddit [switcharoo](https://reddit.com/r/subreddit0/comments/aaaaa/_/?context=3)",
                                   "user1",
                                   date=datetime(2020, 1, 1, 2))
    first_submission = reddit.submission("firstr", link_post=True, date=datetime(2020, 1, 1, 3), author="user1",
                                         body=f"https://reddit.com{first_comment.permalink}?context=3",
                                         subreddit="switcharoo")
    switcharoo.core.process.process(reddit, first_submission, last_switcharoo, action)
    return first_comment


class TestProcess:
    def test_normal(self, reddit, last_switcharoo, action, first_roo, process):
        import switcharoo.core.process
        second = reddit.submission("abcde", link_post=False, body=None,
                                   date=datetime(2020, 2, 1, 1), author="otheruser",
                                   subreddit="subreddit1")
        second_comment = reddit.comment("12345", second,
                                        f"Ah the old reddit [switcharoo]"
                                        f"({first_roo.get_link_and_context(3)})",
                                        "user1",
                                        date=datetime(2020, 2, 1, 2))
        second_submission = reddit.submission("abcdf", link_post=True, date=datetime(2020, 2, 1, 3), author="user1",
                                              body=second_comment.get_link_and_context(3),
                                              subreddit="switcharoo")

        switcharoo.core.process.process(reddit, second_submission, last_switcharoo, action)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        assert issues == model_issues

    def test_pre2020_user_mismatch(self, reddit, last_switcharoo, action, process, first_roo):
        import switcharoo.core.process
        second = reddit.submission("abcde", link_post=False, body=None,
                                   date=datetime(2020, 2, 1, 1), author="otheruser",
                                   subreddit="subreddit1")
        second_comment = reddit.comment("12345", second,
                                        f"Ah the old reddit [switcharoo]"
                                        f"({first_roo.get_link_and_context(3)})",
                                        "user1",
                                        date=datetime(2020, 2, 1, 2))
        second_submission = reddit.submission("abcdf", link_post=True, date=datetime(2020, 2, 1, 3), author="wrongUuser",
                                              body=second_comment.get_link_and_context(3),
                                              subreddit="switcharoo")

        switcharoo.core.process.process(reddit, second_submission, last_switcharoo, action)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        assert issues == model_issues

    def test_user_mismatch(self, reddit, last_switcharoo, action, process, first_roo):
        import switcharoo.core.process
        second = reddit.submission("abcde", link_post=False, body=None,
                                   date=datetime(2022, 2, 1, 1), author="otheruser",
                                   subreddit="subreddit1")
        second_comment = reddit.comment("12345", second,
                                        f"Ah the old reddit [switcharoo]"
                                        f"({first_roo.get_link_and_context(3)})",
                                        "user1",
                                        date=datetime(2022, 2, 1, 2))
        second_submission = reddit.submission("abcdf", link_post=True, date=datetime(2022, 2, 1, 3), author="wrongUuser",
                                              body=second_comment.get_link_and_context(3),
                                              subreddit="switcharoo")

        switcharoo.core.process.process(reddit, second_submission, last_switcharoo, action)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        model_issues.user_mismatch = True
        assert issues == model_issues

    def test_sub_privated(self, reddit, last_switcharoo, action, process, first_roo):
        import switcharoo.core.process
        second = reddit.submission("abcde", link_post=False, body=None,
                                   date=datetime(2022, 2, 1, 1), author="otheruser",
                                   subreddit="subreddit2")
        second_comment = reddit.comment("12345", second,
                                        f"Ah the old reddit [switcharoo]"
                                        f"({first_roo.get_link_and_context(3)})",
                                        "user1",
                                        date=datetime(2022, 2, 1, 2))
        second.private = True
        second_comment.private = True
        second_submission = reddit.submission("abcdf", link_post=True, date=datetime(2022, 2, 1, 3), author="user1",
                                              body=second_comment.get_link_and_context(3),
                                              subreddit="switcharoo")

        switcharoo.core.process.process(reddit, second_submission, last_switcharoo, action)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        model_issues.subreddit_privated = True
        assert issues == model_issues

    # Should be moved to a `reprocess` test suite
    def test_sub_privated_allowed(self, reddit, last_switcharoo, action, process, first_roo):
        import switcharoo.core.process
        # Do a first pass process
        last_switcharoo.update_privated_sub("subreddit2", allowed=True, update_requested=False)
        second = reddit.submission("abcde", link_post=False, body=None,
                                   date=datetime(2022, 2, 1, 1), author="otheruser",
                                   subreddit="subreddit2")
        second_comment = reddit.comment("12345", second,
                                        f"Ah the old reddit [switcharoo]"
                                        f"({first_roo.get_link_and_context(3)})",
                                        "user1",
                                        date=datetime(2022, 2, 1, 2))
        second_submission = reddit.submission("abcdf", link_post=True, date=datetime(2022, 2, 1, 3), author="user1",
                                              body=second_comment.get_link_and_context(3),
                                              subreddit="switcharoo")
        switcharoo.core.process.process(reddit, second_submission, last_switcharoo, action)
        # Now, the roo has been privated in the meantime, update the issues
        second.private = True
        second_comment.private = True
        roo = last_switcharoo.get_roo(submission_id=second_submission.id)
        switcharoo.core.process.reprocess(reddit, roo, last_switcharoo, action, stage=consts.ALL_ROOS)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        assert issues == model_issues

    # Should be moved to a `reprocess` test suite
    def test_sub_privated_rejected(self, reddit, last_switcharoo, action, process, first_roo):
        import switcharoo.core.process
        # Do a first pass process
        last_switcharoo.update_privated_sub("subreddit2", allowed=False, update_requested=False)
        second = reddit.submission("abcde", link_post=False, body=None,
                                   date=datetime(2022, 2, 1, 1), author="otheruser",
                                   subreddit="subreddit2")
        second_comment = reddit.comment("12345", second,
                                        f"Ah the old reddit [switcharoo]"
                                        f"({first_roo.get_link_and_context(3)})",
                                        "user1",
                                        date=datetime(2022, 2, 1, 2))
        second_submission = reddit.submission("abcdf", link_post=True, date=datetime(2022, 2, 1, 3), author="user1",
                                              body=second_comment.get_link_and_context(3),
                                              subreddit="switcharoo")
        switcharoo.core.process.process(reddit, second_submission, last_switcharoo, action)
        # Now, the roo has been privated in the meantime, update the issues
        second.private = True
        second_comment.private = True
        roo = last_switcharoo.get_roo(submission_id=second_submission.id)
        switcharoo.core.process.reprocess(reddit, roo, last_switcharoo, action, stage=consts.ALL_ROOS)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        model_issues.subreddit_privated = True
        model_issues.submission_deleted = True
        assert issues == model_issues

    def test_comment_linked_bad_roo(self, reddit, last_switcharoo, action, process, first_roo):
        import switcharoo.core.process
        # Do a first pass process
        last_switcharoo.update_privated_sub("subreddit2", allowed=False, update_requested=False)
        bad = reddit.submission("abcde", link_post=False, body=None,
                                date=datetime(2022, 2, 1, 1), author="otheruser",
                                subreddit="subreddit2")
        bad_comment = reddit.comment("12345", bad,
                                     "I'm a bad roo!",
                                     "user1",
                                     date=datetime(2022, 2, 1, 2))
        bad_submission = reddit.submission("abcdf", link_post=True, date=datetime(2022, 2, 1, 3), author="user1",
                                           body=bad_comment.get_link_and_context(3),
                                           subreddit="switcharoo")
        switcharoo.core.process.process(reddit, bad_submission, last_switcharoo, action)
        second = reddit.submission("zbcdf", link_post=False, body=None,
                                   date=datetime(2022, 2, 1, 1), author="otheruser",
                                   subreddit="subreddit2")
        second_comment = reddit.comment("12346", second,
                                        f"Ah the old reddit [switcharoo]"
                                        f"({bad_comment.get_link_and_context(3)})",
                                        "user1",
                                        date=datetime(2022, 2, 1, 2))
        second_submission = reddit.submission("zbcdg", link_post=True, date=datetime(2022, 2, 1, 3), author="user1",
                                              body=second_comment.get_link_and_context(3),
                                              subreddit="switcharoo")
        switcharoo.core.process.process(reddit, second_submission, last_switcharoo, action)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        model_issues.comment_linked_bad_roo = True
        assert issues == model_issues