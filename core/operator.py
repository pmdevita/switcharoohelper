import praw
import core.constants as consts
import core.strings


def message_private_sub(reddit: praw.Reddit, subreddit):
    reddit.subreddit(consts.subreddit).message(core.strings.ModMail.privated_sub_subject,
                                               core.strings.ModMail.privated_sub_body.format(subreddit=subreddit))


