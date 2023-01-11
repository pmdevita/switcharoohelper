import typing

import praw.exceptions
import prawcore.exceptions

from tests.mock.praw.models.redditor import MockRedditor
from tests.mock.praw.models.submission import MockSubmission
from tests.mock.praw.exceptions import ClientException, Forbidden


class MockComment:
    def __init__(self, comment_id, submission: MockSubmission, body, author, date, private=False, blocked=False):
        self.id = comment_id
        self.thread_id = submission.id
        self.body = body
        self.created_utc = date.timestamp()
        self.author = MockRedditor(author)
        self.private = private
        self.permalink = f"/r/{submission.subreddit}/comments/{submission.id}/_/{self.id}/"
        self.unrepliable_reason = None
        if blocked:
            self.body = "[unavailable]"
            self.unrepliable_reason = "NEAR_BLOCKER"

    def refresh(self):
        if super(MockComment, self).__getattribute__("private"):
            raise ClientException

    def get_link_and_context(self, context: typing.Optional[int]):
        if context:
            return f"https://reddit.com{self.permalink}?context={context}"
        else:
            return f"https://reddit.com{self.permalink}"

    def __getattr__(self, item):
        if not super(MockComment, self).__getattribute__("private"):
            return super(MockComment, self).__getattribute__(item)
        raise Forbidden
