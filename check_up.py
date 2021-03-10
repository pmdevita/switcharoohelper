import praw
import time
import traceback
import prawcore.exceptions

from core.credentials import get_credentials, CredentialsLoader
from core.process import reprocess
from core.history import SwitcharooLog
from core import constants as consts
from core.action import PrintAction, ModAction

credentials = CredentialsLoader.get_credentials()['reddit']

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

switcharoo = reddit.subreddit("switcharoo")

# Action object tracks switcharoo and performs a final action (delete/comment)
mode = CredentialsLoader.get_credentials()['general']['mode']
operator = CredentialsLoader.get_credentials()['general']['operator']

if mode == 'production':
    action = ModAction(reddit)
elif mode == 'development':
    action = PrintAction(reddit)
else:
    print("No mode defined in credentials")
    exit(1)

last_switcharoo = SwitcharooLog(reddit)
last_switcharoo.sync_issues()

def get_newest_id(subreddit, index=0):
    """Retrieves the newest post's id. Used for starting the last switcharoo history trackers"""
    return [i for i in subreddit.new(params={"limit": "1"})][index].id


print("SwitcharooHelper Check-up v{} using {} Ctrl+C to stop".format(consts.version, action.__class__.__name__))


# while True:
try:
    # Mark all bad roos (or unmark bad roos)
    roos = last_switcharoo.get_roos()
    for roo in roos:
        reprocess(reddit, roo, last_switcharoo, action, consts.ONLY_BAD)

    # Now remove ignored posts
    # for roo in roos:
    #     reprocess(reddit, roo, last_switcharoo, action, consts.ONLY_IGNORED)

    # Everything should be updated, perform full actions
    for roo in roos:
        reprocess(reddit, roo, last_switcharoo, action, consts.ALL_ROOS)

    # time.sleep(consts.sleep_time)

except prawcore.exceptions.RequestException:    # Unable to connect to Reddit
    print("Unable to connect to Reddit, is the internet down?")
    time.sleep(consts.sleep_time * 2)

except prawcore.exceptions.ResponseException as e:
    print("weird other exceptions?", e)
    time.sleep(consts.sleep_time * 2)

except KeyboardInterrupt:
    print("\nExiting...")
    # break

except Exception as e:
    if mode == "production":
        reddit.redditor(operator).message("SH Error!", "Help I crashed!\n\n    {}".format(
            str(traceback.format_exc()).replace('\n', '\n    ')))
    raise
