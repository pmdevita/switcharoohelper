import praw
import time
import traceback
import prawcore.exceptions

from core.credentials import get_credentials, CredentialsLoader
from core.process import process
from core.history import SwitcharooLog
from core import constants as consts
from core.action import PrintAction, ModAction
from core.inbox import process_message, process_modmail

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

# if mode == 'production':
action = ModAction(reddit)
# elif mode == 'development':
#     action = PrintAction(reddit)
# else:
#     print("No mode defined in credentials")
#     exit(1)

last_switcharoo = SwitcharooLog(reddit)
last_switcharoo.sync_issues()

message_reading_cooldown = 0

def get_newest_id(subreddit, index=0):
    """Retrieves the newest post's id. Used for starting the last switcharoo history trackers"""
    return [i for i in subreddit.new(params={"limit": "1"})][index].id


print("SwitcharooHelper v{} using {} Ctrl+C to stop".format(consts.version, action.__class__.__name__))

while True:
    try:
        # Update the switcharoo log for any deleted posts
        last_switcharoo.verify()
        # Then grab the newest's submission ID
        last_check = last_switcharoo.last_submission()
        # If there is not one, grab the second newest submission (so that we start with the next, the newest)
        if last_check:
            last_check = last_check.submission_id
        else:
            last_check = get_newest_id(switcharoo, 50)

        submissions = []
        # This "before" is a little confusing, it means before it in the listing but it would be after it time-wise
        for submission in switcharoo.new(params={"before": "t3_{}".format(last_check)}):
            submissions.append(submission)

        if submissions:
            print("Processing new submissions...")

            # Reverse the list to be in chronological order and then process every submission
            submissions.reverse()

            for submission in submissions:
                process(reddit, submission, last_switcharoo, action)
                action.reset()

            print("Checked up to", submissions[len(submissions) - 1].id)
            # save_last_data(last_data, last_switcharoo)

        # for message in reddit.inbox.unread():
        #     process_message(reddit, last_switcharoo, message)

        if not message_reading_cooldown:
            for conversation in switcharoo.modmail.conversations(limit=100, state="mod"):
                process_modmail(reddit, last_switcharoo, conversation)
            message_reading_cooldown = 61
        message_reading_cooldown -= 1


        time.sleep(consts.sleep_time)

    except prawcore.exceptions.RequestException:    # Unable to connect to Reddit
        print("Unable to connect to Reddit, is the internet down?")
        time.sleep(consts.sleep_time * 2)

    except prawcore.exceptions.ResponseException as e:
        print("weird other exceptions?", e)
        time.sleep(consts.sleep_time * 2)

    except KeyboardInterrupt:
        print("\nExiting...")
        break

    except Exception as e:
        if mode == "production":
            reddit.redditor(operator).message("SH Error!", "Help I crashed!\n\n    {}".format(
                str(traceback.format_exc()).replace('\n', '\n    ')))
        raise
