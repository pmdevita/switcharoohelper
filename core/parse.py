import re

"""
Provides different methods to parse Reddit data
"""

class REPatterns:
    # returns the URL from a Reddit embedded hyperlink
    old_link = re.compile("\[.*?\] *\n? *\((.*?)\)")
    link = re.compile("\[(.*?)\] *\n? *\((.*?)\)")
    reddit_thread = re.compile("^http(?:s)?://(?:\w+?\.)?reddit.com\/r\/.*?\/comments\/(?P<thread_id>\w{6})\/.*?\/(?P<comment_id>\w{7})")
    # Newer regex parsers
    reddit_strict_parse = re.compile("^http(?:s)?://(?:\w+?\.)?reddit.com(/r/|/user/)?(?(1)(\w{3,21}))(?(2)/comments/(\w{6})(?:/[\w%]+)?)?(?(3)/(\w{7}))?/?(\?)?(?(5)(.+))?$")
    reddit_detect = re.compile("http(?:s)?://(?:\w+?\.)?reddit.com(/r/)?(?(1)(\w{3,21}))(?(2)/comments/(\w{6})(?:/[\w%]+)?)?(?(3)/(\w{7}))?/?(\?)?(?(5)([a-zA-Z0-9%&=]+))?")
    # wrongly_meta = re.compile("\A(?:https|http)?:\/\/(?:\w+?\.)?reddit.com\/r\/.*?\/comments\/(?P<thread_id>\w{6})\/.*?\/(?P<comment_id>\w{7})(?P<paramters>[\w?\/=]*?)\Z")


def process_url_params(url_params):
    params = {}
    param_list = url_params.split("&")
    for param in param_list:
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

    match = REPatterns.reddit_thread.match(url)

    if match:
        thread_id = match.group("thread_id")
        comment_id = match.group("comment_id")
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
    matches = REPatterns.old_link.findall(text)
    if matches:
        # Now check for a reddit link
        for i in matches:
            match = REPatterns.reddit_thread.match(i)
            if match:
                return i
    return None


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


    # If it is an embedded link
    link = REPatterns.link.findall(text)
    if link:

        # Recalcuate total characters
        for i in link:
            total_len -= len(i[0]) + len(i[1]) + 4  # markup characters

        print("link found", link, total_len)

        # Is the embedded link a reddit link?
        for i in link:
            reddit_match = REPatterns.reddit_detect.match(i[1])
            if reddit_match:
                print("reddit match", reddit_match)
                if total_len < threshold:
                    return True

    # If there's text around the link
    match = REPatterns.reddit_detect.search(text)
    # There is, are we under threshold?
    if match:
        total_len -= match.end() - match.start()
        if total_len < threshold:
            return True

    return False


if __name__ == '__main__':
    # print(REPatterns.reddit_strict_parse.findall("https://www.reddit.com/r/CasualUK/comments/cllj0z/a_year_ago_i_decided_to_go_to_every_wetherspoons/evwbbe8?context=2&asdf=asdf"))
    print(process_url_params("context=2&asdf=asdf"))