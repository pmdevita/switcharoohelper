from random import randrange
from datetime import datetime
from core.issues import *
from core.strings import BLANK, ModActionStrings, WarnStrings, DeleteStrings, ReminderStrings, NewIssueStrings, NewIssueDeleteStrings
from core.constants import ALL_ROOS
from core.reddit import ReplyObject, UserDoesNotExist
from core.credentials import CredentialsLoader

creds = CredentialsLoader.get_credentials()['general']
dry_run = creds['dry_run'].lower() != "false"

# issues = GetIssues.get()
# bad_issues = GetIssues.bad()

WARN = 1


class BaseAction:
    def __init__(self, reddit):
        """
        :param reddit: PRAW Reddit instance
        """
        self.issues = set()
        self.reddit = reddit

    def add_issue(self, issue):
        self.issues.add(issue)

    def act(self, issues, submission, last_good_submission=None):
        if issues.has_issues():
            self.process(issues, submission, last_good_submission)
        else:
            print(" Correct")

    def process(self, issues, reply_object: ReplyObject, last_good_submission=None, strings=None):
        pass

    # I'm sorry for the name
    def act_again(self, roo, issues, request, grace_period, stage, last_good_submission):
        # If it has been some time since we
        if request.not_responded_in_days(grace_period) or request.attempts == 0 or dry_run:
            reply_object = ReplyObject.from_roo(roo)
            if request.attempts > 2:
                # Alright pal you're heading out
                time = reply_object.created
                # The date before this went live
                print("User is non-compliant, deleting unless otherwise mentioned")
                if time > datetime(year=2021, month=3, day=11, hour=0, minute=0, second=0) or issues.comment_linked_bad_roo or issues.comment_linked_wrong:
                    issues.user_noncompliance = True
                    self.process(issues, reply_object, last_good_submission, strings=NewIssueDeleteStrings)
                    if not dry_run:
                        request.reset()
                else:
                    print("User is non-compliant, not deleting though")
            elif request.attempts == 0:
                if stage == ALL_ROOS:
                    # They've never been asked (but this isn't none for some reason), ask nicely
                    # Not sure if this would even ever fire
                    self.process(issues, reply_object, last_good_submission, strings=NewIssueStrings)
                    # If we are on a dry run, then delete this already null request
                    if dry_run:
                        request.reset()
                    # Normal behavior
                    else:
                        request.set_attempts(request.attempts + 1)
                else:
                    # We can get here sometimes when processing for deleted roos
                    # Delete this request
                    request.reset()
            elif stage == ALL_ROOS:
                # They've been told once, they get one more warning
                self.process(issues, reply_object, last_good_submission, strings=ReminderStrings)
                if not dry_run:
                    request.set_attempts(request.attempts + 1)
        else:
            print("Still waiting on cooldown")

    def thank_you(self, roo, award):
        reply_object = ReplyObject.from_roo(roo)
        print(f"Thank you {reply_object.author} for fixing your roo! {reply_object.permalink}")
        if award:
            # Gib award
            pass

    def reset(self):
        self.issues = set()


class PrintAction(BaseAction):
    def process(self, issues, reply_object: ReplyObject, last_good_submission=None, strings=None):
        message_lines = []
        if issues.submission_lacks_context:
            message_lines.append("{} submission link does not have ?context".format(
                reply_object.permalink))
        if issues.submission_linked_thread:
            message_lines.append("{} linked to a thread, not a comment".format(
                reply_object.permalink))
        if issues.comment_deleted:
            message_lines.append("{} comment got deleted. Post should be removed.".format(
                reply_object.permalink))
        if issues.comment_has_no_link:
            message_lines.append("{} has no link in the comment".format(
                reply_object.permalink))
        if issues.comment_linked_wrong:
            message_lines.append("{} comment is not linked to the next level, https://www.reddit."
                                 "com{}?context={}".format(reply_object.permalink, last_good_submission.comment.permalink, last_good_submission.context))
        if issues.comment_linked_bad_roo:
            message_lines.append("{} comment is linked to bad roo, not https://www.reddit.com{}?context={}"
                                 .format(reply_object.permalink, last_good_submission.comment.permalink, last_good_submission.context))
        if issues.comment_lacks_context:
            message_lines.append("{} comment is correct link but did not "
                                 "have ?context in it".format(reply_object.permalink))
        if issues.submission_multiple_params:
            message_lines.append("{} had more than one param sections".format(
                reply_object.permalink))
        if issues.submission_link_final_slash:
            message_lines.append("{} had a trailing slash at the end".format(
                reply_object.permalink))
        if issues.submission_not_reddit:
            message_lines.append("{} is not a reddit link.".format(
                reply_object.permalink))
        if issues.submission_is_meta:
            message_lines.append("{} is a meta post switcharoo".format(
                reply_object.permalink))
        if issues.submission_bad_url:
            message_lines.append("{} has a malformed URL".format(
                reply_object.permalink))
        if issues.user_noncompliance:
            message_lines.append("{} has ignored bot instruction".format(
                reply_object.permalink))
        if message_lines:
            for i in message_lines:
                print(" ", i)


