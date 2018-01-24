import praw.exceptions

from pprint import pprint

from core import parse


def process(reddit, submission, last_submission):
    """
    Check the submission to make sure it is correct
    :param reddit: PRAW reddit instance
    :param submission: post to check
    :param last_submission: a dict of the last submission in the chain's thread_id, comment_id, and submission object
    :return:
    """
    # pprint(vars(submission))

    # Verify it is a link post (not a self post)
    if submission.is_self:
        return last_submission

    # Verify it is a link to a reddit thread
    if submission.domain != "reddit.com":
        return last_submission

    print("Roo:", submission.title)

    # Verify it contains ?context
    if "?context" not in submission.url:
        print("https://www.reddit.com{} submission link does not have ?context".format(submission.permalink))

    # Create object from comment (what the submission is linking to)
    thread_id, comment_id = parse.thread_url_to_id(submission.url)
    # print(thread_id, comment_id)

    # If there was a comment in the link, make the comment object
    if comment_id:
        comment = reddit.comment(comment_id)
    else:
        print("https://www.reddit.com{} linked to a thread, not a comment".format(submission.permalink))
        return last_submission

    # If comment was deleted, this will make an error. The try alleviates that
    try:
        comment.refresh()
    except praw.exceptions.ClientException:
        print("https://www.reddit.com{} comment got deleted. Post should be removed.".format(submission.permalink))
        return last_submission

    # Get link in comment
    comment_link = parse.parse_comment(comment.body)

    # If there is no link, report it
    if not comment_link:
        print("https://www.reddit.com{} has no link in the comment".format(submission.permalink))
        return last_submission

    # Get the level below thread and comment id
    next_thread_id, next_comment_id = parse.thread_url_to_id(comment_link)

    # and check if it matches the last submission
    if last_submission:
        # If we just reloaded data from last time and need to remake the submission object
        if "submission" not in last_submission:
            last_submission["submission"] = reddit.submission(url=last_submission["submission_url"])
        # Is this comment linked to the last comment?
        if next_thread_id == last_submission["thread_id"] and next_comment_id == last_submission["comment_id"]:
            # Woohoo! Linked to correct comment. Now check for ?context
            if "?context" not in comment_link:
                print("https://www.reddit.com{} comment is correct link but did not have ?context in it".format(
                    submission.permalink))
            else:
                print("Linked correctly to next level in roo")
        else:
            print("https://www.reddit.com{} comment is not linked to the next level".format(
                submission.permalink))
    else:
        print("Didn't have a last submission to check against")

    return {"thread_id":thread_id, "comment_id":comment_id, "submission":submission, "submission_url":submission.url}
