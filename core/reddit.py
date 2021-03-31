import praw.models
import praw.exceptions
from datetime import datetime
from core.credentials import CredentialsLoader

creds = CredentialsLoader.get_credentials()['general']


class UserDoesNotExist(Exception):
    pass


class ReplyObject:
    def __init__(self, obj):
        self.object = obj
        self.roo = None
        self.dry_run = creds['dry_run'].lower() != "false"

    @classmethod
    def from_roo(cls, roo):
        if roo.submission:
            a = cls(roo.submission)
        else:
            a = cls(roo.comment)
        a.roo = roo
        return a

    def reply(self, subject, message):
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
                if self.roo:
                    link = f"https://reddit.com{self.roo.comment.permalink}"
                redditor.message(subject=subject, message=f"{link}\n\n{message}", from_subreddit="switcharoo")
        elif isinstance(self.object, praw.models.Comment):
            redditor = self.object.author
            redditor.message(subject=subject, message=f"{self.permalink}\n\n{message}", from_subreddit="switcharoo")

    def delete(self):
        if self.dry_run:
            return
        if isinstance(self.object, praw.models.Submission):
            if not self.object.removed_by:
                self.object.mod.remove()
            else:
                print("Not removing since it was already removed")

    @property
    def permalink(self):
        return f"https://reddit.com{self.object.permalink}"

    @property
    def author(self):
        return self.object.author

    @property
    def created(self):
        return datetime.utcfromtimestamp(self.object.created_utc)
