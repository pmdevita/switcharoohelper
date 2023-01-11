from random import randrange
from datetime import datetime, timedelta, date, time
from switcharoo.config.strings import ModActionStrings, WarnStrings, DeleteStrings, ReminderStrings, NewIssueStrings, \
    NewIssueDeleteStrings
from switcharoo.config.constants import ALL_ROOS
from switcharoo.core.reddit import ReplyObject, UserDoesNotExist
from switcharoo.config.credentials import CredentialsLoader
from switcharoo.core.operator import message_private_sub
from switcharoo.core.parse import REPatterns, RedditURL

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
    def act_again(self, reply_object: ReplyObject, issues, request, grace_period, stage, last_good_submission):
        # If it has been some time since we
        if request.not_responded_in_days(grace_period) or request.attempts == 0 or dry_run:
            if request.attempts > 30:
                # Alright pal you're heading out
                time = reply_object.created
                # The date before this went live
                print("User is non-compliant, deleting unless otherwise mentioned")
                if time > datetime(year=2021, month=3, day=11, hour=0, minute=0,
                                   second=0) or issues.comment_linked_bad_roo or issues.comment_linked_wrong:
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

    def thank_you(self, roo, reply_object: ReplyObject = None, request=None):
        if not reply_object:
            reply_object = ReplyObject.from_roo(roo)
        print(f"Thank you {reply_object.author} for fixing your roo! {reply_object.permalink}")

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
                                 "com{}?context={}".format(reply_object.permalink,
                                                           last_good_submission.comment.permalink,
                                                           last_good_submission.context))
        if issues.comment_linked_bad_roo:
            message_lines.append("{} comment is linked to bad roo, not https://www.reddit.com{}?context={}"
                                 .format(reply_object.permalink, last_good_submission.comment.permalink,
                                         last_good_submission.context))
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
    def thank_you(self, roo=None, reply_object: ReplyObject = None, request=None):
        if not reply_object:
            reply_object = ReplyObject.from_roo(roo)
        print(f"Thank you {reply_object.author} for fixing your roo! {reply_object.permalink}")

        post_creation = reply_object.created
        # Thank yous were implemented after this date and have not been brought earlier yet
        if post_creation > datetime(year=2021, month=6, day=1):
            if request:
                request_date = request.time.date()
                request_time = request.time.time()
                if request_date == date(2022, 2, 10) and request_time < time(4, 0):
                    reply_object.reply("Apologies for the error!",
                                       ModActionStrings.thank_you20220210 + ModActionStrings.footer)
                    return
            reply_object.reply("Thanks from r/switcharoo!", ModActionStrings.thank_you + ModActionStrings.footer)

    def process(self, issues, reply_object: ReplyObject, last_good_submission=None, strings=None, mute=False):
        # List of descriptions of every error the roo made
        message_lines = []
        # Do we request the user resubmit the roo?
        resubmit = True
        # Get main response strings
        if not strings:
            strings = DeleteStrings if issues.has_bad_issues() else WarnStrings

        # Do we need to be concerned about different formatting for messages?
        message_aware = strings.message_issue_strings is not None

        # Get strings for each issue
        issue_strings = strings.issue_strings

        # If we have multiple issues and the string set has a different issue set for that, use it
        if len(issues) > 1 and strings.multi_issue_strings is not None:
            issue_strings = strings.multi_issue_strings

        # If this is message aware, swap for those strings
        if message_aware:
            if not reply_object.can_reply():
                issue_strings = strings.message_issue_strings

                # If we have multiple issues and the string set has a different issue set for that, use it
                if len(issues) > 1 and strings.multi_issue_strings is not None:
                    issue_strings = strings.message_multi_issue_strings

        # Should the bot ask the mod team for further assistance?
        request_assistance = False

        last_good_url = None
        context = "0"
        # If we do have context, format the link ourselves with it
        if last_good_submission.context is not None:
            context = str(last_good_submission.context)
            if last_good_submission.context > 0:
                submission_url = RedditURL(last_good_submission.comment)
                submission_url.params["context"] = last_good_submission.context
                last_good_url = submission_url.to_link(self.reddit)
        if not last_good_url:
            if last_good_submission.submission:
                submission_url = RedditURL(last_good_submission.submission.url)
                last_good_url = submission_url.to_link(self.reddit)
            else:
                last_good_url = f"https://reddit.com{last_good_submission.comment.permalink}"

        comment_url = reply_object.permalink
        if reply_object.is_submission():
            comment_url = reply_object.get_comment()

        for issue in issues:
            # Retrieve message string for this issue
            string = getattr(issue_strings, issue.name, None)
            if string is None:
                continue
            if not string:
                raise Exception(f"Unsupported issue {issue.name} for string set {issue_strings}")
            message_lines.append(string.format(last_good_url=last_good_url, last_good_context=context,
                                               comment_url=comment_url))
            if not issue.resubmit:
                resubmit = False

        message = strings.header.format(["Hi!", "Hey!", "Howdy!", "Hello!"][randrange(4)])

        # Assemble message
        if len(message_lines) == 1:
            message = message + strings.single_reason.format(message_lines[0])
        else:
            reasons = ""
            for i in message_lines:
                # Indent any line breaks to match the bullets
                fixed_message = i.replace("\n", "\n  ")
                # Bullet point, capitalize the first letter
                bullet_point = f"* {fixed_message[0].upper()}{fixed_message[1:]}\n"
                # Messages that had line breaks need another line break at the end
                if "\n" in i:
                    bullet_point += "\n"
                reasons = reasons + bullet_point
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

        if issubclass(strings, DeleteStrings):
            already_deleted = reply_object.delete()
            # If this was already deleted, mute ourselves
            if already_deleted:
                mute = True

        if not mute:
            try:
                reply_object.reply(strings.subject, message, message_aware=message_aware)
            except UserDoesNotExist:
                # Posts that don't have a user attached to them anymore are OK unless we need to change things
                # That gets detected here. We then log the issue and then it will get picked up next run
                print("Tried to fix a submission with no user, marking as noncompliant")
                issues.user_noncompliance = True
        # if request_assistance:
        #     self.reddit.subreddit("switcharoo").message("switcharoohelper requests assistance",
        #                                                 "{}".format(submission.url))


