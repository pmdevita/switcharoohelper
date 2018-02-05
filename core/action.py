from random import randrange
from core.issues import *
from core.constants import ModActionStrings as MS

DELETE = 0
WARN = 1

class BaseAction:
    def __init__(self, reddit):
        """
        :param reddit: PRAW Reddit instance
        """
        self.reddit = reddit
        self.issues = []

    def add_issue(self, issue):
        self.issues.append(issue)

    def act(self, submission, last_submission=None):
        if self.issues:
            self.process(submission, last_submission)

    def process(self, submission, last_submission=None):
        pass

    def reset(self):
        self.issues = []

class PrintAction(BaseAction):
    def process(self, submission, last_submission=None):
        message_lines = []
        if submission_lacks_context in self.issues:
            message_lines.append("https://www.reddit.com{} submission link does not have ?context".format(
                submission.permalink))
        if submission_linked_thread in self.issues:
            message_lines.append("https://www.reddit.com{} linked to a thread, not a comment".format(
                submission.permalink))
        if comment_deleted in self.issues:
            message_lines.append("https://www.reddit.com{} comment got deleted. Post should be removed.".format(
                submission.permalink))
        if comment_has_no_link in self.issues:
            message_lines.append("https://www.reddit.com{} has no link in the comment".format(
                submission.permalink))
        if comment_linked_wrong in self.issues:
            message_lines.append("https://www.reddit.com{} comment is not linked to the next level".format(
                submission.permalink))
        if comment_lacks_context in self.issues:
            message_lines.append("https://www.reddit.com{} comment is correct link but did not "
                                 "have ?context in it".format(submission.permalink))
        for i in message_lines:
            print(" ", i)

class ModAction(BaseAction):
    def process(self, submission, last_submission=None):
        # List of descriptions of every error the roo made
        message_lines = []
        # Do we request the user resubmit the roo?
        resubmit = True
        # What do we do after we tell them what they did wrong?
        action = DELETE
        # Should the bot ask the mod team for further assistance?
        request_assistance = False

        # What issues have been raised? Add their messages to the list
        if submission_lacks_context in self.issues:
            message_lines.append("the link to your switcharoo does not contain the `?context=x` suffix. Read "
                                 "the sidebar for more information.")
        if submission_linked_thread in self.issues:
            message_lines.append("your post's link is to a Reddit thread, not a comment permalink.")
        if comment_deleted in self.issues:
            message_lines.append("your switcharoo comment was deleted.")
            resubmit = False
        if comment_has_no_link in self.issues:
            message_lines.append("your submission does not link to a switcharoo. It's very likely you linked the "
                                 "wrong comment. Read the sidebar for more information.")
        if comment_linked_wrong in self.issues:
            message_lines.append("your switcharoo is not linked to the correct roo. Did you remember to sort the "
                                 "subreddit by new? The correct link is \n\n    {}\n\nCan you please change it to that? "
                                 "Thanks!".format(last_submission["submission_url"]))
            resubmit = False
            action = WARN
        if comment_linked_bad_roo in self.issues:
            message_lines.append("your switcharoo links to a broken roo. Can you please change it to this link?\n\n"
                                 "    {}\n\nThanks!".format(last_submission["submission_url"]))
            resubmit = False
            action = WARN
        if comment_lacks_context in self.issues:
            message_lines.append("your switcharoo's link does not contain the `?context=x` suffix. It's likely this "
                                 "isn't your fault and the roo'er before you did not add it to their link.\n\n"
                                 "I've asked the mods to help out with determining how much context is needed but you "
                                 "can also figure it out yourself if you'd like.\n\nGo to the switcharoo your comment "
                                 "links to and count how many comments above it are needed to understand the joke. "
                                 "Then, in the link in your comment, append `?context=x` to the end of the link, "
                                 "replacing x with the number of levels you counted.")
            resubmit = False
            action = WARN
            request_assistance = True

        # Assemble message

        message = MS.header.format(["Hi!", "Hey!", "Howdy!", "Hello!"][randrange(4)])
        if action == DELETE:
            if len(message_lines) == 1:
                message = message + MS.delete_single_reason.format(message_lines[0])
            else:
                reasons = ""
                for i in message_lines:
                    reasons = reasons + "* " + i[0].upper() + i[1:] + "\n"
                message = message + MS.delete_multiple_reason.format(reasons)
            if resubmit:
                message = message + MS.resubmit_text

        elif action == WARN:
            if len(message_lines) == 1:
                message = message + MS.warn_single_reason.format(message_lines[0])
            else:
                warnings = ""
        message = message + MS.footer

        # Reply and delete (if that is what we are supposed to do)!
        # submission.reply(message)
        # if action == DELETE:
        #     submission.mod.remove()
        print(message)