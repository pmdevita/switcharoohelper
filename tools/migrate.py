import praw
import praw.exceptions
import time
import traceback
import prawcore.exceptions

from core.credentials import get_credentials, CredentialsLoader
credentials = CredentialsLoader.get_credentials("../credentials.ini")['reddit']

from core.history import SwitcharooLog
from core import constants as consts
from core.arguments import check_up as argparser


reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

args = argparser.parse_args()

last_switcharoo = SwitcharooLog(reddit)
last_switcharoo.sync_issues()

print("SwitcharooHelper Migrate v{} Ctrl+C to stop".format(consts.version))

start = args.starting_roo
if not start:
    print("Give starting ID")
    start = input()
    try:
        start = int(start)
    except:
        start = None
else:
    try:
        start = int(start)
    except:
        if start == "last":
            start = None
        else:
            raise Exception("Unspecified starting roo, not 'last' or a number")
DB_LIMIT = 50
limit = None

try:
    # Mark all bad roos (or unmark bad roos)
    if start:
        start = last_switcharoo.get_roo(start)
    roos = last_switcharoo.get_roos(after_roo=start, limit=max(min(DB_LIMIT, limit), 0) if limit is not None else DB_LIMIT)
    if limit:
        limit -= DB_LIMIT

    while roos:

        for roo in roos:
            print(roo.id)
            if not roo.thread_id and not roo.comment_id:
                print("missing thread and comment ids")
                continue
            try:
                author = roo.comment.author if roo.comment else roo.submission.author
                subreddit = roo.comment.subreddit if roo.comment else reddit.submission(roo.thread_id).subreddit
            except praw.exceptions.ClientException:
                print("not able to get data")
                continue
            except prawcore.exceptions.Forbidden:
                print("probably privated")
                continue
            if author:
                last_switcharoo.update(roo, user=author.name)
            if subreddit:
                last_switcharoo.update(roo, subreddit=subreddit.display_name)

        if roos:
            roos = last_switcharoo.get_roos(after_roo=roos[-1],
                                            limit=max(min(DB_LIMIT, limit), 0) if limit is not None else DB_LIMIT)
            if limit:
                limit -= DB_LIMIT

    # time.sleep(consts.sleep_time)

except KeyboardInterrupt:
    print("\nExiting...")

except Exception as e:
    raise
