from pprint import pprint
from datetime import datetime

import praw.exceptions

from core import parse
from core.issues import *

issues = GetIssues.get()


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
        # If meta, determine if it was incorrectly submitted as meta
        if not parse.is_meta_title(submission.title):
            if parse.only_reddit_url(submission.selftext):
                action.add_issue(submission_is_meta)
                action.act(submission)
        roo = last_switcharoo.add(submission.id, link_post=False, time=datetime.utcfromtimestamp(submission.created_utc))
        return

    # Ignore announcements
    if submission.distinguished:
        return

    # Verify it is a link to a reddit thread
    # If not, assume it's a faulty submission and delete.
    if submission.domain[-10:] != "reddit.com":
        action.add_issue(submission_not_reddit)
        action.act(submission)
        return

    # Verify that the linked post is not NSFW
    # If yes, delete the roo.
    linked_post_id = parse.thread_url_to_id(submission.url)[0]
    linked_post = reddit.submission(id=linked_post_id)
    if linked_post.over_18:
        action.add_issue(submission_is_NSFW)
        action.act(submission)
        return

    print("Roo:", submission.title)

    # It's a roo, add it to the list of all roos
    # Mark it as unfinished in processing in case the roo doesn't finish getting processed
    roo = last_switcharoo.add(submission.id, roo_issues=[issues.submission_processing], time=datetime.utcfromtimestamp(submission.created_utc))

    # Redo next three checks with regex

    regex = parse.REPatterns.reddit_strict_parse.findall(submission.url)
    url_params = parse.process_url_params(regex[0][-1])
    print(regex, url_params)
    context = int(url_params['context']) if "context" in url_params else 0
    last_switcharoo.update(roo, context=context)

    # Check if it has multiple ? in it (like "?st=JDHTGB67&sh=f66dbbbe?context=3)
    if submission.url.count("?") > 1:
        action.add_issue(submission_multiple_params)
        action.act(submission)
        last_switcharoo.update(roo, roo_issues=action.issues)
        return

    # Verify it contains ?context
    if "?context" not in submission.url:
        action.add_issue(submission_lacks_context)

    # Verify it doesn't contain a slash at the end (which ignores the URL params) (Issue #5)
    if submission.url.count("?"):
        if "/" in submission.url[submission.url.index("?"):]:
            action.add_issue(submission_link_final_slash)

    # Create object from comment (what the submission is linking to)
    thread_id, comment_id = parse.thread_url_to_id(submission.url)
    roo = last_switcharoo.update(roo, thread_id=thread_id, comment_id=comment_id)

    # If there was a comment in the link, make the comment object
    if comment_id:
        comment = reddit.comment(comment_id)
    else:   # If there was no comment in the link, take action
        action.add_issue(submission_linked_thread)
        action.act(submission)
        last_switcharoo.update(roo, roo_issues=action.issues)
        return

    # If comment was deleted, this will make an error. The try alleviates that
    try:
        comment.refresh()
    except (praw.exceptions.ClientException, praw.exceptions.PRAWException):
        action.add_issue(comment_deleted)
        action.act(submission)
        last_switcharoo.update(roo, roo_issues=action.issues)
        return

    # Deleted comments sometimes don't generate errors
    if comment.body == "[removed]":
        action.add_issue(comment_deleted)
        action.act(submission, last_switcharoo.last_good(offset=1))
        last_switcharoo.update(roo, roo_issues=action.issues)
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
        last_switcharoo.update(roo, roo_issues=action.issues)
        return

    # What comment and thread does this submission's switcharoo link to? It should be the last good one
    next_thread_id, next_comment_id = parse.thread_url_to_id(comment_link)

    # We'll need the last verified good switcharoo from here on
    last_good_submission = last_switcharoo.last_good(before_roo=roo, offset=1)

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
            # Was this linked correctly linked to another roo?
            linked_roo = last_switcharoo.search(next_thread_id, next_comment_id)
            if linked_roo:
                # User correctly linked, the roo was just bad
                action.add_issue(comment_linked_bad_roo)
            else:
                # I dunno what the user linked but it didn't link the last good or last posted
                action.add_issue(comment_linked_wrong)
    else:
        print("Didn't have a last submission to check against")

    action.act(submission, last_good_submission)

    last_switcharoo.update(roo, roo_issues=action.issues, remove_issues=[issues.submission_processing])
    # last_switcharoo.add_good(submission, thread_id, comment_id)

    return

def process_old(switcharoo):
    pass
