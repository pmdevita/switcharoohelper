import re
import praw.exceptions
from datetime import datetime

"""
Provides different methods to parse Reddit data
"""

class REPatterns:
    # returns the URL from a Reddit embedded hyperlink
    old_link = re.compile("\[.*?\] *\n? *\((.*?)\)")
    link = re.compile("\[(.*?)\] *\n? *\(\s*(.*?)\s*\)")
    reddit_thread = re.compile("^http(?:s)?://(?:\w+?\.)?reddit.com\/r\/.*?\/comments\/(?P<thread_id>\w{6})\/.*?\/(?P<comment_id>\w{7})")
    # Newer regex parsers
    REDDIT_PATTERN = "http(?:s)?://(?:\w+?\.)?reddit.com(/r/|/user/)?(?(1)(\w{2,21}))(/comments/)?(?(3)(\w{6})(?:/[\w%\\\\-]+)?)?(?(4)/(\w{7}))?/?(\?)?(?(6)(\S+))?"
    SHORT_REDDIT_PATTERN = "(/r/|/user/)(?(1)(\w{2,21}))(/comments/)?(?(3)(\w{6})(?:/[\w%\\\\-]+)?)?(?(4)/(\w{7}))?/?(\?)?(?(6)(\S+))?"
    reddit_strict_parse = re.compile("^{}$".format(REDDIT_PATTERN))
    reddit_detect = re.compile(REDDIT_PATTERN)
    short_reddit_strict_parse = re.compile("^{}$".format(SHORT_REDDIT_PATTERN))
    short_reddit_detect = re.compile(SHORT_REDDIT_PATTERN)

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
            match = REPatterns.reddit_detect.findall(i[1])
            if match:
                return RedditURL(i[1].strip())
            match = REPatterns.short_reddit_detect.findall(i[1])
            if match:
                return RedditURL(i[1].strip())
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


def only_reddit_url(text):
    """Determines if text is only a reddit URL. Used for finding incorrectly made
    meta posts"""
    total_len = len(text)
    threshold = 15

    # match = REPatterns.reddit_detect.match(text)
    # if match:
    #     total_len - match.end() - match.start()
    #     if total_len < threshold:
    #         return True
    #

    links = []

    # If it is an embedded link
    for m in REPatterns.link.finditer(text):
        groups = m.groups()
        start = m.start()
        end = m.end()
        # Remove the captured strings from the match length and then subtract that from the total length
        # Removes the link markup essentially
        total_len -= (end - start) - (len(groups[0]) + len(groups[1]))

        print("link found", groups, total_len)

        # Is the embedded link a reddit link?
        reddit_match = REPatterns.reddit_detect.match(groups[1])
        if reddit_match:
            print("reddit match", reddit_match)
            total_len -= len(groups[1])
            if total_len < threshold:
                return True

        links.append([groups, start, end])

    # We have passed all the checks for link markup, now remove them from the text to finish the search
    for i in reversed(links):
        text = text[:i[1]] + i[0][0] + text[i[2]:]

    # Now remove Reddit links from the rest of the text
    for match in REPatterns.reddit_detect.finditer(text):
        # There is, are we under threshold?
        total_len -= match.end() - match.start()
        if total_len < threshold:
            return True

    # Is not only a reddit url!
    return False


def find_roo_recursive(comment, starting_depth, depth):
    if not depth:
        return None
    url = parse_comment(comment.body)
    if url.comment_id:
        url = RedditURL(f"https://reddit.com{comment.permalink}")
        url.params['context'] = starting_depth - depth
        return url
    else:
        comment.refresh()
        for reply in comment.replies:
            url = find_roo_recursive(reply, starting_depth, depth - 1)
            if url:
                return url
    return None


def find_roo_comment(comment):
    return find_roo_recursive(comment, 4, 4)


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


if __name__ == '__main__':
    print(parse_comment("""[](/kderpymeow-90-f) Ah, the ol' reddit [third-world-aroo!](https://old.reddit.com/r/interestingasfuck/comments/a9xt2g/you_may_be_cool_but_you_will_never_be_as_cool_as/ecnjvlf/?context=2)"""))