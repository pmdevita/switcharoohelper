from pprint import pprint
import praw.exceptions
from datetime import datetime, timedelta
from core import parse
from core.issues import IssueTracker
from core.strings import NewIssueDeleteStrings
from core.reddit import ReplyObject
from core.constants import ONLY_BAD, ONLY_IGNORED, ALL_ROOS
from core.history import SwitcharooLog


def process(reddit, submission, last_switcharoo, action):
    # First, add this submission to the database
    tracker = IssueTracker()
    tracker.submission_processing = True
    roo = last_switcharoo.add(submission.id, link_post=not submission.is_self,
                              roo_issues=tracker,
                              time=datetime.utcfromtimestamp(submission.created_utc))
    # Create an issue tracker made from it's errors
    tracker = check_errors(reddit, last_switcharoo, roo, init_db=True, submission=submission)

    # If it has issues, perform an action to correct it
    if tracker.has_issues():
        action.process(tracker, ReplyObject(submission), last_switcharoo.last_good(before_roo=roo, offset=0))
        last_switcharoo.update(roo, roo_issues=tracker, reset_issues=True)
        if not tracker.has_bad_issues():
            last_switcharoo.update_request(roo, requests=1)
    else:
        last_switcharoo.update(roo, reset_issues=True)


def reprocess(reddit, roo, last_switcharoo: SwitcharooLog, action, award=False, stage=ONLY_BAD):
    # When scanning the chain with this, do this in two passes. First to re-update the status of each roo submission
    # and secondly to then give instructions to fix
    if stage == ALL_ROOS:
        roo.print()
    old_tracker = last_switcharoo.get_issues(roo)

    if roo.submission:
        new_tracker = check_errors(reddit, last_switcharoo, roo, submission=roo.submission)
    else:
        new_tracker = check_errors(reddit, last_switcharoo, roo, comment=roo.comment)

    request = last_switcharoo.check_request(roo)

    # Requests made within the last month have 3 days to respond, requests made a week out have 7
    grace_period = 3 if roo.time > datetime.now() - timedelta(days=30) else 7

    # If this roo has bad issues or it was marked for noncompliance,
    # it should be updated immediately to be removed from the chain
    if new_tracker.has_bad_issues() or old_tracker.user_noncompliance:
        if old_tracker.has_bad_issues():
            roo.print()
            print("Roo was already bad")
        else:
            roo.print()
            print("Roo has gone bad")
            action.process(new_tracker, ReplyObject.from_roo(roo), last_switcharoo.last_good(roo, offset=0), mute=True)
            new_tracker.submission_deleted = True
        last_switcharoo.update(roo, roo_issues=new_tracker, reset_issues=True)
        return
    else:
        # If this roo was miraculously cured of bad issues
        if old_tracker.has_bad_issues():
            # Then reinstate it.
            print(f"Roo {roo.id} was miraculously cured of bad issues")
            last_switcharoo.update(roo, roo_issues=new_tracker, reset_issues=True)
            return

    if new_tracker.has_issues():
        # If this is after they were supposed to fix something, gently ask them again
        # If this was long after they were supposed to fix something and nothing happened, delete the post
        added, removed = old_tracker.diff(new_tracker)
        if parse.has_responded_to_post(roo.submission) and not request:
            print("Have previously responded, adding to DB")
            request = last_switcharoo.update_request(roo, requests=1)
        # Has the issue set changed since last time
        if len(added) == 0 and len(removed) == 0:
            print("Issues unchanged")
            if not request:
                request = last_switcharoo.update_request(roo, requests=0)
            # If we are within cooldown, remind them and increase remind count
            action.act_again(roo, new_tracker, request, grace_period, stage, last_switcharoo.last_good(roo, offset=0))
        elif stage == ALL_ROOS:
            print("Roo issues have changed")
            print(added, removed)
            # New situation, reset the request if it's there
            if request:
                request = last_switcharoo.reset_request(request=request)
            request = last_switcharoo.update_request(roo, requests=0)
            # Something has changed. Did we previously have issues too?
            # If we are within cooldown, remind them and increase remind count
            if old_tracker.has_issues():
                # Either they fixed and a new issue came up or it's a new issue
                action.act_again(roo, new_tracker, request, grace_period, stage,
                                 last_switcharoo.last_good(roo, offset=0))
            else:
                # This was working before, the chain might have just changed around them.
                action.act_again(roo, new_tracker, request, grace_period, stage,
                                 last_switcharoo.last_good(roo, offset=0))
    elif stage == ALL_ROOS:
        # If this is after they fixed something, say thank you
        if old_tracker.has_issues():
            action.thank_you(roo, award)
        else:
            # If the old one didn't have issues, then nothing has changed, it's fine
            print("Correct")
        if request:
            last_switcharoo.reset_request(request=request)

    # After action has been taken on the roo, update the database with the new issue status
    if stage == ALL_ROOS:
        last_switcharoo.update(roo, roo_issues=new_tracker, reset_issues=True)


