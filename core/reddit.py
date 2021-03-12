import praw.models
import praw.exceptions
from datetime import datetime


class ReplyObject:
    def __init__(self, obj):
        self.object = obj

    @classmethod
    def from_roo(cls, roo):
        if roo.submission:
            return cls(roo.submission)
        else:
            return cls(roo.comment)

    def reply(self, subject, message):
        if isinstance(self.object, praw.models.Submission):
            try:
                comment = self.object.reply(message)
                comment.mod.distinguish()
            except praw.exceptions.RedditAPIException:
                redditor = self.object.author
                redditor.message(subject=subject, message=f"{self.permalink}\n\n{message}", from_subreddit="switcharoo")
        elif isinstance(self.object, praw.models.Comment):
            redditor = self.object.author
            redditor.message(subject=subject, message=f"{self.permalink}\n\n{message}", from_subreddit="switcharoo")

    def delete(self):
        if isinstance(self.object, praw.models.Submission):
            self.object.mod.remove()

    @property
    def permalink(self):
        return f"https://reddit.com{self.object.permalink}"

    @property
    def author(self):
        return self.object.author

    @property
    def created(self):
        return datetime.fromtimestamp(self.object.created_utc)
