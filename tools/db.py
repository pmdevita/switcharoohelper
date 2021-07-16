from core.credentials import CredentialsLoader
from core.history import *
from core import constants as consts
from core.action import PrintAction, ModAction
from core.process import reprocess, check_errors, add_comment
credentials = CredentialsLoader.get_credentials()['reddit']

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

last_switcharoo = SwitcharooLog(reddit)

# Action object tracks switcharoo and performs a final action (delete/comment)
mode = CredentialsLoader.get_credentials()['general']['mode']

if mode == 'production':
    action = ModAction(reddit)
elif mode == 'development':
    action = PrintAction(reddit)


def roo_id_to_submission(id):
    roo = last_switcharoo.get_roo(id)
    print(f"https://reddit.com{roo.submission.permalink}")


def roo_id_to_comment(id):
    roo = last_switcharoo.get_roo(id)
    print(f"https://reddit.com{roo.comment.permalink}")


def roo_id_to_issues(id):
    roo = last_switcharoo.get_roo(id)
    issues = last_switcharoo.get_issues(roo)
    for i in issues:
        print(i)


def roo_id_to_current_issues(id):
    roo = last_switcharoo.get_roo(id)
    if roo.submission:
        issues = check_errors(reddit, last_switcharoo, roo, submission=roo.submission)
    else:
        issues = check_errors(reddit, last_switcharoo, roo, comment=roo.comment)
    for i in issues:
        print(i)


def last_good_of_roo_id(id):
    roo = last_switcharoo.get_roo(id)
    return last_switcharoo.last_good(roo)


def roo_id_info(id):
    roo_id_to_submission(id)
    print("DB issues")
    roo_id_to_issues(id)
    print("Current issues")
    roo_id_to_current_issues(id)
    print("Last good:", last_good_of_roo_id(id))


def good_roos_before_bot():
    return last_switcharoo.stats.num_of_roos(before=datetime(year=2018, day=12, month=2, hour=23))


def good_roos_after_bot():
    return last_switcharoo.stats.num_of_good_roos(after=datetime(year=2018, day=12, month=2, hour=23), axed_issues=False)
