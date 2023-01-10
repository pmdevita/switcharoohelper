# Regular issues can be fixed, bad issues are unsolvable and require removing the roo

issues_list = [
    # The submission link does not have a ?context suffix
    {"type": "submission_lacks_context", "bad": True},

    # The submission linked a thread, not a comment
    {"type": "submission_linked_thread", "bad": True},

    # The submission links to a deleted comment
    {"type": "comment_deleted", "bad": True},

    # The submission links to a comment with no link
    {"type": "comment_has_no_link", "bad": True},

    # The switcharoo comment is linked to the wrong thing
    {"type": "comment_linked_wrong", "bad": False},

    # The switcharoo comment link does not have the ?context suffix
    {"type": "comment_lacks_context", "bad": False},

    # The switcharoo was correctly linked to a bad roo. Ask for edit to new one
    {"type": "comment_linked_bad_roo", "bad": False},

    # The switcharoo tried to have multiple sections of url params (multiple '?')
    {"type": "submission_multiple_params", "bad": True},

    # The switcharoo had a slash at the end of the params
    {"type": "submission_link_final_slash", "bad": True},

    # The submission links outside of reddit
    {"type": "submission_not_reddit", "bad": True},

    # The submission is a meta post when it should have been a link
    {"type": "submission_is_meta", "bad": True},

    # The submission has linked the post on r/switcharoo, not the link
    {"type": "submission_linked_post", "bad": True},

    # The r/switcharoo submission has been deleted
    {"type": "submission_deleted", "bad": True},

    # The submission has not been fully processed yet
    {"type": "submission_processing", "bad": False},

    # The submission's URL is malformed in some unknown way
    {"type": "submission_bad_url", "bad": True},

    # The user ignored the bot and did not fix the roo
    {"type": "user_noncompliance", "bad": True},

    # The user who submitted this roo is not the user who wrote the comment
    {"type": "user_mismatch", "bad": True},

    # This subreddit is privated
    {"type": "subreddit_privated", "bad": True}
]


class Issues:
    def __init__(self):
        for i, issue in enumerate(issues_list):
            self.__setattr__(issue['type'], i)


class BadIssues:
    def __init__(self):
        for i in issues_list:
            self.__setattr__(i['type'], i['bad'])


class GetIssues:
    issues = None
    bad_issues = None

    @classmethod
    def get(cls):
        if not cls.issues:
            cls.issues = Issues()
        return cls.issues

    @classmethod
    def bad(cls):
        if not cls.bad:
            cls.bad = BadIssues()
        return cls.bad


class Issue:
    def __init__(self, id, name, bad):
        self.id = id
        self.name = name
        self.bad = bad
        self.has_issue = False  # Is there a better name for this?

    def __get__(self, obj, obj_type=None):
        return obj.has_issue

    def __set__(self, obj, value):
        obj.has_issue = value

    def __str__(self):
        return f"Issue-{self.name} {self.has_issue}"


class IssueTracker:
    def __init__(self):
        super(IssueTracker, self).__setattr__("_setup", True)
        self.issue_dict = {}
        self.issues = []
        for index, i in enumerate(issues_list):
            issue = Issue(index, i['type'], i['bad'])
            self.issue_dict[i['type']] = issue
            self.issues.append(issue)
        self._setup = False

    def has_issues(self):
        for i in super(IssueTracker, self).__getattribute__("issues"):
            if i.has_issue:
                return True
        return False

    def has_bad_issues(self):
        for i in super(IssueTracker, self).__getattribute__("issues"):
            if i.has_issue and i.bad:
                return True
        return False

    def diff(self, other: "IssueTracker"):
        issues = super(IssueTracker, self).__getattribute__("issues")
        other_issues = super(IssueTracker, other).__getattribute__("issues")
        added = []
        removed = []
        for i in range(len(issues)):
            if issues[i].has_issue and not other_issues[i].has_issue:
                removed.append(other_issues[i])
            elif not issues[i].has_issue and other_issues[i].has_issue:
                added.append(other_issues[i])
        return added, removed

    def __getattr__(self, item):
        return self.issue_dict[item].has_issue

    def __setattr__(self, key, value):
        if super(IssueTracker, self).__getattribute__("_setup"):
            return super(IssueTracker, self).__setattr__(key, value)
        else:
            self.issue_dict[key].has_issue = value

    def __setitem__(self, key, value):
        self.issues[key].has_issue = value

    def __contains__(self, item):
        return self.issue_dict[item].has_issue

    def __iter__(self):
        return IssueTrackerIter(super(IssueTracker, self).__getattribute__("issues"))

    def __len__(self):
        size = 0
        for i in super(IssueTracker, self).__getattribute__("issues"):
            if i.has_issue:
                size += 1
        return size

    def __eq__(self, other: "IssueTracker"):
        added, removed = self.diff(other)
        return len(added) == 0 and len(removed) == 0

    def __repr__(self):
        issue_string = " ".join([i.name for i in self.issues if i.has_issue])
        return f"IssueTracker({issue_string})"


class IssueTrackerIter:
    def __init__(self, issues):
        self.index = 0
        self.issues = issues

    def __iter__(self):
        return self

    def __next__(self):
        while self.index < len(self.issues):
            if self.issues[self.index].has_issue:
                self.index += 1
                return self.issues[self.index - 1]
            else:
                self.index += 1
        raise StopIteration


if __name__ == '__main__':
    it = IssueTracker()
    print(it.submission_processing)
    it.submission_processing = True
    print(it.submission_processing)
