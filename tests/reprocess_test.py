from datetime import datetime

from switcharoo.config.issues import IssueTracker
from switcharoo.config import constants as consts


class TestReprocess:
    # Text posts are only checked if they are a roo on their first check, if they
    # are edited later, that is ignored to avoid random spam. However, there was a
    # bug where if this happened, the post would not also get marked as deleted and
    # switcharoohelper thought it was still a good post and tried to look up new
    # roos based on its ID. This caused the 6 month outage of 2022.
    def test_meta_deleted_later(self, reddit, last_switcharoo, action, first_roo):
        import switcharoo.core.process
        second = reddit.submission("zbcdf", link_post=False, content=None,
                                   date=datetime(2022, 8, 1, 1), author="otheruser",
                                   subreddit="subreddit2")
        second_comment = reddit.comment("12346", second,
                                        f"Ah the old reddit [switcharoo]"
                                        f"({first_roo.get_link_and_context(3)})",
                                        "user1",
                                        date=datetime(2022, 8, 1, 2))
        second_submission = reddit.submission("zbcdg", link_post=False, date=datetime(2022, 8, 1, 3), author="user1",
                                              content="haha definitely not a roo!!!!",
                                              subreddit="switcharoo")
        switcharoo.core.process.process(reddit, second_submission, last_switcharoo, action)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        assert issues == model_issues
        second_submission.selftext = f"[Sike!]({second_comment.get_link_and_context(3)})"
        second_submission.mod.remove()
        switcharoo.core.process.reprocess(reddit, last_switcharoo.get_roo(submission_id=second_submission.id),
                                          last_switcharoo, action, stage=consts.ALL_ROOS)
        issues = last_switcharoo.get_issues(last_switcharoo.get_roo(submission_id=second_submission.id))
        model_issues = IssueTracker()
        model_issues.submission_deleted = True
        assert issues == model_issues
        assert issues.has_bad_issues()

