from datetime import datetime, timedelta
from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, commit, Set, desc, set_sql_debug, \
    TransactionIntegrityError
from core.credentials import CredentialsLoader
from core.issues import issues_list, GetIssues
import praw
import prawcore.exceptions
import random
import string
from core.issues import issues_list, IssueTracker

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

    return creds['type']


class Switcharoo(db.Entity):
    id = PrimaryKey(int, auto=True)
    time = Required(datetime)
    submission_id = Optional(str, unique=True, nullable=True)
    thread_id = Optional(str)
    comment_id = Optional(str)
    context = Optional(int)
    link_post = Required(bool)
    issues = Set('Issues')
    requests = Optional('FixRequests', cascade_delete=True)

    def _link_reddit(self, reddit):
        self.reddit = reddit
        self._submission = None
        self._comment = None

    @property
    def submission(self):
        if not self.submission_id:
            return None
        if not self._submission:
            self._submission = self.reddit.submission(self.submission_id)
        return self._submission

    @property
    def comment(self):
        if not self._comment:
            self._comment = self.reddit.comment(self.comment_id)
        return self._comment

    def print(self):
        if self.submission_id:
            print(f"Roo {self.id}: {self.submission.title} by {self.submission.author}"
                  f" {datetime.fromtimestamp(self.submission.created_utc)}")
        else:
            print(f"Roo {self.id}: {self.comment.author}"
                  f" {datetime.fromtimestamp(self.comment.created_utc)}")


class Issues(db.Entity):
    type = Required(str)
    id = PrimaryKey(int)
    bad = Required(bool)
    switcharoos = Set(Switcharoo)


class FixRequests(db.Entity):
    roo = PrimaryKey(Switcharoo)
    time = Required(datetime)
    attempts = Required(int)

    def not_responded_in_days(self, days):
        return self.time < datetime.now() - timedelta(days=days)

    def set_attempts(self, value):
        with db_session:
            r = FixRequests[self.roo.id]
            r.attempts = value
            r.time = datetime.now()
            return r

    def reset(self):
        with db_session:
            r = FixRequests[self.roo.id]
            r.delete()
        return None


db_type = bind_db(db)

db.generate_mapping(create_tables=True)


# set_sql_debug(True)


