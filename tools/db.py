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

def roo_id_to_issues(id):
    roo = last_switcharoo.get_roo(id)
    issues = last_switcharoo.get_issues(roo)
    for i in issues:
        print(i)