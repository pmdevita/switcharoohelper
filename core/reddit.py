import praw.models
import praw.exceptions
from datetime import datetime, timedelta
from core.credentials import CredentialsLoader

creds = CredentialsLoader.get_credentials()['general']


class UserDoesNotExist(Exception):
    pass


class ReplyObject:
    def __init__(self, obj, reply_to=None):
        self.object = obj
        self.reply_to = reply_to
        self.roo = None
        self.dry_run = creds['dry_run'].lower() != "false"

    @classmethod
    def from_roo(cls, roo, reply_to=None):
        if roo:
            if roo.submission:
                a = cls(roo.submission, reply_to)
            else:
                a = cls(roo.comment, reply_to)
            a.roo = roo
        else:
            a = cls(reply_to, reply_to)
        return a

    def reply(self, subject, message, message_aware=False):
        if self.dry_run:
            return

        if self.reply_to:
            if isinstance(self.reply_to, praw.models.Submission):
                try:
                    # Attempt to comment on the submission
                    comment = self.reply_to.reply(message)
                    comment.mod.distinguish()
                except praw.exceptions.RedditAPIException:
                    # If it fails, try to message them the normal way
                    pass
            elif isinstance(self.reply_to, praw.models.Comment):
                try:
                    # Attempt to comment on the comment
                    comment = self.reply_to.reply(message)
                    comment.mod.distinguish()
                except praw.exceptions.RedditAPIException:
                    # If it fails, try to message them the normal way
                    pass

        if isinstance(self.object, praw.models.Submission):
            try:
                # Attempt to comment on the submission
                comment = self.object.reply(message)
                comment.mod.distinguish()
            except praw.exceptions.RedditAPIException:
                # If that fails, attempt to message them instead
                self._backup_message(subject, message, f"https://reddit.com{self.roo.comment.permalink}", message_aware)
        elif isinstance(self.object, praw.models.Comment):
            try:
                # Attempt to comment on the comment
                comment = self.object.reply(message)
                comment.mod.distinguish()
            except praw.exceptions.RedditAPIException:
                # If that fails, attempt to message them instead
                self._backup_message(subject, message, self.permalink, message_aware)

    def _backup_message(self, subject, message, link, message_aware=False):
        redditor = self.object.author
        if redditor is None:
            if self.roo:
                redditor = self.roo.comment.author
                if redditor is None:
                    raise UserDoesNotExist
            raise UserDoesNotExist
        new_message = message
        # If this message is not message aware (formatted for PMing) then add the link in
        if self.roo and not message_aware:
            new_message = f"{link}\n\n{message}"
        redditor.message(subject=subject, message=new_message, from_subreddit="switcharoo")

    def message(self, subject, message):
        pass

    def delete(self):
        if self.dry_run:
            return True  # Mute just in case in dry runs
        if isinstance(self.object, praw.models.Submission):
            if not self.object.removed_by:
                self.object.mod.remove()
                return False
            else:
                print("Not removing since it was already removed")
                return True

    def can_reply(self):
        # Just to be absolutely sure we can
        if isinstance(self.object, praw.models.Comment):
            return False
        return (self.created - timedelta(seconds=5)) > (datetime.now() - timedelta(days=180))

    @property
    def permalink(self):
        return f"https://reddit.com{self.object.permalink}"

    @property
    def author(self):
        return self.object.author

    @property
    def created(self):
        return datetime.utcfromtimestamp(self.object.created_utc)

    def is_comment(self):
        return isinstance(self.object, praw.models.Comment)

    def is_submission(self):
        return isinstance(self.object, praw.models.Submission)

    def get_comment(self):
        if self.is_submission() and self.roo:
            return f"https://reddit.com{self.roo.comment.permalink}"
