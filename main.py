import praw
import time

from core.credentials import get_credentials
from core import process, LastData, SwitcharooLog
from core import constants as consts
from core.action import PrintAction, ModAction

credentials = get_credentials()

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent.format(consts.version),
                     username=credentials["username"],
                     password=credentials["password"])

switcharoo = reddit.subreddit("switcharoo")

# Action object tracks switcharoo and performs a final action (delete/comment)
# action = ModAction(reddit)
action = PrintAction(reddit)
settled_action = PrintAction(reddit)

# LastData keeps track of data from the last time the helper was run so we can restore state
last_data = LastData()

# LastSwitcharoo keeps a log of all switcharoos, used to help users relink their roo
# LastSwitcharoo also keeps track of switcharoos so we can do a final settling a few days later (after things get
#   removed and moderators shift things around)
last_switcharoo = SwitcharooLog(reddit, last_data.get("last_switcharoo", None))


def get_newest_id(subreddit, index=0):
    """Retrieves the newest post's id. Used for starting the last switcharoo history trackers"""
    return [i for i in subreddit.new(params={"limit": "1"})][index].id

# Save last_data to file
def save_last_data(last_data, last_switcharoo):
    last_data.data["last_switcharoo"] = last_switcharoo.save()
    last_data.save()


print("SwitcharooHelper v{} using {} Ctrl+C to stop".format(consts.version, action.__class__.__name__))

try:
    while True:
        # Update the switcharoo log for any deleted posts
        last_switcharoo.verify()
        # Then grab the newest's submission ID
        last_check = last_switcharoo.last_good()
        # If there is not one, grab the second newest submission (so that we start with the next, the newest)
        if not last_check:
            last_check = get_newest_id(switcharoo, 1)

        submissions = []
        for submission in switcharoo.new(params={"before": "t3_{}".format(last_check)}):
            submissions.append(submission)

        if submissions:
            print("Processing new submissions...")

            submissions.reverse()

            # Process every submission
            for submission in submissions:
                process(reddit, submission, last_switcharoo, action)
                action.reset()
                # Add this submission's url to the tracker
                last_switcharoo.add_last(submission.url)

            print("Checked up to", submissions[len(submissions) - 1].id)
            save_last_data(last_data, last_switcharoo)

        time.sleep(consts.sleep_time)

except KeyboardInterrupt:
    print("\nExiting...")
