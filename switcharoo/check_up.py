import datetime

import praw
import time
import traceback
import prawcore.exceptions

from switcharoo.config.credentials import CredentialsLoader
from switcharoo.core.process import reprocess, double_check_link
from switcharoo.core.history import SwitcharooLog
from switcharoo.config import constants as consts
from switcharoo.core.action import ModAction
from switcharoo.config.arguments import check_up as parser

credentials = CredentialsLoader.get_credentials()['reddit']

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

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


def get_newest_id(subreddit, index=0):
    """Retrieves the newest post's id. Used for starting the last switcharoo history trackers"""
    return [i for i in subreddit.new(params={"limit": "1"})][index].id


def check_up():
    args = parser.parse_args()
    print("SwitcharooHelper Check-up v{} using {} Ctrl+C to stop".format(consts.version, action.__class__.__name__))

    start = args.starting_roo
    if not start:
        print("Give starting ID")
        start = input()
        try:
            start = int(start)
        except ValueError:
            start = None
    else:
        try:
            start = int(start)
        except ValueError:
            if start == "last":
                start = None
            else:
                raise Exception("Unspecified starting roo, not 'last' or a number")

    DB_LIMIT = 50
    limit = args.limit
    if not limit:
        limit = None
    else:
        limit = int(limit)

    date_limit = None
    if args.date_limit:
        try:
            date_limit = datetime.datetime.fromisoformat(args.date_limit)
        except Exception as e:
            print("Unknown date string for date limit")
            raise e

    try:
        # Mark all bad roos (or unmark bad roos)
        if start:
            start = last_switcharoo.get_roo(start)
        roos = last_switcharoo.get_roos(after_roo=start,
                                        limit=max(min(DB_LIMIT, limit), 0) if limit is not None else DB_LIMIT,
                                        meta=args.include_meta,
                                        date_limit=date_limit)
        if limit:
            limit -= DB_LIMIT

        while roos:

            if args.double_check_link:
                print("\nDouble checking links\n")
                for roo in roos[:-2]:
                    double_check_link(reddit, last_switcharoo, roo)

            if not args.no_delete_check:
                print("\nChecking for deleted/bad roos\n")
                for roo in roos:
                    reprocess(reddit, roo, last_switcharoo, action, stage=consts.ONLY_BAD, mute=args.unmute_delete)

            # Now remove ignored posts
            # for roo in roos:
            #     reprocess(reddit, roo, last_switcharoo, action, consts.ONLY_IGNORED)

            # Everything should be updated, perform full actions
            if not args.no_relink:
                print("\nSending fix requests\n")
                for roo in roos[:-2]:
                    reprocess(reddit, roo, last_switcharoo, action, stage=consts.ALL_ROOS)

            if roos:
                roos = last_switcharoo.get_roos(after_roo=roos[-4 if len(roos) > 3 else 0],
                                                limit=max(min(DB_LIMIT, limit), 0) if limit is not None else DB_LIMIT,
                                                meta=args.include_meta,
                                                date_limit=date_limit)
                if limit:
                    limit -= DB_LIMIT

        # time.sleep(consts.sleep_time)

    except prawcore.exceptions.RequestException:  # Unable to connect to Reddit
        print("Unable to connect to Reddit, is the internet down?")
        time.sleep(consts.sleep_time * 2)

    except prawcore.exceptions.ResponseException as e:
        print("weird other exceptions?", e)
        time.sleep(consts.sleep_time * 2)

    except KeyboardInterrupt:
        print("\nExiting...")

    except Exception as e:
        if mode == "production":
            reddit.redditor(operator).message("SH Error!", "Help I crashed!\n\n    {}".format(
                str(traceback.format_exc()).replace('\n', '\n    ')))
        raise


if __name__ == '__main__':
    check_up()

