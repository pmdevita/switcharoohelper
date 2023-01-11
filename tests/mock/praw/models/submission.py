import prawcore
from datetime import datetime

from tests.mock.requests import MockResponse
from tests.mock.praw.models.redditor import MockRedditor


class MockSubmission:
    def __init__(self, submission_id, link_post: bool, body, date: datetime, author: str, subreddit, title="Roo Title", private=False):
        self.id = submission_id
        self.distinguished = False
        self.is_self = not link_post
        self.domain = "reddit.com"
        self.title = title
        self.author = MockRedditor(author)
        self.removed_by_category = None
        self.banned_at_utc = None
        self.banned_by = None
        self.selftext = ""
        self.subreddit = subreddit
        self.created_utc = date.timestamp()
        self.private = private
        self.permalink = f"/r/{subreddit}/comments/{submission_id}/slug"
        if self.is_self:
            self.body = body
        else:
            self.url = body

    def __getattribute__(self, item):
        if not super(MockSubmission, self).__getattribute__("private"):
            return super(MockSubmission, self).__getattribute__(item)
        raise prawcore.exceptions.Forbidden(MockResponse(403))
