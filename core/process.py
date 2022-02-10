from pprint import pprint
import praw.exceptions
import prawcore.exceptions
from datetime import datetime, timedelta
from core import parse
from core.issues import IssueTracker
from core.strings import NewIssueDeleteStrings
from core.reddit import ReplyObject
from core.constants import ONLY_BAD, ONLY_IGNORED, ALL_ROOS
from core.history import SwitcharooLog, Switcharoo
from core.credentials import CredentialsLoader
from core.action import decide_subreddit_privated, increment_user_fixes
import core.operator

creds = CredentialsLoader.get_credentials()['general']
DRY_RUN = creds['dry_run'].lower() != "false"


def process(reddit, submission, last_switcharoo: SwitcharooLog, action):
    # First, add this submission to the database
    # Add with submission processing issue to prevent rescans from interfering during add
    tracker = IssueTracker()
    tracker.submission_processing = True
    roo = last_switcharoo.add(submission.id, link_post=not submission.is_self, user=submission.author.name,
                              roo_issues=tracker, time=datetime.utcfromtimestamp(submission.created_utc))
    # Create an issue tracker made from its errors
    tracker = check_errors(reddit, last_switcharoo, roo, init_db=True, submission=submission)

    # If it has issues, perform an action to correct it
    if tracker.has_issues():
        last_good = last_switcharoo.last_good(before_roo=roo, offset=0)
        action.process(tracker, ReplyObject(submission), last_good)
        last_switcharoo.update(roo, roo_issues=tracker, reset_issues=True)
        # If this roo has bad issues, we'll probably want to delete it later since it
        # was immediately deleted, making it not really useful
        if tracker.has_bad_issues():
            last_switcharoo.delete_later(roo)
        # If the roo doesn't have bad issues, we need to track the repair of it
        else:
            last_switcharoo.update_request(roo, requests=1, linked_roo=last_good)
    else:
        last_switcharoo.update(roo, reset_issues=True)


def reprocess(reddit, roo, last_switcharoo: SwitcharooLog, action, stage=ONLY_BAD, mute=True, verbose=True,
              reply_object=None):
    # When scanning the chain with this, do this in two passes. First to re-update the status of each roo submission
    # and secondly to then give instructions to fix
    if stage == ALL_ROOS and verbose:
        roo.print()
    old_tracker = last_switcharoo.get_issues(roo)

    # If this roo is currently being processed, don't touch it
    if old_tracker.submission_processing:
        if verbose:
            print("Roo {roo.id} is mid-processing, cannot be checked")
        return None

    if roo.submission:
        new_tracker = check_errors(reddit, last_switcharoo, roo, submission=roo.submission)
    else:
        new_tracker = check_errors(reddit, last_switcharoo, roo, comment=roo.comment)

    if not roo.link_post:
        # We're just updating a meta post with current removal status
        # If a meta post doesn't already have a submission_is_meta issue, remove it
        # It can't be added after the initial check to prevent deleting approved meta posts
        if not old_tracker.submission_is_meta and new_tracker.submission_is_meta:
            new_tracker.submission_is_meta = False
        if old_tracker != new_tracker:
            last_switcharoo.update(roo, roo_issues=new_tracker, reset_issues=True)
        return new_tracker

    if new_tracker is None:
        if verbose:
            print(f"Roo {roo.id} cannot be processed at the moment")
        return new_tracker

    request = last_switcharoo.check_request(roo)
    if not reply_object:
        reply_object = ReplyObject.from_roo(roo)

    # Scale cooldown time with age of roo
    grace_period = 3
    if roo.time < datetime.now() - timedelta(days=360):
        grace_period = 30
    if roo.time < datetime.now() - timedelta(days=180):
        grace_period = 14
    elif roo.time < datetime.now() - timedelta(days=30):
        grace_period = 7

    # If this roo has bad issues or it was marked for noncompliance,
    # it should be updated immediately to be removed from the chain
    if new_tracker.has_bad_issues() or old_tracker.user_noncompliance:
        if old_tracker.has_bad_issues():
            if verbose:
                roo.print()
                print("Roo was already bad")
        else:
            if verbose:
                roo.print()
                print("Roo has gone bad")
            action.process(new_tracker, ReplyObject.from_roo(roo), last_switcharoo.last_good(roo, offset=0), mute=mute)
            new_tracker.submission_deleted = True
            last_switcharoo.reset_request(roo=roo)
        last_switcharoo.update(roo, roo_issues=new_tracker, reset_issues=True)
        return new_tracker
    else:
        # If this roo was miraculously cured of bad issues
        if old_tracker.has_bad_issues():
            # Then reinstate it.
            print(f"Roo {roo.id} was miraculously cured of bad issues")
            last_switcharoo.update(roo, roo_issues=new_tracker, reset_issues=True)
            return new_tracker

    if new_tracker.has_issues():
        # If this is after they were supposed to fix something, gently ask them again
        # If this was long after they were supposed to fix something and nothing happened, delete the post
        # if parse.has_responded_to_post(roo.submission) and not request:
        #     print("Have previously responded, adding to DB")
        #     request = last_switcharoo.update_request(roo, requests=1)

        last_good = last_switcharoo.last_good(roo, offset=0)
        # Double check the correct link hasn't changed since last time
        # If it has we need to issue a new request for the new link
        same_link = True
        if request:
            if request.linked_roo:
                same_link = request.linked_roo.equals(last_good)

        # Has the issue set changed since last time
        if old_tracker == new_tracker and same_link:
            print("Issues unchanged")
            if not request:
                request = last_switcharoo.update_request(roo, requests=0, linked_roo=last_good)
            # If we are within cooldown, remind them and increase remind count
            action.act_again(reply_object, new_tracker, request, grace_period, stage, last_good)
        elif stage == ALL_ROOS:
            print("Roo issues have changed")
            # New situation, reset the request if it's there
            if request:
                request = last_switcharoo.reset_request(request=request)
            request = last_switcharoo.update_request(roo, requests=0, linked_roo=last_good)
            # Something has changed. Did we previously have issues too?
            # If we are within cooldown, remind them and increase remind count
            if old_tracker.has_issues():
                # Either they fixed and a new issue came up or it's a new issue
                action.act_again(reply_object, new_tracker, request, grace_period, stage,
                                 last_good)
            else:
                # This was working before, the chain might have just changed around them.
                action.act_again(reply_object, new_tracker, request, grace_period, stage,
                                 last_good)
    elif stage == ALL_ROOS:
        # If this is after they fixed something, say thank you
        if old_tracker.has_issues():
            action.thank_you(reply_object=reply_object, request=request)
            increment_user_fixes(last_switcharoo, reply_object)
        else:
            # If the old one didn't have issues, then nothing has changed, it's fine
            print("Correct")
        if request:
            last_switcharoo.reset_request(request=request)

    # After action has been taken on the roo, update the database with the new issue status
    if stage == ALL_ROOS:
        last_switcharoo.update(roo, roo_issues=new_tracker, reset_issues=True)

    return new_tracker


