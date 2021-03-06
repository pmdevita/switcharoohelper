import praw
import time
import pendulum

import prawcore.exceptions

from core.credentials import CredentialsLoader
from core import constants as consts
from core import parse
from core.history import SwitcharooLog

credentials = CredentialsLoader.get_credentials()['reddit']

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

switcharoo = reddit.subreddit("switcharoo")

log = SwitcharooLog(reddit)

def get_newest_id(subreddit, index=0):
    """Retrieves the newest post's id. Used for starting the last switcharoo history trackers"""
    return [i for i in subreddit.new(params={"limit": "1"})][index].url

print("Paste the URL of the switcharoo comment you'd like to start at\nOr leave blank to start at the newest")
url = input().strip()

if not url:
    url = get_newest_id(switcharoo, 0)

roo_count = 0

print("SwitcharooHelper Tracer v{} Ctrl+C to stop".format(consts.version))

while True:
    try:
        if url:
            if isinstance(url, str):
                thread_id, comment_id = parse.thread_url_to_id(url)
                if not comment_id:
                    print(url, comment_id)
        else:
            print("Unable to find a link.")
            roo = log.search(thread_id, comment_id)
            after = log.last_good(roo)
            before = log.next_good(roo)
            print("-".join([str(i) for i in[before, roo, after]]))
            print("I think you should link", "https://reddit.com" + before.submission.permalink, "to", "https://reddit.com" + after.submission.permalink)

            print("\nUnable to find a link. Go here, find the switcharoo, and paste the link \n"
                  "to the next one here. \n\n", last_url)
            url = input().strip()
            thread_id, comment_id = parse.thread_url_to_id(url)

        comment = reddit.comment(comment_id)

        date = pendulum.from_timestamp(comment.created_utc, tz="UTC")
        date = date.in_timezone("local")

        print("{} {} {}".format(comment.body, date, comment.author, comment.permalink))
        roo_count += 1

        last_url = url
        url = parse.parse_comment(comment.body)
        # If not url, search
        if not url:
            print("Roo linked incorrectly")
            url = parse.find_roo_comment(comment)
            print("Guessing", url)
            # print("y for yes, otherwise paste URL")
            # response = input()
            # if response.lower() != "y":
            #     url = response

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
        print("Roo Count:", roo_count)
        raise e
print("Roo Count:", roo_count)