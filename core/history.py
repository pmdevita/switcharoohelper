from datetime import date
from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, commit, Set, desc, set_sql_debug
from core.credentials import CredentialsLoader
from core.issues import issues_list, GetIssues
import praw
import prawcore.exceptions
import random, string

issues_obj = GetIssues.get()

db = Database()

def bind_db(db):
    creds = CredentialsLoader.get_credentials()['database']

    if creds['type'] == 'sqlite':
        db.bind(provider='sqlite', filename='../database.sqlite', create_db=True)
    elif creds['type'] == 'mysql':
        # Check for SSL arguments
        ssl = {}
        if creds.get('ssl-ca', None):
            ssl['ssl'] = {'ca': creds['ssl-ca'], 'key': creds['ssl-key'], 'cert': creds['ssl-cert']}

        db.bind(provider="mysql", host=creds['host'], user=creds['username'], password=creds['password'],
                db=creds['database'], ssl=ssl, port=int(creds.get('port', 3306)))
    else:
        raise Exception("No database configuration")

class Switcharoo(db.Entity):
    id = PrimaryKey(int, auto=True)
    submission_id = Required(str)
    thread_id = Optional(str)
    comment_id = Optional(str)
    context = Optional(int)
    issues = Set('Issues')

    def _link_reddit(self, reddit):
        self.reddit = reddit
        self._submission = None
        self._comment = None

    @property
    def submission(self):
        if not self._submission:
            self._submission = self.reddit.submission(self.submission_id)
        return self._submission

    @property
    def comment(self):
        if not self._comment:
            self._comment = self.reddit.comment(self.comment_id)
        return self._comment


class Issues(db.Entity):
    type = Required(str)
    id = PrimaryKey(int)
    bad = Required(bool)
    switcharoos = Set(Switcharoo)

bind_db(db)

db.generate_mapping(create_tables=True)
# set_sql_debug(True)

class SwitcharooLog:
    def __init__(self, reddit):
        self.reddit = reddit

    def _link_reddit(self, roo):
        """Give DB entity a reference to the Reddit object"""
        roo._link_reddit(self.reddit)

    def _params_without_none(self, **kwargs):
        base_params = kwargs
        params = {}
        for key in base_params:
            if base_params[key] is not None:
                params[key] = base_params[key]
        return params

    def add(self, submission_id, thread_id=None, comment_id=None, context=None, roo_issues=[]):
        params = self._params_without_none(submission_id=submission_id, thread_id=thread_id, comment_id=comment_id,
                                           context=context)

        with db_session:
            n = Switcharoo(**params)
            for i in roo_issues:
                n.issues.add(Issues[i])
        return n

    def update(self, roo, submission_id=None, thread_id=None, comment_id=None, context=None, roo_issues=[]):
        params = self._params_without_none(submission_id=submission_id, thread_id=thread_id, comment_id=comment_id,
                                           context=context)

        with db_session:
            roo = Switcharoo[roo.id]
            roo.set(**params)
            for i in roo_issues:
                roo.issues.add(Issues[i])

        return roo



    def last_good(self, offset=0):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if True not in s.issues.bad).order_by(desc(Switcharoo.id)).limit(1, offset=offset)
            if q:
                roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def last_submission(self, offset=0):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if Issues[issues_obj.submission_deleted] not in s.issues).order_by(desc(Switcharoo.id)).limit(1, offset=offset)
            if q:
                roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def last(self):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo).order_by(desc(Switcharoo.id)).limit(1)
            if q:
                roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def search(self, thread_id, comment_id):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if s.thread_id == thread_id and s.comment_id == comment_id)
            if q:
                roo = q.first()
        if roo:
            self._link_reddit(roo)
        return roo


    def verify(self):
        """Verify roos until we have one last good roo"""
        with db_session:
            counter = 0
            good = False
            while not good:
                q = select(s for s in Switcharoo).order_by(desc(Switcharoo.id)).limit(10, counter)
                if len(q) == 0:
                    good = True
                    break
                for roo in q:
                    self._link_reddit(roo)
                    try:
                        if roo.submission.banned_by:
                            if not roo.submission.approved_by:
                                roo.issues.add(Issues[issues_obj.submission_deleted])
                                continue
                        if hasattr(roo.submission, "removed"):
                            if roo.submission.removed:
                                roo.issues.add(Issues[issues_obj.submission_deleted])
                                continue
                    except prawcore.exceptions.BadRequest:
                        roo.issues.add(Issues[issues_obj.submission_deleted])
                        continue

                    try:
                        roo.comment.refresh()
                    except (praw.exceptions.ClientException, praw.exceptions.PRAWException):
                        roo.issues.add(Issues[issues_obj.comment_deleted])
                        continue
                    # This one has passed the tests, should be good to go
                    good = True
                    break
                counter += 10


    def sync_issues(self):
        from core.issues import issues_list
        with db_session:
            for i, issue_type in enumerate(issues_list):
                q = select(r for r in Issues if r.type == issue_type['type'])
                q = q.first()
                if q:
                    if q.id != i:
                        q.id = i
                    if q.bad != issue_type['bad']:
                        q.bad = issue_type['bad']
                else:
                    new = Issues(type=issue_type['type'], id=i, bad=issue_type['bad'])
            commit()

if __name__ == '__main__':
    log = SwitcharooLog("asdf")
    # for i in range(5):
    #     issues = [random.randrange(12) for i in range(random.randrange(4))]
    #     log.add(''.join(random.sample(string.ascii_letters, 7)), ''.join(random.sample(string.ascii_letters, 7)),
    #                     ''.join(random.sample(string.ascii_letters, 7)), random.randrange(5), issues)
    print(log.last_good(), log.last())