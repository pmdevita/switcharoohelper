import praw
import time

from credentials import get_credentials
from core import process, last_data, action
from core import constants as consts

credentials = get_credentials()

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent.format(consts.version),
                     username=credentials["username"],
                     password=credentials["password"])

switcharoo = reddit.subreddit("switcharoo")

# Create object to perform actions
act = action.PrintAction(reddit)

# Restore or make data for last check and last thread in switcharoo
data = last_data.LastData()
last_check = data.data.get("last_check", time.time()-60*60*24*5)
last_thread = data.data.get("last_thread", None)
if last_thread:
    reddit.submission(last_thread)

print("Ctrl+C to stop")

try:
    while True:
        # Get submissions and reverse them
        print("Checking submissions...")
        submissions = []
        for submission in switcharoo.submissions(start=last_check):
            submissions.append(submission)
        submissions.reverse()

        # Process every submission
        for submission in submissions:
            last_thread = process(reddit, submission, last_thread, act)

        # Get the creation date from the last submission to look for anything more recent than it next loop
        if submissions:
            last_check = submissions[len(submissions) - 1].created_utc + 1
            print("last check", last_check)
            data.save()
        time.sleep(consts.sleep_time)

except KeyboardInterrupt:
    data.data["last_check"] = last_check
    last_thread.pop("submission", None)
    data.data["last_thread"] = last_thread
    data.save()