class ModAction(BaseAction):
    def thank_you(self, roo, award, reply_object: ReplyObject = None):
        if not reply_object:
            reply_object = ReplyObject.from_roo(roo)
        print(f"Thank you {reply_object.author} for fixing your roo! {reply_object.permalink}")

        time = reply_object.created
        if time > datetime(year=2021, month=3, day=1):
            reply_object.reply("Thanks from r/switcharoo!", ModActionStrings.thank_you + ModActionStrings.footer)

    def process(self, issues, reply_object: ReplyObject, last_good_submission=None, strings=None, mute=False):
        # List of descriptions of every error the roo made
        message_lines = []
        # Do we request the user resubmit the roo?
        resubmit = True
        # Get main response strings
        if not strings:
            strings = DeleteStrings if issues.has_bad_issues() else WarnStrings

        # Get strings for each issue
        issue_strings = strings.issue_strings

        # If we have multiple issues and the string set has a different issue set for that, use it
        if len(issues) > 1 and strings.multi_issue_strings is not None:
            issue_strings = strings.multi_issue_strings

        # Should the bot ask the mod team for further assistance?
        request_assistance = False

        for issue in issues:
            string = getattr(issue_strings, issue.name, None)
            if string == BLANK:
                continue
            if not string:
                raise Exception(f"Unsupported issue {issue.name} for string set {issue_strings}")
            last_good_url = None
            # If we do have context, format the link ourselves with it
            if last_good_submission.context is not None:
                if last_good_submission.context > 0:
                    last_good_url = f"https://reddit.com{last_good_submission.comment.permalink}" \
                                           f"?context={last_good_submission.context} "
            if not last_good_url:
                if last_good_submission.submission:
                    last_good_url = last_good_submission.submission.url
                else:
                    last_good_url = f"https://reddit.com{last_good_submission.comment.permalink}"

            message_lines.append(string.format(last_good_url=last_good_url))

        # What issues have been raised? Add their messages to the list
        # if issues.submission_lacks_context:
        #     message_lines.append("the link to your switcharoo does not contain the `?context=x` suffix. Read "
        #                          "the sidebar for more information.")
        # if issues.submission_linked_thread:
        #     message_lines.append("your post's link is to a Reddit thread, not a comment permalink. Make sure to "
        #                          "click the permalink button on the comment (or on mobile, grab the link to the "
        #                          "comment).")
        if issues.comment_deleted:
            # message_lines.append("your switcharoo comment was deleted. If you deleted your comment, please don't do "
            #                      "that. If you can still see the comment, then the subreddit moderators probably "
            #                      "removed it. If you want to double check, log out or log into a "
            #                      "different account and look for your comment.\n\nIf you think your comment was "
            #                      "removed by was that subreddit's moderators, please let us know so we can add it to "
            #                      "the forbidden subs list. Also, sorry. It sucks when this happens.")
            resubmit = False
        # if issues.comment_has_no_link:
        #     message_lines.append("your submission does not link to a switcharoo. It's very likely you linked the "
        #                          "wrong comment. Read the sidebar or stickied \"how to\" post for more information.")
        if issues.comment_linked_wrong:
            # message_lines.append("your switcharoo is not linked to the correct roo. Did you remember to sort the "
            #                      "subreddit by new? The correct link is \n\n{}\n\nCan you please change it to "
            #                      "that? Thanks!".format(last_good_submission.submission.url))
            resubmit = False
            action = WARN
        if issues.comment_linked_bad_roo:
            # message_lines.append("your switcharoo links to a broken roo. Can you please change it to this link?\n\n"
            #                      "{}\n\nThanks!".format(last_good_submission.submission.url))
            resubmit = False
            action = WARN
        if issues.comment_lacks_context:
            # message_lines.append("the roo you have **linked to in your comment** (not the URL you have submitted) is "
            #                      "missing a `?context=x` suffix. Most likely, the roo'er previous to you left it out "
            #                      "but it's possible you missed it in copying their link.\n\nGo to the switcharoo your "
            #                      "comment links to and count how many comments above it are needed to understand the "
            #                      "joke. Then, in the link in your comment, append `?context=x` to the end of the link, "
            #                      "replacing x with the number of levels you counted. Thanks for fixing it!")
            resubmit = False
            action = WARN
            request_assistance = True
        if issues.submission_multiple_params:
            # message_lines.append("your switcharoo had multiple '?' sections at the end of it. You can resubmit if you "
            #                      "delete everything after and including the '?' in your URL and then append "
            #                      "`?context=x` to the end of the URL. Don't forget to relink your switcharoo to the "
            #                      "newest switcharoo submission!")
            resubmit = False    # Already gives resubmit instructions so this is redundant
        if issues.submission_link_final_slash:
            # message_lines.append("your switcharoo had a trailing slash (\"/\") at the end of it. This causes the "
            #                      "`?context=x` property to not work. You can resubmit if you delete the slash(es) "
            #                      "at the end of the URL. Don't forget to relink your switcharoo to the "
            #                      "newest switcharoo submission!")
            resubmit = False
        if issues.submission_not_reddit:
            # message_lines.append("the link leads outside of reddit. Did you mean to submit a meta "
            #                      "post? Read the sidebar for more information.")
            resubmit = False
        # if issues.submission_is_meta:
        #     message_lines.append("your post appears to be a roo submitted as a text post. All switcharoos should be "
        #                          "submitted as link posts for clarity and subreddit organization.")
        # if issues.submission_bad_url:
        #     message_lines.append("your URL seems to have either the submission ID or post ID messed up. Did you copy "
        #                          "it correctly?")
        if issues.user_noncompliance:
            # message_lines.append("you have ignored the request to fix the linking problems. Contact the moderators "
            #                      "to have your post reinstated.")
            resubmit = False

        # Choose template based on action
        # This should be a subclass thing, not this
        # if action == DELETE:
        #     header = MS.header
        #     reason = MS.delete_single_reason
        #     multi_reason = MS.delete_multiple_reason
        # elif action == WARN:
        #     header = MS.header
        #     reason = MS.warn_single_reason
        #     multi_reason = MS.warn_multiple_reason

        message = strings.header.format(["Hi!", "Hey!", "Howdy!", "Hello!"][randrange(4)])

        # Assemble message
        if len(message_lines) == 1:
            message = message + strings.single_reason.format(message_lines[0])
        else:
            reasons = ""
            for i in message_lines:
                reasons = reasons + "* {}{}{}".format(i[0].upper(), i[1:], "\n")
            message = message + strings.multiple_reason.format(reasons)
        if strings == DeleteStrings and resubmit:
            message = message + strings.resubmit_text.format("issue" if len(message_lines) == 1 else "issues")

        if reply_object.created < datetime(year=2020, month=6, day=1):
            message = message + strings.old_footer
        else:
            message = message + strings.footer

        print(message)
        print("Replying and deleting if true", strings == DeleteStrings)
        # input()
        # Reply and delete (if that is what we are supposed to do)!

        if not mute:
            try:
                reply_object.reply(strings.subject, message)
            except UserDoesNotExist:
                # Posts that don't have a user attached to them anymore are OK unless we need to change things
                # That gets detected here. We then log the issue and then it will get picked up next run
                print("Tried to fix a submission with no user, marking as noncompliant")
                issues.user_noncompliance = True
        if issubclass(strings, DeleteStrings):
            reply_object.delete()
        # if request_assistance:
        #     self.reddit.subreddit("switcharoo").message("switcharoohelper requests assistance",
        #                                                 "{}".format(submission.url))
