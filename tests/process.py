import unittest
import os
from tests.shims import praw
from datetime import datetime

from core.credentials import get_credentials, CredentialsLoader

# Configure config first
credentials = CredentialsLoader().get_credentials("configs/process.ini")
from core.process import check_errors
from core.history import SwitcharooLog
from core.issues import IssueTracker


def reset_database(reddit, last_switcharoo: SwitcharooLog = None):
    if last_switcharoo:
        last_switcharoo.unbind()
    if os.path.exists(f"../{credentials['database']['db_file']}"):
        os.remove(f"../{credentials['database']['db_file']}")
    return SwitcharooLog(reddit)


def reddit_url_gen(subreddit, thread_id, comment_id=None, context=None):
    string = f"https://reddit.com/r/{subreddit}/comments/{thread_id}/_/"
    if comment_id:
        string += f"{comment_id}/"
    if context:
        string += f"?context={context}"
    return string


def gen_url_and_roo(reddit, last_switcharoo, subreddit, user, submission_id, thread_id, comment_id, context, time,
                    init_db=False):
    if init_db:
        roo = last_switcharoo.add(submission_id=submission_id,
                                  link_post=True, time=time,
                                  user=user)
    else:
        roo = last_switcharoo.add(submission_id=submission_id, thread_id=thread_id, comment_id=comment_id,
                                  link_post=True, context=context, time=time,
                                  user=user, subreddit=subreddit)
    url = reddit_url_gen(subreddit, thread_id, comment_id, context)
    submission = reddit.submission(submission_id, True, url, time, user, "switcharoo")
    reddit.submission(thread_id, False, "some text post", time, user, subreddit)
    return roo, url, submission


global last_switcharoo
last_switcharoo = None


class CheckErrors(unittest.TestCase):
    def test_normal(self):
        reddit = praw.Reddit(username=credentials['reddit']['username'])
        global last_switcharoo
        last_switcharoo = reset_database(reddit, last_switcharoo)
        previous_roo, previous_url, previous_submission = gen_url_and_roo(reddit, last_switcharoo, "sub1", "user1",
                                                                          "000000", "aaaaaa", "123abcd", 3,
                                                                          datetime(month=4, day=1, year=2021))
        roo, url, submission = gen_url_and_roo(reddit, last_switcharoo, "sub1", "user1",
                                               "000001", "aaaaab", "123abce", 3,
                                               datetime(month=4, day=2, year=2021), init_db=True)
        reddit.comment("123abce", f"[Ah the ol' Reddit switcharoo!]({previous_url})", "user1",
                       datetime(month=1, day=2, year=2020))
        expected_tracker = IssueTracker()
        tracker = check_errors(reddit, last_switcharoo, roo, init_db=True, submission=submission)
        self.assertTrue(tracker == expected_tracker)

    def test_user_mismatch(self):
        reddit = praw.Reddit(username=credentials['reddit']['username'])
        global last_switcharoo
        last_switcharoo = reset_database(reddit, last_switcharoo)
        previous_roo, previous_url, previous_submission = gen_url_and_roo(reddit, last_switcharoo, "sub1", "user1",
                                                                          "000000", "aaaaaa", "123abcd", 3,
                                                                          datetime(month=4, day=1, year=2021))
        roo, url, submission = gen_url_and_roo(reddit, last_switcharoo, "sub1", "user1",
                                               "000001", "aaaaab", "123abce", 3,
                                               datetime(month=4, day=2, year=2021), init_db=True)
        reddit.comment("123abce", f"[Ah the ol' Reddit switcharoo!]({previous_url})", "user2",
                       datetime(month=4, day=2, year=2020))
        expected_tracker = IssueTracker()
        expected_tracker.user_mismatch = True
        tracker = check_errors(reddit, last_switcharoo, roo, init_db=True, submission=submission)
        self.assertTrue(tracker == expected_tracker)

    def test_sub_privated(self):
        reddit = praw.Reddit(username=credentials['reddit']['username'])
        global last_switcharoo
        last_switcharoo = reset_database(reddit, last_switcharoo)
        last_switcharoo.update_privated_sub("sub2", allowed=False, update_requested=False)
        previous_roo, previous_url, previous_submission = gen_url_and_roo(reddit, last_switcharoo, "sub1", "user1",
                                                                          "000000", "aaaaaa", "123abcd", 3,
                                                                          datetime(month=4, day=1, year=2021))
        roo, url, submission = gen_url_and_roo(reddit, last_switcharoo, "sub2", "user1",
                                               "000001", "aaaaab", "123abce", 3,
                                               datetime(month=4, day=2, year=2021), init_db=True)
        reddit.submission("aaaaab").private = True
        reddit.comment("123abce", f"[Ah the ol' Reddit switcharoo!]({previous_url})", "user1",
                       datetime(month=4, day=2, year=2020), private=True)
        expected_tracker = IssueTracker()
        expected_tracker.subreddit_privated = True
        tracker = check_errors(reddit, last_switcharoo, roo, init_db=True, submission=submission)
        self.assertTrue(tracker == expected_tracker)