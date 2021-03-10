from random import randrange
from core.issues import *
from core.constants import ModActionStrings as MS
from core.constants import ALL_ROOS

# issues = GetIssues.get()
# bad_issues = GetIssues.bad()

DELETE = 0
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

    def process(self, issues, submission, last_good_submission=None, reminder=False):
        pass

    # I'm sorry for the name
    def act_again(self, roo, issues, request, grace_period, stage, last_good_submission):
        # If it has been some time since we
        if request.not_responded_in_days(grace_period) or request.attempts == 0:
            if request.attempts >= 3:
                # Alright pal you're heading out
                # Since this should be the same ref, it should get updated back up in process
                issues.user_noncompliance = True
                self.process(issues, roo.submission, last_good_submission)
                request.reset()
            elif request.attempts == 0 and stage == ALL_ROOS:
                # They've never been asked (but this isn't none for some reason), ask nicely
                # Not sure if this would even ever fire
                self.process(issues, roo.submission, last_good_submission)
                request.set_attempts(request.attempts + 1)
            elif stage == ALL_ROOS:
                # They've been told once, they get one more warning
                self.process(issues, roo.submission, last_good_submission, reminder=True)
                request.set_attempts(request.attempts + 1)
        else:
            print("Still waiting on cooldown")

    def thank_you(self, roo, award):
        print(f"Thank you {roo.submission.author} for fixing your roo! {roo.submission.permalink}")
        if award:
            # Gib award
            pass


    def reset(self):
        self.issues = set()


class PrintAction(BaseAction):
    def process(self, issues, submission, last_good_submission=None, reminder=False):
        message_lines = []
        if issues.submission_lacks_context:
            message_lines.append("https://www.reddit.com{} submission link does not have ?context".format(
                submission.permalink))
        if issues.submission_linked_thread:
            message_lines.append("https://www.reddit.com{} linked to a thread, not a comment".format(
                submission.permalink))
        if issues.comment_deleted:
            message_lines.append("https://www.reddit.com{} comment got deleted. Post should be removed.".format(
                submission.permalink))
        if issues.comment_has_no_link:
            message_lines.append("https://www.reddit.com{} has no link in the comment".format(
                submission.permalink))
        if issues.comment_linked_wrong:
            message_lines.append("https://www.reddit.com{} comment is not linked to the next level, https://www.reddit."
                                 "com{}".format(submission.permalink, last_good_submission.comment.permalink))
        if issues.comment_linked_bad_roo:
            message_lines.append("https://www.reddit.com{} comment is linked to bad roo, not https://www.reddit.com{}"
                                 .format(submission.permalink, last_good_submission.comment.permalink))
        if issues.comment_lacks_context:
            message_lines.append("https://www.reddit.com{} comment is correct link but did not "
                                 "have ?context in it".format(submission.permalink))
        if issues.submission_multiple_params:
            message_lines.append("https://www.reddit.com{} had more than one param sections".format(
                submission.permalink))
        if issues.submission_link_final_slash:
            message_lines.append("https://www.reddit.com{} had a trailing slash at the end".format(
                submission.permalink))
        if issues.submission_not_reddit:
            message_lines.append("https://www.reddit.com{} is not a reddit link.".format(
                submission.permalink))
        if issues.submission_is_meta:
            message_lines.append("https://www.reddit.com{} is a meta post switcharoo".format(
                submission.permalink))
        if issues.submission_bad_url:
            message_lines.append("https://www.reddit.com{} has a malformed URL".format(
                submission.permalink))
        if issues.user_noncompliance:
            message_lines.append("https://www.reddit.com{} has ignored bot instruction".format(
                submission.permalink))
        if message_lines:
            for i in message_lines:
                print(" ", i)


