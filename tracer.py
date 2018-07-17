import praw
import time
import pendulum

import prawcore.exceptions

from core.credentials import get_credentials
from core import constants as consts
from core import parse

credentials = get_credentials()

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent.format(consts.version),
                     username=credentials["username"],
                     password=credentials["password"])

switcharoo = reddit.subreddit("switcharoo")

def get_newest_id(subreddit, index=0):
    """Retrieves the newest post's id. Used for starting the last switcharoo history trackers"""
    return [i for i in subreddit.new(params={"limit": "1"})][index].url

print("Paste the URL of the switcharoo comment you'd like to start at\nOr leave blank to start at the newest")
url = input()

if not url:
    url = get_newest_id(switcharoo, 1)

print("SwitcharooHelper Tracer v{} Ctrl+C to stop".format(consts.version))

while True:
    try:
        if url:
            thread_id, comment_id = parse.thread_url_to_id(url)
        else:
            print("\nUnable to find a link. Go here, find the switcharoo, and paste the link \n"
                  "to the next one here. \n\n", last_url)
            url = input()
            thread_id, comment_id = parse.thread_url_to_id(url)

        comment = reddit.comment(comment_id)

        date = pendulum.from_timestamp(comment.created_utc, tz="UTC")
        date = date.in_timezone("local")

        print("{} {} {}".format(comment.body, date, comment.permalink))

        last_url = url
        url = parse.parse_comment(comment.body)
        # print(url)

    except prawcore.exceptions.RequestException:    # Unable to connect to Reddit
        print("Unable to connect to Reddit, is the internet down?")
        time.sleep(consts.sleep_time * 2)

    except prawcore.exceptions.ResponseException as e:
        print("weird other exceptions?", e)
        time.sleep(consts.sleep_time * 2)

    except KeyboardInterrupt:
        print("\nExiting...")
        break