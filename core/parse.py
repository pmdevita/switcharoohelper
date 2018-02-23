import re

"""
Provides different methods to parse Reddit data
"""

class REPatterns:
    # returns the URL from a Reddit embedded hyperlink
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

    # Someone submitted a '.' as the comment id once ¯\_(ツ)_/¯
    if len(comment_id) != 7:
        comment_id = None

    return thread_id, comment_id


def parse_comment(text):
    """Get url from switcharoo comment"""
    matches = REPatterns.link.findall(text)
    print(matches)
    if matches:
        if len(matches) > 1:    # Some subreddits add strange links and stuff
            for match in matches:   # usually they don't start with http
                if match[:4] == "http":
                    return match
            return None
        else:                   # Normal case where there is only one link
            return matches[0]
    else:
        return None

