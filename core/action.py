class BaseAction:
    def __init__(self, reddit):
        """
        :param reddit: PRAW Reddit instance
        """
        self.reddit = reddit

    def submission_lacks_context(self, submission):
        """The submission link does not have a ?context suffix"""
        pass

    def submission_linked_thread(self, submission):
        """The submission linked a thread, not a comment"""
        pass

    def comment_deleted(self, submission):
        """The submission links to a deleted comment"""
        pass

    def comment_has_no_link(self, submission):
        """The submission links to a comment with no link"""
        pass

    def comment_linked_wrong(self, submission):
        """The switcharoo comment is linked to the wrong thing"""
        pass

    def comment_lacks_context(self, submission):
        """The switcharoo comment link does not have the ?context suffix"""


class PrintAction(BaseAction):
    def submission_lacks_context(self, submission):
        print("https://www.reddit.com{} submission link does not have ?context".format(submission.permalink))

    def submission_linked_thread(self, submission):
        print("https://www.reddit.com{} linked to a thread, not a comment".format(submission.permalink))

    def comment_deleted(self, submission):
        print("https://www.reddit.com{} comment got deleted. Post should be removed.".format(submission.permalink))

    def comment_has_no_link(self, submission):
        print("https://www.reddit.com{} has no link in the comment".format(submission.permalink))

    def comment_linked_wrong(self, submission):
        print("https://www.reddit.com{} comment is not linked to the next level".format(submission.permalink))

    def comment_lacks_context(self, submission):
        print("https://www.reddit.com{} comment is correct link but did not have ?context in it".format(
            submission.permalink))
