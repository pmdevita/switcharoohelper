import prawcore.exceptions

"""
Switcharoos "graduate" out of the good roo log and into the old roo log. 
This allows us to track data on them for future responses.
"""

LIMIT = 10

class Switcharoo:
    def __init__(self, thread_id, comment_id, comment_url, submission_url, submission_id, submission=None):
        self.thread_id = thread_id
        self.comment_id = comment_id
        self.comment_url = comment_url
        self.submission_url = submission_url
        self.submission_id = submission_id
        if submission:
            self.submission = submission

    """Support for deprecated access"""
    def __getitem__(self, item):
        self.__getattribute__(item)

    def __str__(self):
        return self.submission_id

    @classmethod
    def load(cls, properties):
        return cls(properties["thread_id"], properties["comment_id"], properties["comment_url"],
                          properties["submission_url"], properties["submission_id"])

    def save(self):
        return {"thread_id": self.thread_id, "comment_id": self.comment_id, "comment_url": self.comment_url,
                "submission_url": self.submission_url, "submission_id": self.submission_id}

# TODO: Create a SwitcharooLog class and derive the New and Settled versions from it

class SwitcharooLog:
    """Keeps a log of the switcharoos, both good/verified and the last one
    in general. Used to give correct links and to find place in submissions log"""
    def __init__(self, reddit, load=None):
        """

        :param reddit: PRAW Reddit instance
        :param load: Data from save() to resume object
        """
        self.reddit = reddit

        if load:
            self.good_roos = []
            for roo in load["good_roos"]:
                self.good_roos.append(Switcharoo.load(roo))
            self._last_roos = load["last_roos"]
            if "old_roos" in load:
                self.old_roos = []
                for roo in load["old_roos"]:
                    self.old_roos.append(Switcharoo.load(roo))
                self.old_good_roos = []
                for roo in load["old_good_roos"]:
                    self.old_good_roos.append(Switcharoo.load(roo))
                self.old_time = load['old_time']
            else:
                self.old_roos = []
                self.old_good_roos = []
                self.old_time = 0
        else:
            self.good_roos = []    # List of all good roos
            self._last_roos = []    # List of
            self.old_roos = []
            self.old_good_roos = []
            self.old_time = 0

    def verify(self):
        """Check that if the last good or last submitted roo was deleted (by someone else), we don't link to it"""
        # Track the indices to remove
        # TODO: Add check for deleted comments
        remove = []
        for i, roo in enumerate(self.good_roos):
            submission = self.reddit.submission(roo.submission_id)
            try:
                if submission.author is None:
                    remove.append(i)
                    continue
                if submission.banned_by:
                    if not submission.approved_by:
                        remove.append(i)
                        continue
                if hasattr(submission, "removed"):
                    if submission.removed:
                        remove.append(i)
                        continue
                break   # This one passed the test, we are done here
            except prawcore.exceptions.BadRequest:  # Failed request also indicates removed post
                remove.append(i)

        for i in sorted(remove, reverse=True):  # Work backwards to avoid updating indexes
            del self.good_roos[i]

        # remove = []     # This may not be a good idea since a roo may have linked to a deleted one of these
        # for i, roo in enumerate(self._last_roos):
        #     submission = self.reddit.submission(url=roo)
        #     try:
        #         if submission.author is None:
        #             remove.append(i)
        #             continue
        #         if submission.banned_by:
        #             if not submission.approved_by:
        #                 remove.append(i)
        #                 continue
        #         if hasattr(submission, "removed"):
        #             if submission.removed:
        #                 remove.append(i)
        #                 continue
        #         break   # This one passed the test, we are done here
        #     except prawcore.exceptions.BadRequest:  # Failed request also indicates removed post
        #         remove.append(i)
        #
        # for i in sorted(remove, reverse=True):  # Work backwards to avoid updating indexes
        #     del self._last_roos[i]

    # def verify_settled(self):
    #     """Verify roos for linking on the tail of the roo log. We need at least one good one for linking to"""
    #     # Track the indicies to remove
    #     remove = []
    #     for i, roo in enumerate(reversed(self._good_roos)):
    #         # reverse the index since we are reading backwards
    #         index = len(self._good_roos) - 1 - i
    #         submission = self.reddit.submission(url=roo["submission_url"])
    #         try:
    #             if submission.author is None:
    #                 remove.append(index)
    #             elif hasattr(submission, "removed"):
    #                 if submission.removed:
    #                     remove.append(index)
    #             else:  # We only need one good submission to continue
    #                 break
    #         except prawcore.exceptions.BadRequest:  # Failed request also indicates removed post
    #             remove.append(index)
    #
    #     for i in sorted(remove, reverse=True):  # Work backwards to avoid updating indexes
    #         del self._good_roos[index]
    #
    #     remove = []
    #     for i, roo in enumerate(reversed(self._last_roos)):
    #         # reverse the index since we are reading backwards
    #         index = len(self._good_roos) - 1 - i
    #         submission = self.reddit.submission(url=roo)
    #         if submission.author is None:
    #             remove.append(index)
    #         elif hasattr(submission, "removed"):
    #             if submission.removed:
    #                 remove.append(index)
    #         else:  # We only need one good submission to continue
    #             break
    #     for i in sorted(remove, reverse=True):  # Work backwards to avoid updating indexes
    #         del self._last_roos[index]



    def add_good(self, submission, thread_id, comment_id):
        """
    
        :param submission: submission dictionary
        :param thread_id: id of the switcharoo comment thread
        :param comment_id: id of the switcharoo comment
        :return: 
        """
        self.good_roos.insert(0, Switcharoo(thread_id, comment_id, submission.url,
                                             "https://reddit.com{}".format(submission.permalink), submission.id,
                                            submission))

        # Move old roos to old_roos and remove from good_roos
        if len(self.good_roos) > LIMIT:
            self.old_roos.insert(0, self.good_roos[len(self.good_roos) - 1])
            del self.good_roos[len(self.good_roos) - 1]

    def add_last(self, submission_url):
        self._last_roos.insert(0, submission_url)

        # Remove any excess roos
        if len(self._last_roos) > LIMIT:
            del self._last_roos[len(self._last_roos)-1]

    def add_old_good(self, submission, thread_id, comment_id):
        """

        :param submission: submission dictionary
        :param thread_id: id of the switcharoo comment thread
        :param comment_id: id of the switcharoo comment
        :return:
        """
        self.old_good_roos.insert(0, Switcharoo(thread_id, comment_id, submission.url,
                                            "https://reddit.com{}".format(submission.permalink), submission.id,
                                            submission))

        if len(self.old_good_roos) > LIMIT:
            del self.old_good_roos[len(self.old_good_roos) - 1]

    def last_good(self, index=0):
        if self.good_roos:
            return self.good_roos[index]
        else:
            return None

    def last_submitted(self, index=0):
        if self._last_roos:
            return self._last_roos[index]
        else:
            return None

    def last_old(self, index=0):
        if self.old_roos:
            return self.old_roos[index]
        else:
            return None

    def last_old_good(self, index=0):
        if self.old_good_roos:
            return self.old_good_roos[index]
        else:
            return None

    def save(self):
        """Returns object ready for jsonification"""
        good_roos = []
        for i in self.good_roos:
            good_roos.append(i.save())
        old_roos = []
        for i in self.old_roos:
            old_roos.append(i.save())
        old_good_roos = []
        for i in self.old_good_roos:
            old_good_roos.append(i.save())
        return {"good_roos": good_roos, "last_roos": self._last_roos, "old_roos": old_roos,
                "old_time": self.old_time, "old_good_roos": old_good_roos}

class OldSwitcharooLog:
    def __init__(self, switcharoolog):
        self.switcharoolog = switcharoolog

    def add_last(self, roo):
        pass

    def add_good(self, submission, thread_id, comment_id):
        self.switcharoolog.add_old_good(submission, thread_id, comment_id)

    def last_good(self, index=0):
        return self.switcharoolog.last_old_good(index)

    def last_submitted(self):
        return None, None