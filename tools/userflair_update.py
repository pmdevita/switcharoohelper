# Bootstrap the main library into the path
import os
import sys
from pathlib import Path
tools_folder = Path(os.path.dirname(os.path.realpath(__file__)))
root = str(tools_folder.parent)
if root not in sys.path:
    sys.path.append(root)

from core.credentials import CredentialsLoader
credentials = CredentialsLoader.get_credentials(tools_folder / "../credentials.ini")['reddit']

import praw
import prawcore.exceptions
from core.history import SwitcharooLog
from core import constants as consts

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

switcharoo = reddit.subreddit("switcharoo")

last_switcharoo = SwitcharooLog(reddit)


def pad_zeros(number, zeros):
    string = str(number)
    return "".join(["0" for i in range(max(zeros - len(string), 0))]) + string


def remove_deleted_users(flairs):
    delete_list = []
    # Double check that the users exist before committing changes
    for i, flair in enumerate(flairs):
        try:
            redditor = reddit.redditor(flair['user'])
            status = redditor.is_suspended
        except prawcore.exceptions.NotFound:
            print(flair['user'], "no longer exists, omitting")
            delete_list.append(i)
        except AttributeError:
            pass
    for i in reversed(delete_list):
        flairs.pop(i)
    return flairs


print("SwitcharooHelper Flair Sync v{} Ctrl+C to stop".format(consts.version))


current_good = last_switcharoo.stats.num_of_good_roos(all_users=True)
current_good = {i[0]: [i[1], 0] for i in current_good}
user_flair = last_switcharoo.stats.all_user_flair()
for flair in user_flair:
    if flair.user in current_good:
        current_flair = current_good[flair.user]
        current_good[flair.user] = [current_flair[0] + flair.roos, current_flair[1] + flair.fixes]
    else:
        current_good[flair.user] = [flair.roos, flair.fixes]

if None in current_good:
    del current_good[None]

final_flairs = {key: f"badge-{pad_zeros(current_good[key][0], 2)}" for key in current_good}
delete_list = []

# Omit anyone with a troublemaker flair or already has the flair
for flair in switcharoo.flair():
    if flair['flair_css_class']:
        if flair['flair_css_class'][:6] != "badge-":
            # This person has a special flair, omit them if they are in the list
            if flair['user'].name in current_good:
                print("omitting", flair['user'].name)
                del current_good[flair['user'].name]
        elif flair['user'].name not in current_good:
            # This person has a number badge but they aren't represented in the data, they should be deleted
            delete_list.append(flair['user'].name)
        else:
            # This person has a badge in reddit and our data, double check it needs to be updated
            if final_flairs[flair['user'].name] == flair['flair_css_class']:
                # It's the same, remove it
                # print("omitting", flair['user'].name, "because it's unchanged")
                del current_good[flair['user'].name]

# Remake flairs from changed data
final_flairs = [{"user": key, "flair_css_class": f"badge-{pad_zeros(current_good[key][0], 2)}"} for key in current_good]
final_flairs += [{"user": user, "flair_css_class": "", "flair_text": ""} for user in delete_list]

print("Updating flairs...")

switcharoo.flair.update(remove_deleted_users(final_flairs))

print("Done!")
