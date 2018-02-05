import praw
import time

from credentials import get_credentials
from core import process
from core import constants as consts
from core.action import PrintAction, ModAction
from core.last_data import LastData

credentials = get_credentials()

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent.format(consts.version),
                     username=credentials["username"],
                     password=credentials["password"])

switcharoo = reddit.subreddit("switcharoo")

# Create object to perform actions
action = ModAction(reddit)

# Restore or make data for last check and last thread in switcharoo
last_data = LastData()

# UTC time of last post checked, used to find new posts
last_check = last_data.get("last_check", time.time() - 60 * 60 * 24 * 4)
# Last switcharoo submission that was cleared
last_good_submission = last_data.get("last_good_submission", None)
# Latest switcharoo submission. Used for determining if the user tried to link right
last_submission = last_data.get("last_submission", None)

# Save last_data to file
def save_last_data(last_good_submission, last_data):
    print(last_good_submission)
    last_good_submission.pop("submission", None)
    last_data.data["last_check"] = last_check
    last_data.data["last_good_submission"] = last_good_submission
    last_data.data["last_submission"] = last_submission
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
        submissions.reverse()

        # Process every submission
        for submission in submissions:
            last_good_submission, last_submission = process(reddit, submission, last_good_submission, last_submission,
                                                            action)
            action.reset()

        # Get the creation date from the last submission to look for anything more recent than it next loop
        if submissions:
            last_check = submissions[len(submissions) - 1].created_utc + 1
            print("Checked up to", last_check)
            save_last_data(last_good_submission, last_data)
        time.sleep(consts.sleep_time)

except KeyboardInterrupt:
    print("Saving and exiting...")
    save_last_data(last_good_submission, last_data)
