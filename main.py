import praw
import time

from credentials import get_credentials
from core import process
from core import constants as consts
from core.action import PrintAction, ModAction
from core.last_data import LastData
from core.last_switcharoo import LastSwitcharoo

credentials = get_credentials()

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent.format(consts.version),
                     username=credentials["username"],
                     password=credentials["password"])

switcharoo = reddit.subreddit("switcharoo")

# Create object to perform actions
action = ModAction(reddit)
# action = PrintAction(reddit)

# Restore or make data for last check and last thread in switcharoo
last_data = LastData()

# UTC time of last post checked, used to find new posts
# If not, we just start checking from this point forward
last_check = last_data.get("last_check", time.time())

# Track last submissions in order to check for correct linking
# and request corrections
last_switcharoo = LastSwitcharoo(reddit, last_data.get("last_switcharoo", None))


# Save last_data to file
def save_last_data(last_switcharoo, last_data):
    last_data.data["last_check"] = last_check
    last_data.data["last_switcharoo"] = last_switcharoo.save()
    last_data.save()


print("Ctrl+C to stop")

try:
    while True:
        # Get submissions and reverse them
        submissions = []
        for submission in switcharoo.submissions(start=last_check):
            submissions.append(submission)

        if submissions:
            print("Processing submissions...")
            # Verify the roos that will be linked to still exist
            last_switcharoo.verify()
        submissions.reverse()

        # Process every submission
        for submission in submissions:
            process(reddit, submission, last_switcharoo, action)
            action.reset()
            # Add this submission's url to the tracker
            last_switcharoo.add_last(submission.url)

        # Get the creation date from the last submission to look for anything more recent than it next loop
        if submissions:
            last_check = submissions[len(submissions) - 1].created_utc + 1
            print("Checked up to", last_check)
            save_last_data(last_switcharoo, last_data)
        time.sleep(consts.sleep_time)

except KeyboardInterrupt:
    print("\nExiting...")
    # save_last_data(last_good_submission, last_data)