def add_comment(reddit, last_switcharoo, link):
    url = parse.RedditURL(link)
    comment = reddit.comment(url.comment_id)
    last_switcharoo.add_comment(url.thread_id, url.comment_id, url.params['context'],
                                datetime.utcfromtimestamp(comment.created_utc))


def double_check_link(reddit, last_switcharoo: SwitcharooLog, roo: Switcharoo):
    comment = roo.comment
    comment_url = parse.RedditURL(comment.permalink)
    comment_url.params['context'] = roo.context
    link = parse.parse_comment(comment.body)
    if not link.comment_id:
        if not comment:
            print(roo, f"https://reddit.com{comment.permalink}?context={roo.context}")
            input()
        new_link = parse.find_roo_comment(comment)
        if new_link:
            if new_link.comment_id:
                if comment_url.comment_id == new_link.comment_id:
                    return
                try:
                    new_link.params['context'] = str(int(comment_url.params.get('context', 0)) +
                                                     int(new_link.params.get('context', 0)))
                except ValueError:
                    print(f"Got {comment_url.params['context']} and {new_link.params['context']}, what should it be?")
                    new_link.params['context'] = int(input())
                print("Should", f"https://reddit.com{comment.permalink}?context={roo.context}", "be actually",
                      new_link.to_link(reddit), "?")
                print("(y/n/new_link)")
                option = input()
                if option == "n":
                    return
                elif option != "y":
                    new_link = parse.RedditURL(option)
                last_switcharoo.update(roo, thread_id=new_link.thread_id, comment_id=new_link.comment_id,
                                       context=new_link.params.get("context", link.params.get('context', 0)))
                return
        print(roo, f"https://reddit.com{comment.permalink}?context={roo.context}")
        print("Paste in a new link to replace otherwise enter to continue")
        option = input()
        if option:
            new_link = parse.RedditURL(option)
            last_switcharoo.update(roo, thread_id=new_link.thread_id, comment_id=new_link.comment_id,
                                   context=new_link.params.get("context", link.params.get('context', 0)))


