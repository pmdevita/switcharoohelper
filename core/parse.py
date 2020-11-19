import re

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
    reddit_strict_parse = re.compile("^{}$".format(REDDIT_PATTERN))
    reddit_detect = re.compile(REDDIT_PATTERN)
    # wrongly_meta = re.compile("\A(?:https|http)?:\/\/(?:\w+?\.)?reddit.com\/r\/.*?\/comments\/(?P<thread_id>\w{6})\/.*?\/(?P<comment_id>\w{7})(?P<paramters>[\w?\/=]*?)\Z")


class RedditURL:
    def __init__(self, url):
        self._regex = REPatterns.reddit_strict_parse.match(url)




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
                return i[1].strip()
    # Search for just general URLs in the comment
    matches = REPatterns.reddit_detect.match(text)
    if matches:
        return matches[0]
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


def find_roo_recursive(comment, depth):
    if not depth:
        return None
    url = parse_comment(comment.body)
    if url:
        return url
    else:
        comment.refresh()
        for reply in comment.replies:
            url = find_roo_recursive(reply, depth - 1)
            if url:
                return url


def find_roo_comment(comment):
    return find_roo_recursive(comment, 4)


if __name__ == '__main__':
    # print(REPatterns.reddit_strict_parse.findall("https://www.reddit.com/r/Wellthatsucks/comments/edc61l/ive\_been\_saving\_up\_for\_a\_switch\_for\_a\_couple/fbhggjf?context=2"))
    # print(process_url_params("context=2&asdf=asdf"))
    print(only_reddit_url("[this](https://www.reddit.com/r/marvelstudios/comments/bwqij1/wonder_how_these_users_are_feeling_right_about_now/eq0maab/?context=5) step links to [this one](https://www.reddit.com/r/NoStupidQuestions/comments/bwn8pz/would_i_be_able_to_kill_a_polar_bear_with_an_ak47/epz1f9s/?context=1) which is now deleted and seemingly a https://www.reddit.com/r/marvelstudios/comments/bwqij1/wonder_how_these_users_are_feeling_right_about_now/eq0maab/?context=5 deleted user as well.\n\nmy journey ended early\n\n:("))
    print(only_reddit_url("https://www.reddit.com/r/Wellthatsucks/comments/edc61l/ive\_been\_saving\_up\_for\_a\_switch\_for\_a\_couple/fbhggjf?context=2"))