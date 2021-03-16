import psaw
import praw.exceptions
import time
import pendulum
import webbrowser
from datetime import datetime, timedelta

import prawcore.exceptions

from core.credentials import CredentialsLoader
from core import constants as consts
from core import parse
from core.history import SwitcharooLog
from core.arguments import tracer as argparser
from core.pushshift import get_comment_from_psaw, get_original_comment_from_psaw

credentials = CredentialsLoader.get_credentials()['reddit']

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

pushshift = psaw.PushshiftAPI(reddit)

switcharoo = reddit.subreddit("switcharoo")

log = SwitcharooLog(reddit)

args = argparser.parse_args()


def get_newest_id(subreddit, index=0):
    """Retrieves the newest post's id. Used for starting the last switcharoo history trackers"""
    return [i for i in subreddit.new(params={"limit": "1"})][index].url


if args.discover:
    starting_roo = log.oldest_good()
    print("Starting with", starting_roo)
    starting_roo.print()
    url = f"https://reddit.com{starting_roo.comment.permalink}"
else:
    print("Paste the URL of the switcharoo comment you'd like to start at\nOr leave blank to start at the newest")
    url = input().strip()

    if not url:
        url = get_newest_id(switcharoo, 0)

roo_count = 0
last_url = None
url = parse.RedditURL(url)
start_url = url

print("SwitcharooHelper Tracer v{} Ctrl+C to stop".format(consts.version))


def unable_to_find_link(url: parse.RedditURL, last_url: parse.RedditURL):
    print("Unable to find a link in this roo.")
    print(last_url.to_link(reddit))
    print(url.to_link(reddit))

    # roo = log.search(url.thread_id, url.comment_id)
    # if roo:
    #     after = log.last_good(roo)
    #     before = log.next_good(roo)
    #     print("-".join([str(i) for i in [before, roo, after]]))
    #     print("I think you should link", "https://reddit.com" + before.submission.permalink, "to",
    #           "https://reddit.com" + after.submission.permalink)
    print("\nUnable to find a link. Go here, find the switcharoo, and paste the link \n"
          "to the next one here. \n\n", last_url)
    url = input().strip()
    return parse.RedditURL(url)


def add_comment(url: parse.RedditURL, start_url: parse.RedditURL = None):
    # Double check it's not already there
    q = log.search(comment_id=url.comment_id)
    if q:
        if q == start_url:
            return
        raise Exception(f"{url} already exists in DB, something is wrong")
    # Double check this is the oldest date
    comment_time = datetime.utcfromtimestamp(comment.created_utc)
    q = log.search(after_time=comment_time, oldest=True)
    if q:
        print("Adjusting roo time")
        comment_time = q.time - timedelta(seconds=1)
    try:
        context = int(url.params.get("context", 0))
    except ValueError:
        print(f"Got {url.params['context']} for url {url}, what should it be?")
        context = int(input())

    log.add_comment(url.thread_id, url.comment_id, context, comment_time)





while True:
    try:
        if url.comment_id:
            if isinstance(url, str):
                url = parse.RedditURL(url)
                if not url.comment_id:
                    url = unable_to_find_link(url, last_url)
        else:
            url = unable_to_find_link(url, last_url)

        comment = reddit.comment(url.comment_id)

        try:
            date = pendulum.from_timestamp(comment.created_utc, tz="UTC")
        except praw.exceptions.ClientException:
            url = unable_to_find_link(url, last_url)
            comment = reddit.comment(url.comment_id)
        date = date.in_timezone("local")

        print("{} {} {}".format(comment.body, date, comment.author, comment.permalink))
        roo_count += 1

        last_url = url
        if comment.body == "[deleted]" or comment.body == "[removed]":
            print("Comment was deleted")
            url = parse.search_pushshift(comment, last_url)
        else:
            url = parse.parse_comment(comment.body)

        # If not url, search
        if not url.comment_id:
            print("Roo linked incorrectly, searching thread for link")
            new_last_url = parse.find_roo_comment(comment)
            if new_last_url and last_url:
                try:
                    new_last_url.params['context'] = str(int(new_last_url.params.get('context', 0)) +
                                                         int(last_url.params.get('context', 0)))
                except ValueError:
                    print(f"Got {new_last_url.params['context']} and {last_url.params['context']}, what should it be?")
                    new_last_url.params['context'] = int(input())
            if new_last_url:
                if args.discover:
                    print("Should", last_url.to_link(reddit), "actually be", new_last_url.to_link(reddit), "?")
                    print("(y/n)")
                    webbrowser.open(last_url.to_link(reddit))
                    webbrowser.open(new_last_url.to_link(reddit))
                    option = input()
                    if option == "y":
                        last_url = new_last_url
                else:
                    last_url = new_last_url
                comment = reddit.comment(last_url.comment_id)
                if comment.body == "[deleted]" or comment.body == "[removed]":
                    print("Comment was deleted")
                    url = parse.search_pushshift(comment, last_url)
                else:
                    url = parse.parse_comment(comment.body)
            else:
                url = parse.search_pushshift(comment, last_url)

        if args.discover:
            add_comment(last_url, start_url=start_url)
            if start_url:
                start_url = None


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