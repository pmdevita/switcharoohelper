from datetime import datetime, timedelta
from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, commit, Set, desc, set_sql_debug, \
    TransactionIntegrityError, count
from core.credentials import CredentialsLoader
from core.issues import issues_list, GetIssues
import praw
import praw.exceptions
import prawcore.exceptions
import random
import string
from core.issues import issues_list, IssueTracker
from core.credentials import CredentialsLoader

creds = CredentialsLoader.get_credentials()['general']
DRY_RUN = creds['dry_run'].lower() != "false"

issues_obj = GetIssues.get()

db = Database()


def bind_db(db):
    creds = CredentialsLoader.get_credentials()['database']

    if creds['type'] == 'sqlite':
        db_file = creds.get('db_file', "database.sqlite")
        db.bind(provider='sqlite', filename='../' + db_file, create_db=True)
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
    user = Optional(str, max_len=21)
    subreddit = Optional(str, max_len=21)
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
        if not self.comment_id:
            return None
        if not self._comment:
            self._comment = self.reddit.comment(self.comment_id)
        return self._comment

    def print(self):
        try:
            if self.submission_id:
                print(f"Roo {self.id}: {self.submission.title} by {self.submission.author}"
                      f" {datetime.fromtimestamp(self.submission.created_utc)}")
            else:
                print(f"Roo {self.id}: {self.comment.author if self.comment.author else ''}"
                      f" {datetime.fromtimestamp(self.comment.created_utc if self.comment.author else '')}")
        except praw.exceptions.ClientException:
            print(f"Roo {self.id}")



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


class PrivatedSubs(db.Entity):
    subreddit = PrimaryKey(str, max_len=21)
    allowed = Optional(bool)
    expiration = Optional(datetime)
    update_requested = Required(bool)

    def is_expired(self):
        if self.expiration:
            return datetime.now() > self.expiration
        else:
            # If this has no expiration set, it never expires
            return False

    def reset(self):
        with db_session:
            p = PrivatedSubs[self.subreddit]
            p.delete()
        return None


class UserFlair(db.Entity):
    user = PrimaryKey(str, max_len=21)
    roos = Required(int, default=0)
    fixes = Required(int, default=0)

# set_sql_debug(True)


