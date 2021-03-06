import praw
import re
from praw.models import Comment, Submission
import datetime as dt
from psaw import PushshiftAPI
from core.credentials import CredentialsLoader
from core import constants as consts

credentials = CredentialsLoader.get_credentials()['reddit']

reddit = praw.Reddit(client_id=credentials["client_id"],
                     client_secret=credentials["client_secret"],
                     user_agent=consts.user_agent,
                     username=credentials["username"],
                     password=credentials["password"])

api = PushshiftAPI(reddit)

start = int(dt.datetime(2019, 9, 2).timestamp())
end = int(dt.datetime(2019, 9, 4).timestamp())

# thing = api.search_submissions(after=start, before=end, subreddit='switcharoo')

thing = api.search_comments(subreddit='gifs', after=start, before=end,)

grb = re.compile('gifreversingbot', flags=re.I)

for i in thing:
    if isinstance(i, Submission):
        print(i, i.title, i.author, i.url)
    elif isinstance(i, Comment):
        matches = grb.findall(i.body)
        if matches and i.author.name != 'GifReversingBot':
            print(i, i.author, dt.datetime.utcfromtimestamp(i.created_utc).replace(tzinfo=dt.timezone.utc).astimezone(), "https://reddit.com"+i.permalink)




