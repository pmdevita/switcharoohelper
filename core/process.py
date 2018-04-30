from pprint import pprint

import praw.exceptions

from core import parse
from core.issues import *


def process(reddit, submission, last_switcharoo, action):
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
        return

    # Verify it is a link to a reddit thread
    if submission.domain != "reddit.com":
        return

    print("Roo:", submission.title)

    # Check if it has multiple ? in it (like "?st=JDHTGB67&sh=f66dbbbe?context=3)
    if submission.url.count("?") > 1:
        action.add_issue(submission_multiple_params)
        action.act(submission)
        return

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
        action.act(submission)
        return

    # If comment was deleted, this will make an error. The try alleviates that
    try:
        comment.refresh()
    except (praw.exceptions.ClientException, praw.exceptions.PRAWException):
        action.add_issue(comment_deleted)
        action.act(submission)
        return

    # Deleted comments sometimes don't generate errors
    if comment.author is None or comment.body == "[removed]":
        action.add_issue(comment_deleted)
        action.act(submission, last_switcharoo.last_good())
        return

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
        action.act(submission)
        return

    # What comment and thread does this submission's switcharoo link to? It should be the last good one
    next_thread_id, next_comment_id = parse.thread_url_to_id(comment_link)

    # We'll need the last verified good switcharoo from here on
    last_good_submission = last_switcharoo.last_good()

    # check if there is a last good submission to verify against
    if last_good_submission:

        # Is this switcharoo comment linked to the last good switcharoo?
        if next_thread_id == last_good_submission.thread_id and \
                        next_comment_id == last_good_submission.comment_id:
            # Woohoo! Linked to correct comment. Now check for ?context
            if "?context" not in comment_link:
                action.add_issue(comment_lacks_context)
            else:
                print("  Linked correctly to next level in roo")
        else:
            # Was this linked correctly linked to the last thread and it wasn't good or
            # was this linked to something else?
            last_thread_id, last_comment_id = parse.thread_url_to_id(last_switcharoo.last_submitted())
            if next_thread_id == last_thread_id and next_comment_id == last_comment_id:
                # User correctly linked, the roo was just bad
                action.add_issue(comment_linked_bad_roo)
            else:
                # I dunno what the user linked but it didn't link the last good or last posted
                action.add_issue(comment_linked_wrong)
    else:
        print("Didn't have a last submission to check against")

    action.act(submission, last_good_submission)

    last_switcharoo.add_good(submission, thread_id, comment_id)

    return