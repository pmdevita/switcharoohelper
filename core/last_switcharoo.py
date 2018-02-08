import prawcore.exceptions

LIMIT = 5   # Can't imagine I would delete

"""
The submission dictionary looks like this
{"submission": praw submission object, "thread_id": reddit ID of thread switcharoo comment is in, 
"comment_id": reddit ID of the comment containing the switcharoo, "url": url of the r/switcharoo submission}
The submission is the submission to r/switcharoo and the comment is the 
switcharoo comment it links to
"""


class LastSwitcharoo:
    """Keeps a history of the last switcharoos, both good/verified and the last one
    in general"""
    def __init__(self, reddit, load=None):
        """

        :param reddit: PRAW Reddit instance
        :param load: Data from save() to resume object
        """
        self.reddit = reddit

        if load:
            self._good_roos = load["good_roos"]
            self._last_roos = load["last_roos"]
        else:
            self._good_roos = []
            self._last_roos = []

    def verify(self):
        """Check that if the last good or last submitted roo was deleted (by someone else), we don't link to it"""
        # Track the indicies to remove
        remove = []
        for i, roo in enumerate(self._good_roos):
            submission = self.reddit.submission(url=roo["url"])
            try:
                if hasattr(submission, "removed"):
                    if submission.removed:
                        remove.append(i)
                    else:
                        break
                else:   # We only need one good submission to continue
                    break
            except prawcore.exceptions.BadRequest:  # Failed request also indicates removed post
                remove.append(i)

        for i in sorted(remove, reverse=True):  # Work backwards to avoid updating indexes
            del self._good_roos[i]

        remove = []
        for i, roo in enumerate(self._last_roos):
            submission = self.reddit.submission(url=roo)
            if hasattr(submission, "removed"):
                if submission.removed:
                    remove.append(i)
                else:
                    break
            else:  # We only need one good submission to continue
                break
        for i in sorted(remove, reverse=True):  # Work backwards to avoid updating indexes
            del self._last_roos[i]

    def add_good(self, submission, thread_id, comment_id):
        """
    
        :param submission: submission dictionary
        :param thread_id: id of the switcharoo comment thread
        :param comment_id: id of the switcharoo comment
        :return: 
        """
        self._good_roos.insert(0, {"submission": submission, "url": "https://reddit.com{}".format(submission.permalink),
                                   "thread_id": thread_id, "comment_id": comment_id})
        # Remove any excess roos
        if len(self._good_roos) > LIMIT:
            del self._good_roos[LIMIT-1]

    def add_last(self, submission_url):
        self._last_roos.insert(0, submission_url)

        # Remove any excess roos
        if len(self._last_roos) > LIMIT:
            del self._last_roos[LIMIT-1]

    def last_good(self, index=0):
        if self._good_roos:
            return self._good_roos[index]
        else:
            return None

    def last_submitted(self, index=0):
        if self._last_roos:
            return self._last_roos[index]
        else:
            return None

    def save(self):
        """Returns object ready for jsonification"""
        good_roos = self._good_roos[:]
        last_roos = self._last_roos[:]
        for i in good_roos:
            i.pop("submission", None)
        return {"good_roos": good_roos, "last_roos": last_roos}
