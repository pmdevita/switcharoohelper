import praw
import datetime as dt
from psaw import PushshiftAPI
from core.credentials import CredentialsLoader
from core import constants as consts

credentials = CredentialsLoader.get_credentials()['reddit']

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent.format(consts.version),
                     username=credentials["username"],
                     password=credentials["password"])

api = PushshiftAPI(reddit)

start = int(dt.datetime(2017, 8, 18).timestamp())
end = int(dt.datetime(2017, 8, 21).timestamp())

thing = api.search_submissions(after=start, before=end, subreddit='switcharoo')

for i in thing:
    print(i, i.title, i.author, i.url)