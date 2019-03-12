from datetime import date
from pony.orm import Database, PrimaryKey, Required, Optional, db_session, select, commit, Set, desc, set_sql_debug
from core.credentials import CredentialsLoader
from core.issues import issues, issues_dict
import random, string

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
    thread_id = Required(str)
    comment_id = Required(str)
    context = Required(int)
    submission_id = Required(str)
    issues = Set('Issues')

    def _link_reddit(self, reddit):
        self.reddit = reddit

    @property
    def submission(self):
        if not self.submission:
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

    def add(self, submission_id, thread_id, comment_id, context, roo_issues):
        with db_session:
            n = Switcharoo(thread_id=thread_id, comment_id=comment_id, context=context,
                           submission_id=submission_id)
            for i in roo_issues:
                n.issues.add(Issues[i])

    def last_good(self):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo if True not in s.issues.bad).order_by(desc(Switcharoo.id)).limit(1)
            roo = q[0]
        if roo:
            self._link_reddit(roo)
        return roo

    def last(self):
        roo = None
        with db_session:
            q = select(s for s in Switcharoo).order_by(desc(Switcharoo.id)).limit(1)
            roo = q[0]
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
                for roo in q:
                    self._link_reddit(roo)
                    try:
                        if roo.submission.author is None:
                            roo.issues.add(Issues['submission_deleted'])
                            continue
                        if roo.submission.banned_by:
                            if not roo.submission.approved_by:
                                roo.issues.add(Issues['submission_deleted'])
                                continue
                        if hasattr(roo.submission, "removed"):
                            if roo.submission.removed:
                                roo.issues.add(Issues['submission_deleted'])
                                continue
                    except prawcore.exceptions.BadRequest:
                        roo.issues.add(Issues['submission_deleted'])
                        continue

                    try:
                        roo.comment.refresh()
                    except (praw.exceptions.ClientException, praw.exceptions.PRAWException):
                        roo.issues.add(Issues['comment_deleted'])
                        continue
                    # This one has passed the tests, should be good to go
                    good = True
                    break
                counter += 10


    def sync_issues(self):
        from core.issues import issues as issues_list
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