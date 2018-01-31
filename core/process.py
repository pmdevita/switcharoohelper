import praw.exceptions

from core import parse


def process(reddit, submission, last_submission, action):
    """
    Check the submission to make sure it is correct
    :param reddit: PRAW reddit instance
    :param submission: post to check
    :param last_submission: a dict of the last submission in the chain's thread_id, comment_id, and submission object
    :param action: an action class to call for performing actions
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
        action.submission_lacks_context(submission)

    # Create object from comment (what the submission is linking to)
    thread_id, comment_id = parse.thread_url_to_id(submission.url)
    # print(thread_id, comment_id)

    # If there was a comment in the link, make the comment object
    if comment_id:
        comment = reddit.comment(comment_id)
    else:
        action.submission_linked_thread(submission)
        return last_submission

    # If comment was deleted, this will make an error. The try alleviates that
    try:
        comment.refresh()
    except praw.exceptions.ClientException:
        action.comment_deleted(submission)
        return last_submission

    # Deleted comments sometimes don't generate errors
    if comment.author is None or comment.body == "[removed]":
        action.comment_deleted(submission)
        return last_submission

    # Get link in comment
    comment_link = parse.parse_comment(comment.body)

    # If there is no link, report it
    if not comment_link:
        """
        At this point, we need to decide if the roo is salvageable. We need to search the comments
        to see if there is an actual roo here and request a correction to it's link (and make it 
        the new last_submission). Otherwise if there is no roo, skip it by returning the current 
        last_submission and yell at them for linking something that isn't a roo.
        """
        action.comment_has_no_link(submission)
        return last_submission

    # Get the level below thread and comment id
    next_thread_id, next_comment_id = parse.thread_url_to_id(comment_link)

    # check if there is a last submission to verify against
    if last_submission:
        # If we just reloaded data from last time and need to remake the submission object
        if "submission" not in last_submission:
            last_submission["submission"] = reddit.submission(url=last_submission["submission_url"])

        # Is this comment linked to the last comment?
        if next_thread_id == last_submission["thread_id"] and next_comment_id == last_submission["comment_id"]:
            # Woohoo! Linked to correct comment. Now check for ?context
            if "?context" not in comment_link:
                action.comment_lacks_context(submission)
            else:
                print("Linked correctly to next level in roo")
        else:
            action.comment_linked_wrong(submission)
    else:
        print("Didn't have a last submission to check against")

    return {"thread_id": thread_id, "comment_id": comment_id, "submission": submission,
            "submission_url": submission.url}
