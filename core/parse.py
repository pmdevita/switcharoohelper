import re
import regex
import praw.exceptions
from datetime import datetime
from core.pushshift import get_original_comment_from_psaw, get_comment_from_psaw
import urllib.parse
import praw.models
"""
Provides different methods to parse Reddit data
"""


class REPatterns:
    # returns the URL from a Reddit embedded hyperlink
    old_link = re.compile("\[.*?\] *\n? *\((.*?)\)")
    link = re.compile("\[(.*?)\] *\n? *\(\s*(.*?)\s*\)")
    reddit_thread = re.compile("^http(?:s)?://(?:\w+?\.)?reddit.com\/r\/.*?\/comments\/(?P<thread_id>\w{6})\/.*?\/(?P<comment_id>\w{7})")
    # Newer regex parsers
    REDDIT_PATTERN = "(?V1)(?i)http(?:s)?://(?:www\.)?(?:[\w-]+?\.)?reddit.com(?-i)(/r/|/user/)?(?(1)([\w:\.]{2,21}))(/comments/)?(?(3)(\w{5,6})(?:/[\w%\\\\-]+)?)?(?(4)/(\w{7}))?/?(\?)?(?(6)(\S+))?(\#)?(?(8)(\S+))?"
    SHORT_REDDIT_PATTERN = "(/r/|/user/)(?(1)([\w:\.]{2,21}))(/comments/)?(?(3)(\w{5,6})(?:/[\w%\\\\-]+)?)?(?(4)/(\w{7}))?/?(\?)?(?(6)(\S+))?(\#)?(?(8)(\S+))?"
    reddit_strict_parse = regex.compile("^{}$".format(REDDIT_PATTERN))
    reddit_detect = regex.compile(REDDIT_PATTERN)
    short_reddit_strict_parse = re.compile("^{}$".format(SHORT_REDDIT_PATTERN))
    short_reddit_detect = re.compile(SHORT_REDDIT_PATTERN)

    private_subreddit_response = re.compile("(allow|deny)(?: for (\d+) ((?:hour|day|week|month|year))s?)?", re.I)

    # wrongly_meta = re.compile("\A(?:https|http)?:\/\/(?:\w+?\.)?reddit.com\/r\/.*?\/comments\/(?P<thread_id>\w{6})\/.*?\/(?P<comment_id>\w{7})(?P<paramters>[\w?\/=]*?)\Z")


class RedditURL:
    @classmethod
    def from_regex(cls, regex):
        a = cls("")
        a._regex = regex
        a._regex_to_props()
        return a

    def __init__(self, url):
        self.is_reddit_url = False
        self.subreddit = None
        self.thread_id = None
        self.comment_id = None
        self.params = {}

        self._regex = REPatterns.reddit_strict_parse.findall(url)
        if not self._regex:
            self._regex = REPatterns.short_reddit_strict_parse.findall(url)
        self._regex_to_props()

    def _regex_to_props(self):
        if self._regex:
            self.is_reddit_url = True
            if self._regex[0][1]:
                # Fix user "subreddits" to link properly
                self.subreddit = self._regex[0][1]
                if self._regex[0][0] == "/user/":
                    self.subreddit = "u_" + self._regex[0][1]
            self.thread_id = self._regex[0][3] if self._regex[0][3] else None
            self.comment_id = self._regex[0][4] if self._regex[0][4] else None
            self.params = process_url_params(self._regex[0][6]) if self._regex[0][6] else {}

    def __str__(self):
        return f"RedditURL({self.thread_id}-{self.comment_id})"

    def __eq__(self, other):
        return self.thread_id == other.thread_id and self.comment_id == other.comment_id

    def to_link(self, reddit):
        url = "https://reddit.com"
        try:
            if self.comment_id:
                comment = reddit.comment(self.comment_id)
                url += comment.permalink
            elif self.thread_id:
                submission = reddit.submission(self.thread_id)
                url += submission.permalink
        except praw.exceptions.ClientException:
            return None
        if self.params:
            url += "?"
            url += "&".join([f"{i}={self.params[i]}" for i in self.params])
        return url


def process_url_params(url_params):
    params = {}
    param_list = url_params.split("&")
    for param in param_list:
        if "=" in param:
            p = param.split("=")
            params[p[0]] = p[1]
    return params



def thread_url_to_id(url):
    """
    TODO: Make a regex expression instead
    Get ids from a reddit thread link
    :param url:
    :return: Thread ID and comment ID
    """

    match = REPatterns.reddit_strict_parse.match(url)

    if match:
        thread_id = match[4]
        comment_id = match[5]
    else:
        return None, None

    # parts = url.split("/")
    #
    # # Check if it is a link to
    # if "comments" not in parts:
    #     return None, None
    #
    # thread_id = parts[parts.index("comments") + 1]
    #
    # # Check if there is also a comment id
    # if parts.index("comments") + 3 <= len(parts) - 1:
    #     comment_id = parts[parts.index("comments") + 3]
    #
    #     # Remove any extra URL parameters
    #     comment_id = comment_id.split("?")[0]
    #
    #     # Someone submitted a '.' as the comment id once ¯\_(ツ)_/¯
    #     if len(comment_id) != 7:
    #         comment_id = None
    #
    # else:
    #     comment_id = None

    return thread_id, comment_id


