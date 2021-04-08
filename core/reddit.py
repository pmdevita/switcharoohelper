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
        if roo.submission:
            a = cls(roo.submission, reply_to)
        else:
            a = cls(roo.comment, reply_to)
        a.roo = roo
        return a

    def reply(self, subject, message, message_aware=False):
        if self.dry_run:
            return

        if isinstance(self.object, praw.models.Submission):
            try:
                comment = self.object.reply(message)
                comment.mod.distinguish()
            except praw.exceptions.RedditAPIException:
                redditor = self.object.author
                if redditor is None:
                    if self.roo:
                        redditor = self.roo.comment.author
                        if redditor is None:
                            raise UserDoesNotExist
                    raise UserDoesNotExist
                link = self.permalink
                new_message = message
                if self.roo and not message_aware:
                    new_message = f"https://reddit.com{self.roo.comment.permalink}\n\n{message}"
                redditor.message(subject=subject, message=new_message, from_subreddit="switcharoo")
        elif isinstance(self.object, praw.models.Comment):
            redditor = self.object.author
            redditor.message(subject=subject, message=f"{self.permalink}\n\n{message}", from_subreddit="switcharoo")

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
