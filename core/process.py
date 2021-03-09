from pprint import pprint
from datetime import datetime

import praw.exceptions

from core import parse
from core.issues import GetIssues, IssueTracker


def process(reddit, submission, last_switcharoo, action):
    # First, add this submission to the database
    tracker = IssueTracker()
    tracker.submission_processing = True
    roo = last_switcharoo.add(submission.id, link_post=not submission.is_self,
                              roo_issues=tracker,
                              time=datetime.utcfromtimestamp(submission.created_utc))

    tracker = check_errors(reddit, submission, last_switcharoo, roo, init_db=True)
    if action:
        action.act(tracker, submission, last_switcharoo.last_good(before_roo=roo))
        last_switcharoo.update(roo, roo_issues=tracker, reset_issues=True)
    else:
        last_switcharoo.update(roo, roo_issues=tracker, reset_issues=True)

    last_switcharoo.get_issues(roo)


def check_errors(reddit, submission, last_switcharoo, roo, init_db=False):
    """
    Check the submission to make sure it is correct
    :param init_db:
    :param last_switcharoo:
    :param reddit: PRAW reddit instance
    :param submission: post to check
    :param last_good_submission: a dict of the last good submission in the chain's thread_id, comment_id, and submission object
    :param last_submission: url of the last switcharoo submission
    :param action: an action class to call for performing actions
    :return:
    """
    tracker = IssueTracker()

    # Ignore announcements
    if submission.distinguished:
        return None

    # Verify it is a link post (not a self post)
    if submission.is_self:
        # If meta, determine if it was incorrectly submitted as meta
        if not parse.is_meta_title(submission.title):
            if parse.only_reddit_url(submission.selftext):
                tracker.submission_is_meta = True
                return tracker
        return None

    # Verify it is a link to a reddit thread
    # If not, assume it's a faulty submission and delete.
    if submission.domain[-10:] != "reddit.com":
        tracker.submission_not_reddit = True
        return tracker

    print("Roo:", submission.title)

    # It's a roo, add it to the list of all roos
    # Mark it as unfinished in processing in case the roo doesn't finish getting processed

    # Redo next three checks with regex

    submission_url = parse.RedditURL(submission.url)

    # Some URLs may not pass the stricter check, probably because they did something wrong
    if not submission_url.is_reddit_url:
        tracker.submission_bad_url = True
        return tracker

    # Verify it contains context param
    if "context" not in submission_url.params:
        tracker.submission_lacks_context = True
        return tracker

    # Try to get the context value
    try:
        context = int(submission_url.params['context'])
    except (KeyError, ValueError):  # context is not in URL params or not a number
        tracker.submission_lacks_context = True
        return tracker

    # If we are in the middle of adding this to the db, add the context amount
    if init_db:
        last_switcharoo.update(roo, context=context)

    # Check if it has multiple ? in it (like "?st=JDHTGB67&sh=f66dbbbe?context=3)
    if submission.url.count("?") > 1:
        tracker.submission_multiple_params = True
        return tracker

    # Verify it doesn't contain a slash at the end (which ignores the URL params) (Issue #5)
    if submission.url.count("?"):
        if "/" in submission.url[submission.url.index("?"):]:
            tracker.submission_link_final_slash = True

    # If there was a comment in the link, make the comment object
    if submission_url.comment_id:
        comment = reddit.comment(submission_url.comment_id)
    else:  # If there was no comment in the link, take action
        tracker.submission_linked_thread = True
        return tracker

    # If we are in the middle of adding this to the db, add the thread and comment ids now
    if init_db:
        roo = last_switcharoo.update(roo, thread_id=submission_url.thread_id, comment_id=submission_url.comment_id)

    # If comment was deleted, this will make an error. The try alleviates that
    try:
        comment.refresh()
    except (praw.exceptions.ClientException, praw.exceptions.PRAWException):
        tracker.comment_deleted = True
        return tracker

    # Deleted comments sometimes don't generate errors
    if comment.body == "[removed]":
        tracker.comment_deleted = True
        return tracker

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
        tracker.comment_has_no_link = True
        return tracker

    # What comment and thread does this submission's switcharoo link to? It should be the last good one
    comment_url = parse.RedditURL(comment_link)

    # We'll need the last verified good switcharoo from here on
    last_good_submission = last_switcharoo.last_good(before_roo=roo)

    # check if there is a last good submission to verify against
    if last_good_submission:

        # Is this switcharoo comment linked to the last good switcharoo?
        if comment_url.thread_id == last_good_submission.thread_id and \
                comment_url.comment_id == last_good_submission.comment_id:
            # Hooray! Linked to correct comment. Now check for context param

            # Verify it contains context param
            if "context" not in comment_url.params:
                tracker.comment_lacks_context = True

            # Try to get the context value
            try:
                context = int(comment_url.params['context'])
            except (KeyError, ValueError):  # context is not a number
                tracker.comment_lacks_context = True  # Should be a different error

        else:
            # Was this linked correctly linked to another roo?
            linked_roo = last_switcharoo.search(comment_url.thread_id, comment_url.comment_id)
            if linked_roo:
                # User correctly linked, the roo was just bad
                tracker.comment_linked_bad_roo = True
            else:
                # I dunno what the user linked but it didn't link the last good or last posted
                tracker.comment_linked_wrong = True
    else:
        print("Didn't have a last submission to check against")

    return tracker


def process_old(switcharoo):
    pass
