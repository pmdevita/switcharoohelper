"""
Provides different methods to parse Reddit data
"""


def thread_url_to_id(url):
    """
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
    if "](" not in text:
        return None
    start = text.index("](") + 2
    end = text.index(")", start)
    url = text[start:end]
    return url