def check_errors(reddit, last_switcharoo: SwitcharooLog, roo, init_db=False, submission=None, comment=None):
    """
    Check the submission to make sure it is correct
    :param comment:
    :param init_db:
    :param last_switcharoo:
    :param reddit: PRAW reddit instance
    :param submission: post to check
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
                if parse.only_reddit_url(submission.title, submission.selftext):
                    tracker.submission_is_meta = True
                    return tracker
            # Removed self submissions should be kept track of as well
            if submission.removed_by_category is not None or submission.banned_at_utc is not None \
                    or submission.selftext == "[deleted]":
                tracker.submission_deleted = True
            # 2022/02/10 - Check if this is one of the faulty deleted link posts
            if submission.title == "[deleted by user]" and submission.selftext == "[removed]" and \
                    submission.author is None:
                tracker.submission_deleted = True
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
                        print(
                            f"{roo.id} Banned by automoderator but previous comment isn't linked to it so leaving as is")

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

        # Todo: Make sure there is not already a good roo older than this one with these thread and comment ids

        # If we are in the middle of adding this to the db, add the thread and comment ids now
        if init_db:
            roo = last_switcharoo.update(roo, thread_id=submission_url.thread_id, comment_id=submission_url.comment_id,
                                         subreddit=submission_url.subreddit)

    else:
        # Not sure why this was happening every time
        # roo = last_switcharoo.update(roo, comment_id=comment.id)
        if init_db:
            roo = last_switcharoo.update(roo, comment_id=comment.id)

    # If comment was deleted, this will make an error. The try alleviates that
    try:
        comment.refresh()
    except (praw.exceptions.ClientException, praw.exceptions.PRAWException):
        s = reddit.submission(roo.thread_id)
        try:
            subreddit = s.subreddit
        except prawcore.exceptions.Forbidden:
            print("Forbidded from post, is the subreddit privated?")
            # If this hasn't even been added to the database yet, we have no idea what subreddit
            # To even make this kind of decision on. Reject it
            if init_db:
                tracker.subreddit_privated = True
                return tracker
            # Otherwise, attempt to check the database for this subreddit's status
            allowed = decide_subreddit_privated(reddit, last_switcharoo, roo.subreddit)
            if allowed is None or allowed is True:  # If we are awaiting a response or allowing, pass judgement for now
                return None
            else:   # Mods marked this subreddit as been permanently privated, mark broken
                tracker.subreddit_privated = True
                return tracker
        else:
            tracker.comment_deleted = True
            return tracker

    # Deleted comments sometimes don't generate errors
    if comment.body == "[removed]" or comment.body == "[deleted]":
        tracker.comment_deleted = True
        return tracker

    # Good date info to have on hand in the upcoming checks
    created = submission if submission else comment
    created = datetime.utcfromtimestamp(created.created_utc)

    # Get link in comment
    comment_url = parse.parse_comment(comment.body)

    # If there is no link, report it
    if not comment_url.is_reddit_url:
        """
        At this point, we need to decide if the roo is salvageable. We need to search the comments
        to see if there is an actual roo here and request a correction to it's link (and make it 
        the new last_good_submission). Otherwise if there is no roo, skip it by returning the current 
        last_good_submission and yell at them for linking something that isn't a roo.
        """
        tracker.comment_has_no_link = True
        return tracker

    if created > datetime(year=2021, month=3, day=1):
        if submission and comment:
            if comment.author != submission.author:
                tracker.user_mismatch = True
                return tracker

    # If the comment url links to the switcharoo subreddit, report it
    if comment_url.subreddit == "switcharoo":
        tracker.submission_linked_post = True
        return tracker

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
                if datetime(year=2021, month=3, day=10) < created:
                    tracker.comment_lacks_context = True
                # else:
                #     print("Ignoring bad context cause it's old")

            # Try to get the context value
            try:
                context = int(comment_url.params['context'])
            except (KeyError, ValueError):  # context is not a number
                thing = submission if submission else comment
                if datetime(year=2021, month=3, day=10) < created:
                    tracker.comment_lacks_context = True  # Should be a different error
                # else:
                #     print("Ignoring bad context cause it's old")

            if tracker.submission_deleted:
                if datetime(year=2021, month=3, day=10) > created:
                    # Check if previous comment is linked to it
                    previous_roo = last_switcharoo.next_good(roo)
                    if previous_roo:
                        previous_link = parse.parse_comment(previous_roo.comment.body)
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
                if datetime(year=2021, month=3, day=10) > created:
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
                # Extra check: Is this from before roo logging? Then allow roos that at least get the thread right
                # However, roos that aren't from this time get no such special privilege and are marked wrong
                if not (datetime(year=2019, month=2, day=23) > created and
                        comment_url.thread_id == last_good_submission.thread_id):
                    # I dunno what the user linked but they didn't link any switcharoo from the database
                    tracker.comment_linked_wrong = True
    else:
        print("Didn't have a last submission to check against")

    return tracker
