import prawcore
from datetime import datetime

from tests.mock.requests import MockResponse
from tests.mock.praw.models.redditor import MockRedditor


class MockSubmission:
    def __init__(self, submission_id, link_post: bool, content, date: datetime, author: str, subreddit, title="Roo Title", private=False):
        self.id = submission_id
        self.distinguished = False
        self.is_self = not link_post
        self._content = content
        self.domain = "reddit.com"
        self.title = title
        self.author = MockRedditor(author)
        self.removed = False
        self.removed_by_category = None
        self.banned_at_utc = None
        self.banned_by = None
        self.subreddit = subreddit
        self.created_utc = date.timestamp()
        self.private = private
        self.permalink = f"/r/{subreddit}/comments/{submission_id}/slug"
        self.mod = MockSubmissionModerator(self)

    @property
    def url(self):
        if self.is_self:
            return ""
        return self._content

    @url.setter
    def url(self, value):
        self._content = value

    @property
    def selftext(self):
        if not self.is_self:
            return ""
        return self._content

    @selftext.setter
    def selftext(self, value):
        self._content = value

    def __getattribute__(self, item):
        if not super(MockSubmission, self).__getattribute__("private"):
            return super(MockSubmission, self).__getattribute__(item)
        raise prawcore.exceptions.Forbidden(MockResponse(403))


class MockSubmissionModerator:
    def __init__(self, submission):
        self._submission = submission

    def remove(self):
        self._submission.removed_by_category = "deleted"
        # I don't think this always happens??? It didn't during the
        # 2022 outage
        # self._submission.selftext = "[deleted]"
        self._submission.removed = True
