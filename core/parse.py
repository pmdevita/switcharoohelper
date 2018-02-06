import re

"""
Provides different methods to parse Reddit data
"""

class REPatterns:
    link = re.compile("\[.*?\] *\n? *\((.*?)\)")

def thread_url_to_id(url):
    """
    TODO: Make a regex expression instead
    Get ids from a reddit thread link
    :param url:
    :return: Thread ID and comment ID
    """
    parts = url.split("/")

    # Check if it is a link to
    if "comments" not in parts:
        return None, None

    thread_id = parts[parts.index("comments") + 1]

    # Check if there is also a comment id
    if parts.index("comments") + 3 <= len(parts) - 1:
        comment_id = parts[parts.index("comments") + 3]

        # Remove any extra URL parameters
        comment_id = comment_id.split("?")[0]
    else:
        comment_id = None

    return thread_id, comment_id


def parse_comment(text):
    """Get url from switcharoo comment"""
    # Reddit allows infinite spaces and up to one character turn in
    # between the [] and () parts. We actually have to do a serious
    # breakdown of the text.
    match = REPatterns.link.findall(text)
    if match:
        return match[0]
    else:
        return None