class SwitcharooLog:
    def __init__(self, reddit):
        self.reddit = reddit
        self.stats = SwitcharooStats(reddit)
        self.db = db
        self.db_type = bind_db(db)
        self.db.generate_mapping(create_tables=True)

    def _link_reddit(self, roo):
        """Give DB entity a reference to the Reddit object"""
        roo._link_reddit(self.reddit)

    def __del__(self):
        self.db.disconnect()

    def unbind(self):
        # Kind of a nasty hack
        self.db.disconnect()
        self.db.provider = None
        self.db.schema = None

    def _params_without_none(self, **kwargs):
        """Calling this allows us to have positional arguments that don't affect anything unless set by user"""
        base_params = kwargs
        params = {}
        for key in base_params:
            if base_params[key] is not None:
                params[key] = base_params[key]
        return params

    def add(self, submission_id, thread_id=None, comment_id=None, context=None, roo_issues=[], link_post=True,
            time=None, user=None, subreddit=None):
        params = self._params_without_none(submission_id=submission_id, thread_id=thread_id, comment_id=comment_id,
                                           context=context, link_post=link_post, time=time, user=user,
                                           subreddit=subreddit)
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
            for i in roo_issues:
                n.issues.add(Issues[i.id])
            return n

    def update(self, roo, submission_id=None, thread_id=None, comment_id=None, context=None, roo_issues=[],
               remove_issues=[], time=None, reset_issues=False, user=None, subreddit=None):
        if DRY_RUN:
            return roo
        params = self._params_without_none(submission_id=submission_id, thread_id=thread_id, comment_id=comment_id,
                                           context=context, time=time, user=user, subreddit=subreddit)

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
    def last_good(self, before_roo=None, offset=0, user=None, all=False):
        time = before_roo.time if before_roo else datetime.now()
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if True not in s.issues.bad and s.link_post and s.time < time)
            # SQLite, I love you but why
            if self.db_type == "sqlite" and before_roo:
                q = q.filter(lambda x: x.id != before_roo.id)
            if user:
                q = q.filter(lambda x: x.user == user)
            q = q.order_by(desc(Switcharoo.time)).limit(limit=1, offset=offset)
            if q:
                if all:
                    roo = list(q)
                else:
                    roo = q[0]
        if roo:
            if all:
                for i in roo:
                    self._link_reddit(i)
            else:
                self._link_reddit(roo)
        return roo

    def next_good(self, after_roo, offset=0):
        time = after_roo.time
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if True not in s.issues.bad and s.link_post and s.time > time).limit(
                limit=1, offset=offset)
            if self.db_type == "sqlite":
                q = q.filter(lambda x: x.id != after_roo.id)
            if q:
                roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def last_submission(self, offset=0):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if True not in s.issues.bad and Issues[
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

    def search(self, thread_id=None, comment_id=None, submission_id=None, after_time=None, multiple=False, oldest=False):
        roo = None
        with db_session:
            query = select(s for s in Switcharoo)
            if thread_id:
                query = query.filter(lambda q: q.thread_id == thread_id)
            if comment_id:
                query = query.filter(lambda q: q.comment_id == comment_id)
            if submission_id:
                query = query.filter(lambda q: q.submission_id == submission_id)
            if after_time:
                query = query.filter(lambda q: q.time < after_time)
            if oldest:
                query = query.order_by(Switcharoo.time)
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

    def get_roos(self, after_roo=None, after_time=None, limit=50, meta=False):
        with db_session:
            query = select(s for s in Switcharoo)
            if not meta:
                query = query.filter(lambda x: x.link_post)
            if after_roo or after_time:
                time = after_time if after_time else after_roo.time
                query = query.filter(lambda q: q.time < time)
            if self.db_type == "sqlite" and after_roo:
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

    # has to be passed like this to avoid circular imports, hopefully some restructuring later fixes this
    def verify(self, reprocess, action, mute=False):
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
                    tracker = reprocess(self.reddit, roo, self, action, mute=mute, verbose=False)
                    if tracker:
                        if not tracker.has_bad_issues():
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

    def oldest_good(self, offset=0):
        with db_session:
            q = select(s for s in Switcharoo if True not in s.issues.bad and s.link_post)
            q = q.order_by(Switcharoo.time).limit(limit=1, offset=offset)
            if q:
                roo = q[0]
                self._link_reddit(roo)
                return roo
        return None

    def check_privated_sub(self, subreddit):
        with db_session:
            q = PrivatedSubs.get(subreddit=subreddit)
            return q

    def update_privated_sub(self, subreddit, expiration=None, allowed=None, update_requested=None):
        with db_session:
            p = PrivatedSubs.get(subreddit=subreddit)
            if p:
                p.set(**self._params_without_none(expiration=expiration, allowed=allowed,
                                                  update_requested=update_requested))
            else:
                p = PrivatedSubs(subreddit=subreddit, expiration=expiration, allowed=allowed,
                                 update_requested=update_requested)

    def check_user_flair(self, user):
        with db_session:
            f = UserFlair.get(user=user)
            return f

    def update_user_flair(self, user, roos=None, fixes=None):
        with db_session:
            f = UserFlair.get(user=user)
            if f:
                f.set(**self._params_without_none(roos=roos, fixes=fixes))
            else:
                f = UserFlair(user=user, **self._params_without_none(roos=roos, fixes=fixes))


class SwitcharooStats:
    def __init__(self, reddit):
        self.reddit = reddit

    def num_of_good_roos(self, before=None, after=None, user=None, all_users=False):
        roo = None
        with db_session:
            if all_users and not user:
                q = select((s.user, count(s)) for s in Switcharoo if True not in s.issues.bad and s.link_post)
            else:
                q = select(s for s in Switcharoo if True not in s.issues.bad and s.link_post)
            if before:
                q = q.filter(lambda x: x.time < before)
            if after:
                q = q.filter(lambda x: x.time > after)
            if user:
                q = q.filter(lambda x: x.user == user)
            if all_users and not user:
                return list(q)
            else:
                return count(q)

    def all_user_flair(self):
        with db_session:
            return list(select(u for u in UserFlair))


if __name__ == '__main__':
    log = SwitcharooLog("asdf")
    # for i in range(5):
    #     issues = [random.randrange(12) for i in range(random.randrange(4))]
    #     log.add(''.join(random.sample(string.ascii_letters, 7)), ''.join(random.sample(string.ascii_letters, 7)),
    #                     ''.join(random.sample(string.ascii_letters, 7)), random.randrange(5), issues)
    print(log.last_good(), log.last())
