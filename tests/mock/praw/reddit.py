from tests.mock.praw.models.submission import MockSubmission
from tests.mock.praw.models.comment import MockComment


class MockReddit:
    def __init__(self, username):
        self.username = username
        self._submissions: list[MockSubmission] = {}
        self._comments: list[MockComment] = {}

    def submission(self, submission_id: str, *args, **kwargs) -> MockSubmission:
        if submission_id not in self._submissions:
            submission = MockSubmission(submission_id, *args, **kwargs)
            self._submissions[submission_id] = submission
        return self._submissions[submission_id]

    def comment(self, comment_id, *args, **kwargs) -> MockComment:
        if comment_id not in self._comments:
            comment = MockComment(comment_id, *args, **kwargs)
            parent = kwargs.get("parent", None)
            if parent:
                if isinstance(parent, MockComment):
                    parent = parent.id
                self._comments[parent].replies.append(comment)
            self._comments[comment_id] = comment
        return self._comments[comment_id]
