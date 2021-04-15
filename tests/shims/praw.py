import praw.exceptions
import prawcore.exceptions


class Reddit:
    def __init__(self, username):
        self.username = username
        self.submissions = {}
        self.comments = {}

    def submission(self, id, *args, **kwargs):
        if id not in self.submissions:
            submission = Submission(id, *args, **kwargs)
            self.submissions[id] = submission
        return self.submissions[id]

    def comment(self, id, *args, **kwargs):
        if id not in self.comments:
            comment = Comment(id, *args, **kwargs)
            self.comments[id] = comment
        return self.comments[id]


class Submission:
    def __init__(self, id, link_post: bool, body, date, author: str, subreddit, title="Roo Title", private=False):
        self.id = id
        self.distinguished = False
        self.is_self = not link_post
        self.domain = "reddit.com"
        self.title = title
        self.author = Redditor(author)
        self.removed_by_category = None
        self.banned_at_utc = None
        self.banned_by = None
        self.selftext = ""
        self.subreddit = subreddit
        self.created_utc = date.timestamp()
        self.private = private
        self.permalink = f"/r/{subreddit}/comments/{id}/slug"
        if self.is_self:
            self.body = body
        else:
            self.url = body

    def __getattribute__(self, item):
        if not super(Submission, self).__getattribute__("private"):
            return super(Submission, self).__getattribute__(item)
        raise prawcore.exceptions.Forbidden(Response(403))


class Comment:
    def __init__(self, id, body, author, date, private=False):
        self.id = id
        self.body = body
        self.created_utc = date.timestamp()
        self.author = Redditor(author)
        self.private = private

    def refresh(self):
        if super(Comment, self).__getattribute__("private"):
            raise praw.exceptions.ClientException

    def __getattr__(self, item):
        if not super(Comment, self).__getattr__("private"):
            return super(Comment, self).__getattr__(item)
        raise prawcore.exceptions.Forbidden


class Redditor:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __eq__(self, other: 'Redditor'):
        return self.name == other.name


class Response:
    def __init__(self, status_code):
        self.status_code = status_code