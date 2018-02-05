from pprint import pprint

import praw.exceptions

from core import parse
from core.issues import *


def process(reddit, submission, last_good_submission, last_submission, action):
    """
    Check the submission to make sure it is correct
    :param reddit: PRAW reddit instance
    :param submission: post to check
    :param last_good_submission: a dict of the last good submission in the chain's thread_id, comment_id, and submission object
    :param last_submission: url of the last switcharoo submission
    :param action: an action class to call for performing actions
    :return:
    """

    # Verify it is a link post (not a self post)
    if submission.is_self:
        return last_good_submission, last_submission

    # Verify it is a link to a reddit thread
    if submission.domain != "reddit.com":
        return last_good_submission, last_submission

    print("Roo:", submission.title)

    # Since this is confirmed to be a roo post, it will be the new last_submission next time
    new_last_submission = submission.url

    # Verify it contains ?context
    if "?context" not in submission.url:
        action.add_issue(submission_lacks_context)

    # Create object from comment (what the submission is linking to)
    thread_id, comment_id = parse.thread_url_to_id(submission.url)

    # If there was a comment in the link, make the comment object
    if comment_id:
        comment = reddit.comment(comment_id)
    else:   # If there was no comment in the link, take action
        action.add_issue(submission_linked_thread)
        action.act(submission, last_good_submission)
        return last_good_submission, new_last_submission

    # If comment was deleted, this will make an error. The try alleviates that
    try:
        comment.refresh()
    except praw.exceptions.ClientException:
        action.add_issue(comment_deleted)
        action.act(submission, last_good_submission)
        return last_good_submission, new_last_submission

    # Deleted comments sometimes don't generate errors
    if comment.author is None or comment.body == "[removed]":
        action.add_issue(comment_deleted)
        action.act(submission, last_good_submission)
        return last_good_submission, new_last_submission

    # Get link in comment
    comment_link = parse.parse_comment(comment.body)

    # If there is no link, report it
    if not comment_link:
        """
        At this point, we need to decide if the roo is salvageable. We need to search the comments
        to see if there is an actual roo here and request a correction to it's link (and make it 
        the new last_good_submission). Otherwise if there is no roo, skip it by returning the current 
        last_good_submission and yell at them for linking something that isn't a roo.
        """
        action.add_issue(comment_has_no_link)
        action.act(submission, last_good_submission)
        return last_good_submission, new_last_submission

    # What comment and thread does this submission's switcharoo link to? It should be the last good one
    next_thread_id, next_comment_id = parse.thread_url_to_id(comment_link)

    # check if there is a last good submission to verify against
    if last_good_submission:

        # Is this switcharoo comment linked to the last good switcharoo?
        if next_thread_id == last_good_submission["thread_id"] and \
                        next_comment_id == last_good_submission["comment_id"]:
            # Woohoo! Linked to correct comment. Now check for ?context
            if "?context" not in comment_link:
                action.add_issue(comment_lacks_context)
            else:
                print("  Linked correctly to next level in roo")
        else:
            # Was this linked correctly linked to the last thread and it wasn't good or
            # was this linked to something else?
            last_thread_id, last_commend_id = parse.thread_url_to_id(last_submission)
            if next_thread_id == last_thread_id and next_comment_id == last_commend_id:
                # User correctly linked, the roo was just bad
                action.add_issue(comment_linked_bad_roo)
            else:
                # I dunno what the user linked but it didn't link the last good or last posted
                action.add_issue(comment_linked_wrong)
    else:
        print("Didn't have a last submission to check against")

    action.act(submission, last_good_submission)

    return {"thread_id": thread_id, "comment_id": comment_id, "submission": submission,
            "submission_url": submission.url}, new_last_submission