class ModAction(BaseAction):
    def process(self, issues, submission, last_good_submission=None, reminder=False):
        # List of descriptions of every error the roo made
        message_lines = []
        # Do we request the user resubmit the roo?
        resubmit = True
        # What do we do after we tell them what they did wrong?
        action = DELETE
        # Should the bot ask the mod team for further assistance?
        request_assistance = False

        # What issues have been raised? Add their messages to the list
        if issues.submission_lacks_context:
            message_lines.append("the link to your switcharoo does not contain the `?context=x` suffix. Read "
                                 "the sidebar for more information.")
        if issues.submission_linked_thread:
            message_lines.append("your post's link is to a Reddit thread, not a comment permalink. Make sure to "
                                 "click the permalink button on the comment (or on mobile, grab the link to the "
                                 "comment).")
        if issues.comment_deleted:
            message_lines.append("your switcharoo comment was deleted. If you deleted your comment, please don't do "
                                 "that. If you can still see the comment, then the subreddit moderators probably "
                                 "removed it. If you want to double check, log out or log into a "
                                 "different account and look for your comment.\n\nIf you think your comment was "
                                 "removed by was that subreddit's moderators, please let us know so we can add it to "
                                 "the forbidden subs list. Also, sorry. It sucks when this happens.")
            resubmit = False
        if issues.comment_has_no_link:
            message_lines.append("your submission does not link to a switcharoo. It's very likely you linked the "
                                 "wrong comment. Read the sidebar or stickied \"how to\" post for more information.")
        if issues.comment_linked_wrong:
            message_lines.append("your switcharoo is not linked to the correct roo. Did you remember to sort the "
                                 "subreddit by new? The correct link is \n\n{}\n\nCan you please change it to "
                                 "that? Thanks!".format(last_good_submission.submission.url))
            resubmit = False
            action = WARN
        if issues.comment_linked_bad_roo:
            message_lines.append("your switcharoo links to a broken roo. Can you please change it to this link?\n\n"
                                 "{}\n\nThanks!".format(last_good_submission.submission.url))
            resubmit = False
            action = WARN
        if issues.comment_lacks_context:
            message_lines.append("the roo you have **linked to in your comment** (not the URL you have submitted) is "
                                 "missing a `?context=x` suffix. Most likely, the roo'er previous to you left it out "
                                 "but it's possible you missed it in copying their link.\n\nGo to the switcharoo your "
                                 "comment links to and count how many comments above it are needed to understand the "
                                 "joke. Then, in the link in your comment, append `?context=x` to the end of the link, "
                                 "replacing x with the number of levels you counted. Thanks for fixing it!")
            resubmit = False
            action = WARN
            request_assistance = True
        if issues.submission_multiple_params:
            message_lines.append("your switcharoo had multiple '?' sections at the end of it. You can resubmit if you "
                                 "delete everything after and including the '?' in your URL and then append "
                                 "`?context=x` to the end of the URL. Don't forget to relink your switcharoo to the "
                                 "newest switcharoo submission!")
            resubmit = False
        if issues.submission_link_final_slash:
            message_lines.append("your switcharoo had a trailing slash (\"/\") at the end of it. This causes the "
                                 "`?context=x` property to not work. You can resubmit if you delete the slash(es) "
                                 "at the end of the URL. Don't forget to relink your switcharoo to the "
                                 "newest switcharoo submission!")
            resubmit = False
        if issues.submission_not_reddit:
            message_lines.append("the link leads outside of reddit. Did you mean to submit a meta "
                                 "post? Read the sidebar for more information.")
            resubmit = False
        if issues.submission_is_meta:
            message_lines.append("your post appears to be a roo submitted as a text post. All switcharoos should be "
                                 "submitted as link posts for clarity and subreddit organization.")
        if issues.submission_bad_url:
            message_lines.append("your URL seems to have either the submission ID or post ID messed up. Did you copy "
                                 "it correctly?")
        if issues.user_noncompliance:
            message_lines.append("you have ignored the request to fix the linking problems. Contact the moderators "
                                 "to have your post reinstated.")

        # Choose template based on action
        if action == DELETE:
            reason = MS.delete_single_reason
            multi_reason = MS.delete_multiple_reason
        elif action == WARN:
            reason = MS.warn_single_reason
            multi_reason = MS.warn_multiple_reason

        message = MS.header.format(["Hi!", "Hey!", "Howdy!", "Hello!"][randrange(4)])

        # Assemble message
        if len(message_lines) == 1:
            message = message + reason.format(message_lines[0])
        else:
            reasons = ""
            for i in message_lines:
                reasons = reasons + "* {}{}{}".format(i[0].upper(), i[1:], "\n")
            message = message + multi_reason.format(reasons)
        if action == DELETE and resubmit:
            message = message + MS.resubmit_text.format("issue" if len(message_lines) == 1 else "issues")

        message = message + MS.footer

        # print(message)
        print("Replying and deleting if true", action == DELETE)
        # input()
        # Reply and delete (if that is what we are supposed to do)!

        # return

        comment = submission.reply(message)
        comment.mod.distinguish()
        if action == DELETE:
            submission.mod.remove()
        if request_assistance:
            self.reddit.subreddit("switcharoo").message("switcharoohelper requests assistance",
                                                        "{}".format(submission.url))
