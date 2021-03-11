from core.credentials import CredentialsLoader
from core.history import *
from core import constants as consts
credentials = CredentialsLoader.get_credentials()['reddit']

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

last_switcharoo = SwitcharooLog(reddit)


def roo_id_to_submission(id):
    roo = last_switcharoo.get_roo(id)
    print(f"https://reddit.com{roo.submission.permalink}")

def roo_id_to_issues(id):
    roo = last_switcharoo.get_roo(id)
    issues = last_switcharoo.get_issues(roo)
    for i in issues:
        print(i)