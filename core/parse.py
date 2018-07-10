import re

"""
Provides different methods to parse Reddit data
"""

class REPatterns:
    # returns the URL from a Reddit embedded hyperlink
    link = re.compile("\[.*?\] *\n? *\((.*?)\)")
    reddit_thread = re.compile("https?:\/\/(.*?\.|)reddit.com\/r\/.*?\/comments\/(?P<thread_id>.{6})\/.*?\/(?P<comment_id>.{7})")

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
    matches = REPatterns.link.findall(text)
    if matches:
        # Now check for a reddit link
        for i in matches:
            match = REPatterns.reddit_thread.match(i)
            if match:
                return i
    return None

