import praw
import prawcore.exceptions
from switcharoo.core.history import SwitcharooLog
from switcharoo.config.credentials import CredentialsLoader
from switcharoo.config import constants as consts

credentials = CredentialsLoader.get_credentials()['reddit']

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


def check_user_exists(username):
    try:
        redditor = reddit.redditor(username)
        status = redditor.is_suspended
    except prawcore.exceptions.NotFound:
        print(username, "no longer exists, omitting")
        return False
    except AttributeError:
        return False
    except ValueError:
        # There are some users with blank usernames in the database
        # due to the 2022 outage. They deleted their comments before we could
        # record their usernames
        return False
    return True


def remove_deleted_users(flairs):
    return [flair for flair in flairs if check_user_exists(flair['user'])]


def main():
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

    # Compare generated flairs against Reddit data to reduce updates and filter out
    # users who shouldn't be updated
    # Omit anyone with a troublemaker flair or already has the flair
    for flair in switcharoo.flair():
        if flair['flair_css_class']:
            if flair['flair_css_class'][:6] != "badge-":
                # This person has a special flair, omit them if they are in the list
                if flair['user'].name in current_good:
                    print("omitting", flair['user'].name)
                    del current_good[flair['user'].name]
            elif flair['user'].name not in current_good:
                # This person has a number badge, but they aren't represented in the data, they should be deleted
                delete_list.append(flair['user'].name)
            else:
                # This person has a badge in reddit and our data, double check it needs to be updated
                if final_flairs[flair['user'].name] == flair['flair_css_class']:
                    # It's the same, remove it
                    # print("omitting", flair['user'].name, "because it's unchanged")
                    del current_good[flair['user'].name]

    # Remake flairs from changed data
    final_flairs = [{"user": key, "flair_css_class": f"badge-{pad_zeros(current_good[key][0], 2)}"} for key in
                    current_good]
    final_flairs += [{"user": user, "flair_css_class": "", "flair_text": ""} for user in delete_list]

    print("Updating flairs...")

    switcharoo.flair.update(remove_deleted_users(final_flairs))

    print("Done!")


if __name__ == '__main__':
    main()