def parse_comment(text):
    """Get url from switcharoo comment"""
    # Grab all URLs from all links
    matches = REPatterns.link.findall(text)
    if matches:
        # Now check for a reddit link
        for i in matches:
            url = urllib.parse.unquote(i[1]).replace(" ", "")
            match = REPatterns.reddit_detect.findall(url)
            if match:
                return RedditURL(url.strip())
            match = REPatterns.short_reddit_detect.findall(url)
            if match:
                return RedditURL(url.strip())
    # Search for just general URLs in the comment
    matches = REPatterns.reddit_detect.findall(text)
    if matches:
        return RedditURL.from_regex(matches)
    matches = REPatterns.short_reddit_detect.findall(text)
    if matches:
        return RedditURL.from_regex(matches)
    return RedditURL("")


def is_meta_title(title):
    return "meta" in title.lower() and "vs" not in title.lower()


def only_reddit_url(title, body):
    """Determines if text is only a reddit URL. Used for finding incorrectly made
    meta posts"""
    total_len = len(body)
    threshold = max(len(title), 16)
    no_link = True

    # match = REPatterns.reddit_detect.match(text)
    # if match:
    #     total_len - match.end() - match.start()
    #     if total_len < threshold:
    #         return True
    #

    links = []

    # If it is an embedded link
    for m in REPatterns.link.finditer(body):
        groups = m.groups()
        start = m.start()
        end = m.end()
        # Remove the captured strings from the match length and then subtract that from the total length
        # Removes the link markup essentially
        total_len -= (end - start) - (len(groups[0]) + len(groups[1]))

        # print("link found", groups, total_len)
        no_link = False

        # Is the embedded link a reddit link?
        reddit_match = REPatterns.reddit_detect.match(groups[1])
        if reddit_match:
            # print("reddit match", reddit_match)
            total_len -= len(groups[1])
            if total_len <= threshold:
                return True

        links.append([groups, start, end])

    # We have passed all the checks for link markup, now remove them from the text to finish the search
    for i in reversed(links):
        body = body[:i[1]] + i[0][0] + body[i[2]:]

    # Now remove Reddit links from the rest of the text
    for match in reversed(list(REPatterns.reddit_detect.finditer(body))):
        # There is, are we under threshold?
        total_len -= match.end() - match.start()
        body = body[:match.start()] + body[match.end():]
        no_link = False
        if total_len <= threshold:
            return True

    if no_link and "vs" not in title.lower():
        # This post did not contain any links and it doesn't have vs in the title, it probably
        # won't be considered a roo by humans either
        return False
    else:
        # Strip out all whitespace
        body = body.replace(" ", "").replace("\n", "")
        total_len = len(body)

        # Is not only a reddit url!
        return total_len <= threshold


def find_roo_recursive(comment, starting_depth, depth):
    if not depth:
        return None
    if comment.body == "[deleted]" or comment.body == "[removed]":
        print("Comment was deleted")
        url = search_pushshift(comment)
    else:
        body = comment.body
        url = parse_comment(body)
    if url.comment_id:
        url = RedditURL(f"https://reddit.com{comment.permalink}")
        url.params['context'] = starting_depth - depth
        return url
    else:
        try:
            comment.refresh()
        except praw.exceptions.ClientException:
            return None
        for reply in comment.replies:
            url = find_roo_recursive(reply, starting_depth, depth - 1)
            if url:
                return url
    return None


def find_roo_parent_recursive(comment, starting_depth, depth):
    if not depth:
        return None
    if isinstance(comment, praw.models.Submission):
        return None
    url = parse_comment(comment.body)
    if url.comment_id:
        url = RedditURL(f"https://reddit.com{comment.permalink}")
        # url.params['context'] = starting_depth - depth
        return url
    else:
        try:
            comment.refresh()
        except praw.exceptions.ClientException:
            return None
        url = find_roo_parent_recursive(comment.parent(), starting_depth, depth - 1)
        if url:
            return url
    return None

def find_roo_comment(comment):
    roo = find_roo_recursive(comment, 4, 4)
    if roo:
        return roo
    roo = find_roo_parent_recursive(comment, 3, 3)
    if roo:
        return roo


# If we have only responded to this in the past, then pretend we already have it in FixRequests
# If there is a
def has_responded_to_post(submission):
    if not submission:
        return False
    response = False
    for comment in submission.comments:
        # This should not be hardcoded but it should also only be "temporary"
        if comment.author.name == "switcharoohelper":
            time = datetime.fromtimestamp(comment.created_utc)
            # If is newer than new update
            if time > datetime(year=2021, month=3, day=11):
                # Should already be handled in db
                return False
            else:
                response = True
    return response


def search_pushshift(comment, last_url=None):
    if not last_url:
        last_url = RedditURL(f"https://reddit.com{comment.permalink}")
    print("Searching PushShift for", last_url.comment_id)
    # psaw leaves a little to be desired in default functionality
    ps_comment = get_comment_from_psaw(comment.parent_id[3:], last_url.comment_id)
    if ps_comment:
        ps_comment = parse_comment(ps_comment['body'])
    pso_comment = get_original_comment_from_psaw(last_url.comment_id)
    if pso_comment:
        pso_comment = parse_comment(pso_comment['body'])
    if ps_comment and pso_comment:
        if ps_comment == pso_comment:
            url = ps_comment
        else:
            print("Two versions of comment, which one to use? (1/2)")
            print(pso_comment.to_link(comment._reddit), ps_comment.to_link(comment._reddit))
            option = input()
            if option == "1":
                url = pso_comment
            else:
                url = ps_comment
    elif ps_comment:
        url = ps_comment
    elif pso_comment:
        url = pso_comment
    else:
        url = RedditURL("")
    return url


if __name__ == '__main__':
    print(only_reddit_url("[Turkey vs. Grandma](https://www.reddit.com/r/coolguides/comments/meo1l2/how_to_reheat_pizza/gsl4arc?utm_source=share&utm_medium=web2x&context=5)"))