class SwitcharooLog:
    def __init__(self, reddit):
        self.reddit = reddit

    def _link_reddit(self, roo):
        """Give DB entity a reference to the Reddit object"""
        roo._link_reddit(self.reddit)

    def _params_without_none(self, **kwargs):
        """Calling this allows us to have positional arguments that don't affect anything unless set by user"""
        base_params = kwargs
        params = {}
        for key in base_params:
            if base_params[key] is not None:
                params[key] = base_params[key]
        return params

    def add(self, submission_id, thread_id=None, comment_id=None, context=None, roo_issues=[], link_post=True,
            time=None):
        params = self._params_without_none(submission_id=submission_id, thread_id=thread_id, comment_id=comment_id,
                                           context=context, link_post=link_post, time=time)
        try:
            with db_session:
                n = Switcharoo(**params)
                for i in roo_issues:
                    n.issues.add(Issues[i.id])
        # Probably already in the db
        except TransactionIntegrityError:
            with db_session:
                n = select(s for s in Switcharoo if s.submission_id == submission_id).first()
                if n:
                    n.set(**params)
                    for i in roo_issues:
                        n.issues.add(Issues[i.id])
        return n

    def add_comment(self, thread_id, comment_id, context, time, roo_issues=[]):
        with db_session:
            n = Switcharoo(thread_id=thread_id, comment_id=comment_id, context=context, time=time, link_post=True,
                           submission_id=None)
            return n

    def update(self, roo, submission_id=None, thread_id=None, comment_id=None, context=None, roo_issues=[],
               remove_issues=[], time=None, reset_issues=False):
        params = self._params_without_none(submission_id=submission_id, thread_id=thread_id, comment_id=comment_id,
                                           context=context, time=None)

        with db_session:
            roo = Switcharoo[roo.id]
            roo.set(**params)
            if reset_issues:
                roo.issues.clear()
            else:
                for i in remove_issues:
                    roo.issues.remove(Issues[i.id])
            for i in roo_issues:
                roo.issues.add(Issues[i.id])

        return roo

    def get_roo(self, roo_id):
        with db_session:
            r = Switcharoo.get(id=roo_id)
            if r:
                self._link_reddit(r)
            return r

    def delete_roo(self, roo_id):
        with db_session:
            r = Switcharoo.get(id=roo_id)
            if r:
                r.delete()

    # Used to set offset to 1 to get last good but was never hooked up properly? IDK why it was done
    def last_good(self, before_roo=None, offset=0):
        time = before_roo.time if before_roo else datetime.now()
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if True not in s.issues.bad and s.link_post and s.time < time)
            # SQLite, I love you but why
            if db_type == "sqlite" and before_roo:
                q = q.filter(lambda x: x.id != before_roo.id)
            q = q.order_by(desc(Switcharoo.time)).limit(limit=1, offset=offset)
            if q:
                roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def next_good(self, after_roo, offset=0):
        time = after_roo.time
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if True not in s.issues.bad and s.link_post and s.time > time).limit(
                limit=1, offset=offset)
            if db_type == "sqlite":
                q = q.filter(lambda x: x.id != after_roo.id)
            if q:
                roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def last_submission(self, offset=0):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if Issues[issues_obj.submission_deleted] not in s.issues and Issues[
                issues_obj.submission_processing] not in s.issues).order_by(desc(Switcharoo.time)).limit(1,
                                                                                                         offset=offset)
            if q:
                roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def last(self):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo).order_by(desc(Switcharoo.time)).limit(1)
            if q:
                roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def search(self, thread_id=None, comment_id=None, submission_id=None, multiple=False):
        roo = None
        with db_session:
            query = select(s for s in Switcharoo)
            if thread_id:
                query = query.filter(lambda q: q.thread_id == thread_id)
            if comment_id:
                query = query.filter(lambda q: q.comment_id == comment_id)
            if submission_id:
                query = query.filter(lambda q: q.submission_id == submission_id)
            if query and not multiple:
                roo = query.first()
            else:
                roo = list(query)
        if roo:
            if multiple:
                for i in roo:
                    self._link_reddit(i)
            else:
                self._link_reddit(roo)
        return roo

    def get_roos(self, after_roo=None, after_time=None, limit=50):
        with db_session:
            query = select(s for s in Switcharoo if s.link_post)
            if after_roo or after_time:
                time = after_time if after_time else after_roo.time
                query = query.filter(lambda q: q.time < time)
            if db_type == "sqlite" and after_roo:
                query = query.filter(lambda x: x.id != after_roo.id)
            query = query.order_by(desc(Switcharoo.time)).limit(limit)
            roos = list(query)
        for roo in roos:
            self._link_reddit(roo)
        return roos


    def get_issues(self, roo):
        tracker = IssueTracker()
        with db_session:
            roo = Switcharoo[roo.id]
            query = roo.issues
            for issue in query:
                tracker[issue.id] = True
        return tracker

    def verify(self):
        """Verify roos until we have one last good roo"""
        with db_session:
            offset = 0
            good = False
            while not good:
                q = select(s for s in Switcharoo).order_by(desc(Switcharoo.time)).limit(10, offset)
                if len(q) == 0:
                    good = True
                    break
                for roo in q:
                    self._link_reddit(roo)
                    # Maybe use check_errors here instead now?
                    try:
                        # If this submission was in the middle of processing
                        if Issues[issues_obj.submission_processing] in roo.issues:
                            continue
                        if roo.submission.banned_by:
                            if not roo.submission.approved_by:
                                roo.issues.add(Issues[issues_obj.submission_deleted])
                                continue
                        if hasattr(roo.submission, "removed"):
                            if roo.submission.removed:
                                roo.issues.add(Issues[issues_obj.submission_deleted])
                                continue
                        # If author is none submission was deleted
                        if roo.submission.author is None:
                            roo.issues.add(Issues[issues_obj.submission_deleted])
                            continue
                    except prawcore.exceptions.BadRequest:
                        roo.issues.add(Issues[issues_obj.submission_deleted])
                        continue
                    if roo.link_post:
                        try:
                            roo.comment.refresh()
                        except (praw.exceptions.ClientException, praw.exceptions.PRAWException):
                            roo.issues.add(Issues[issues_obj.comment_deleted])
                            continue
                    # This one has passed the tests, should be good to go
                    good = True
                    break
                offset += 10

    def sync_issues(self):
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

    def check_request(self, roo):
        with db_session:
            roo = Switcharoo[roo.id]
            q = FixRequests.get(roo=roo)
            return q
    
    def update_request(self, roo, time=None, requests=1):
        with db_session:
            roo = Switcharoo[roo.id]
            q = FixRequests.get(roo=roo)
            if q:
                q.set(**self._params_without_none(time=time, requests=requests))
            else:
                r = FixRequests(roo=roo, time=datetime.now(), attempts=requests)
                return r

    def reset_request(self, roo=None, request=None):
        key = None
        if roo:
            key = roo.id
        elif request:
            key = request.roo.id
        else:
            raise Exception("No object passed")
        with db_session:
            r = FixRequests.get(roo=key)
            if r:
                r.delete()
        return None


if __name__ == '__main__':
    log = SwitcharooLog("asdf")
    # for i in range(5):
    #     issues = [random.randrange(12) for i in range(random.randrange(4))]
    #     log.add(''.join(random.sample(string.ascii_letters, 7)), ''.join(random.sample(string.ascii_letters, 7)),
    #                     ''.join(random.sample(string.ascii_letters, 7)), random.randrange(5), issues)
    print(log.last_good(), log.last())