def add_comment(reddit, last_switcharoo, link):
    url = parse.RedditURL(link)
    comment = reddit.comment(url.comment_id)
    last_switcharoo.add_comment(url.thread_id, url.comment_id, url.params['context'],
                                datetime.utcfromtimestamp(comment.created_utc))


def check_errors(reddit, last_switcharoo: SwitcharooLog, roo, init_db=False, submission=None, comment=None):
    """
    Check the submission to make sure it is correct
    :param comment:
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

    if submission:
        # Ignore announcements
        if submission.distinguished:
            return tracker

        # Verify it is a link post (not a self post)
        if submission.is_self:
            # If meta, determine if it was incorrectly submitted as meta
            if not parse.is_meta_title(submission.title):
                if parse.only_reddit_url(submission.selftext):
                    tracker.submission_is_meta = True
                    return tracker
            return tracker

        # Verify it is a link to a reddit thread
        # If not, assume it's a faulty submission and delete.
        if submission.domain[-10:] != "reddit.com":
            tracker.submission_not_reddit = True
            return tracker

        if init_db:
            print(f"Roo: {submission.title} by {submission.author}")

        # It's a roo, add it to the list of all roos

        submission_url = parse.RedditURL(submission.url)

        if submission.removed_by_category is not None or submission.banned_at_utc is not None \
                or submission.selftext == "[deleted]":
            tracker.submission_deleted = True

            # Temporary check
            # Forgive automoderator removals if they mean not sending a fix message
            if submission.banned_by == "AutoModerator":
                previous_roo = last_switcharoo.next_good(roo)
                if previous_roo:
                    previous_link = parse.parse_comment(previous_roo.comment.body)
                    # previous_link = parse.RedditURL(previous_link)
                    submission_url = parse.RedditURL(submission.url)
                    if previous_link.thread_id == submission_url.thread_id \
                        and previous_link.comment_id == submission_url.comment_id:
                        print(f"{roo.id} Previous comment was linked to this one, which was removed by automod")
                        tracker.submission_deleted = False
                    else:
                        print(f"{roo.id} Banned by automoderator but previous comment isn't linked to it so leaving as is")


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

    else:
        roo = last_switcharoo.update(roo, comment_id=comment.id)

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

    # If the comment's author still exist, don't worry about a deleted submission
    # NEVERMIND NEVER DO THIS
    if submission and tracker.submission_deleted:
        if comment.author is not None and submission.banned_at_utc is not None:
            print("THIS ONE RIGHT HERE")
            print(f"{roo.id} https://reddit.com{submission.permalink} {submission.author}")
            print(f"https://reddit.com{comment.permalink}")
            print(last_switcharoo.search(submission_url.thread_id, multiple=True))
            print(parse.RedditURL(f"https://reddit.com{submission.permalink}").thread_id)
            print(submission_url.thread_id)
            # input()

        if comment.author is not None and submission.banned_at_utc is None:
            print("Maybe keep this one???")
            print(f"{roo.id} https://reddit.com{submission.permalink} {submission.author}")
            print(f"https://reddit.com{comment.permalink}")
            # input()

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
    # comment_url = parse.RedditURL(comment_link)
    comment_url = comment_link

    # We'll need the last verified good switcharoo from here on
    last_good_submission = last_switcharoo.last_good(before_roo=roo, offset=0)

    # check if there is a last good submission to verify against
    if last_good_submission:

        # Is this switcharoo comment linked to the last good switcharoo?
        if comment_url.thread_id == last_good_submission.thread_id and \
                comment_url.comment_id == last_good_submission.comment_id:
            # Hooray! Linked to correct comment. Now check for context param

            # Verify it contains context param
            if "context" not in comment_url.params:
                thing = submission if submission else comment
                if datetime(year=2021, month=3, day=10) < datetime.fromtimestamp(thing.created_utc):
                    tracker.comment_lacks_context = True
                else:
                    print("Ignoring bad context cause it's old")

            # Try to get the context value
            try:
                context = int(comment_url.params['context'])
            except (KeyError, ValueError):  # context is not a number
                thing = submission if submission else comment
                if datetime(year=2021, month=3, day=10) < datetime.fromtimestamp(thing.created_utc):
                    tracker.comment_lacks_context = True  # Should be a different error
                else:
                    print("Ignoring bad context cause it's old")

            if tracker.submission_deleted:
                if datetime(year=2021, month=3, day=10) > datetime.fromtimestamp(submission.created_utc):
                    # Check if previous comment is linked to it
                    previous_roo = last_switcharoo.next_good(roo)
                    if previous_roo:
                        previous_link = parse.parse_comment(previous_roo.comment.body)
                        # previous_link = parse.RedditURL(previous_link)
                        submission_url = parse.RedditURL(submission.url)
                        if previous_link.thread_id == submission_url.thread_id \
                                and previous_link.comment_id == submission_url.comment_id:
                            print(f"{roo.id} Previous comment links to it and it's not causing trouble, keeping")
                            tracker.submission_deleted = False
                        else:
                            print(f"{roo.id} Could be alright but previous roo is not linked to it so keeping deleted")

        else:
            # Was this linked correctly linked to another roo?
            linked_roo = last_switcharoo.search(comment_url.thread_id, comment_url.comment_id)
            if linked_roo:
                # User correctly linked, the roo was just bad
                # If this is a problematic old roo, don't touch it unless we have to
                if datetime(year=2021, month=3, day=10) > datetime.fromtimestamp(submission.created_utc):
                    linked_issues = last_switcharoo.get_issues(linked_roo)
                    if linked_issues.comment_deleted or linked_issues.comment_has_no_link \
                            or linked_issues.user_noncompliance:
                        tracker.comment_linked_bad_roo = True
                    else:
                        print(f"{roo.id} is linked to the wrong roo but it's OK so I'm ignoring it")
                        if tracker.submission_deleted:
                            # Check if previous comment is linked to it
                            previous_roo = last_switcharoo.next_good(roo)
                            if previous_roo:
                                previous_link = parse.parse_comment(previous_roo.comment.body)
                                # previous_link = parse.RedditURL(previous_link)
                                submission_url = parse.RedditURL(submission.url)
                                if previous_link.thread_id == submission_url.thread_id \
                                        and previous_link.comment_id == submission_url.comment_id:
                                    print("Previous comment was linked to this one so I'm leaving that intact as well")
                                    tracker.submission_deleted = False
                                else:
                                    print("However, it was skipped over in the chain so I'm keeping it removed")
                        else:
                            print("However, the previous roo isn't linked to it so it'll stay deleted")
                else:
                    tracker.comment_linked_bad_roo = True
            else:
                # I dunno what the user linked but it didn't link the last good or last posted
                tracker.comment_linked_wrong = True
    else:
        print("Didn't have a last submission to check against")

    return tracker

