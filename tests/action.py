import unittest
import os
from tests.shims import praw
from datetime import datetime, timedelta

from core.credentials import CredentialsLoader
from pathlib import Path
# Configure config first
tests_folder = Path(os.path.dirname(os.path.realpath(__file__)))
credentials = CredentialsLoader().get_credentials(tests_folder / "configs/action.ini")

from core.reddit import ReplyObject
from core.action import increment_user_fixes


def reset_database(reddit, last_switcharoo: SwitcharooLog = None):
    if last_switcharoo:
        last_switcharoo.unbind()
    if os.path.exists(tests_folder / ".." / f"{credentials['database']['db_file']}"):
        os.remove(tests_folder / ".." / f"{credentials['database']['db_file']}")
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


class ActionMethods(unittest.TestCase):
    def test_too_new_to_fix_flair(self):
        reddit = praw.Reddit(username=credentials['reddit']['username'])
        global last_switcharoo
        last_switcharoo = reset_database(reddit, last_switcharoo)
        roo, url, submission = gen_url_and_roo(reddit, last_switcharoo, "sub1", "user1",
                                               "000001", "aaaaab", "123abce", 3,
                                               datetime.now())
        roo = last_switcharoo.search(comment_id="123abce")
        reply_object = ReplyObject.from_roo(roo)

        increment_user_fixes(last_switcharoo, reply_object)
        f = last_switcharoo.check_user_flair(roo.user)
        if f:
            self.assertEqual(f.fixes, 0)
        else:
            self.assertEqual(f, None)

    def test_old_enough_to_fix_flair(self):
        reddit = praw.Reddit(username=credentials['reddit']['username'])
        global last_switcharoo
        last_switcharoo = reset_database(reddit, last_switcharoo)
        roo, url, submission = gen_url_and_roo(reddit, last_switcharoo, "sub1", "user1",
                                               "000001", "aaaaab", "123abce", 3,
                                               datetime.now() - timedelta(weeks=12))
        roo = last_switcharoo.search(comment_id="123abce")
        reply_object = ReplyObject.from_roo(roo)

        increment_user_fixes(last_switcharoo, reply_object)
        f = last_switcharoo.check_user_flair(roo.user)
        self.assertEqual(f.fixes, 1)

        increment_user_fixes(last_switcharoo, reply_object)
        f = last_switcharoo.check_user_flair(roo.user)
        self.assertEqual(f.fixes, 2)

