import praw
from switcharoo import core as consts


def message_private_sub(reddit: praw.Reddit, subreddit):
    reddit.subreddit(consts.subreddit).message(switcharoo.core.strings.ModMail.privated_sub_subject,
                                               switcharoo.core.strings.ModMail.privated_sub_body.format(subreddit=subreddit))