def decide_subreddit_privated(reddit, last_switcharoo, subreddit):
    ps = last_switcharoo.check_privated_sub(subreddit)
    if ps:
        if not ps.is_expired() and ps.allowed is not None:
            # We have a valid and current decision, report it back
            return ps.allowed
        else:
            if ps.update_requested:
                return None
            ps.reset()
    # There is no currently valid decision and the mods haven't been asked, ask the mods
    message_private_sub(reddit, subreddit)
    last_switcharoo.update_privated_sub(subreddit, update_requested=True)
    return None


def modmail_action(last_switcharoo, context, message):
    decision_type = context.get("decision-type", None)
    if decision_type == "private-subreddit":
        return private_subreddit(last_switcharoo, context["subreddit"], message)


def inbox_action(reply_object, last_switcharoo, context, message):
    decision_type = context.get("decision-type", None)
    if decision_type == "meta-roo":
        if "not a roo" in message.body.lower():
            return restore_meta(reply_object, last_switcharoo)


def private_subreddit(last_switcharoo, subreddit, message):
    match = REPatterns.private_subreddit_response.findall(message)
    if match:
        match = match[0]
        status = None
        time = None
        if match[0].lower() == "allow":
            status = True
        elif match[0].lower() == "deny":
            status = False
        message = f"Got it, {'allowed' if status else 'denied'}"
        if match[1]:
            time = datetime.now()
            amount = int(match[1])
            unit = match[2] + "s"
            if unit == "months":
                amount = amount * 4
                unit = "weeks"
            if unit == "years":
                amount = amount * 52
                unit = "weeks"
            time = time + timedelta(**{unit: amount})
            message += f" for {amount} {unit}"
        last_switcharoo.update_privated_sub(subreddit, allowed=status, expiration=time, update_requested=False)
        return message
    return None


def increment_user_fixes(last_switcharoo, reply_object):
    if creds.get("award", "false").lower() == "true":
        # Only award old posts, not new posts that were just wrong
        if reply_object.created < datetime.now() - timedelta(weeks=2):
            fixes = last_switcharoo.check_user_flair(reply_object.author.name)
            fixes = fixes.fixes if fixes else 0
            last_switcharoo.update_user_flair(user=reply_object.author.name, fixes=fixes + 1)


def restore_meta(reply_object, last_switcharoo):
    issues = last_switcharoo.get_issues(reply_object.roo)
    if issues.submission_is_meta:
        reply_object.approve()
        issues.submission_is_meta = False
        last_switcharoo.update(reply_object.roo, roo_issues=issues, reset_issues=True)
        return "Post approved!\n\n" + ModActionStrings.footer
