import json
from switcharoo.config.constants import CONTEXT_HEADER


def format_context(context):
    return f"[]({CONTEXT_HEADER}{{{json.dumps(context)}}})"


class CommentHasNoLink:
    template = "the comment you've linked to doesn't seem to have a switcharoo linked in it. This " \
               "is *almost always* a case of just linking the wrong comment."
    found_url = " I did a quick search and I think the actual URL you meant to submit was " \
                "this one.\n\n{correct_comment_url}\n\nDouble check this is the correct link and submit " \
                "it again. Thanks!"
    not_found_url = " I did a quick search but I wasn't able to find the correct comment. You'll want to " \
                    "submit the link to your comment that has the \"Ah the ol' switcharoo!\" message " \
                    "with a link to next switcharoo."

    @classmethod
    def format(cls, correct_comment_url=None, **kwargs):
        if correct_comment_url:
            return cls.template + cls.found_url.format(correct_comment_url=correct_comment_url, **kwargs)
        else:
            return cls.template + cls.not_found_url


class IssueStrings:
    submission_lacks_context = ""
    submission_linked_thread = ""
    comment_deleted = ""
    comment_has_no_link = ""
    comment_linked_wrong = ""
    comment_lacks_context = ""
    comment_linked_bad_roo = ""
    submission_multiple_params = ""
    submission_link_final_slash = ""
    submission_not_reddit = ""
    submission_is_meta = ""
    submission_linked_post = ""
    submission_bad_url = ""
    user_noncompliance = ""
    user_mismatch = ""
    subreddit_privated = ""
    user_blocked = ""

    def __str__(self):
        return self.__class__.__name__


class ModIssueStrings(IssueStrings):
    submission_lacks_context = "the link to your switcharoo does not contain the `?context=x` suffix. Read " \
                               "the sidebar for more information."
    submission_linked_thread = "your post's link is to a Reddit thread, not a comment permalink. Make sure to " \
                               "click the permalink button on the comment (or on mobile, grab the link to the " \
                               "comment)."
    comment_deleted = "your switcharoo comment was deleted. If you deleted your comment, please don't do " \
                      "that. If you can still see the comment, then the subreddit moderators probably " \
                      "removed it. If you want to double check, log out or log into a " \
                      "different account and look for your comment.\n\nIf you think your comment was " \
                      "removed by was that subreddit's moderators, please let us know so we can add it to " \
                      "the forbidden subs list. Also, sorry. It sucks when this happens."
    comment_has_no_link = CommentHasNoLink
    comment_linked_wrong = "I'm not sure what you are linking into but it doesn't seem quite right. Can you change " \
                           "your link to here instead?\n\n{last_good_url}\n\nThank you!"
    comment_lacks_context = "the roo you have **linked to in your comment** (not the URL you have submitted) is " \
                            "missing a `?context=x` suffix. Most likely, the roo'er previous to you left it out " \
                            "but it's possible you missed it in copying their link.\n\nGo to the switcharoo your " \
                            "comment links to and count how many comments above it are needed to understand the " \
                            "joke. Then, in the link in your comment, append `?context=x` to the end of the link, " \
                            "replacing x with the number of levels you counted. Thanks for fixing it!"
    comment_linked_bad_roo = "your switcharoo is not linked to the correct roo. Did you remember to sort the " \
                             "subreddit by new? The correct link is \n\n{last_good_url}\n\nCan you please change it " \
                             "to that? Thanks!"
    submission_multiple_params = "your switcharoo had multiple '?' sections at the end of it. You can resubmit if " \
                                 "you delete everything after and including the '?' in your URL and then append " \
                                 "`?context=x` to the end of the URL. Don't forget to relink your switcharoo to the " \
                                 "newest switcharoo submission!"
    submission_link_final_slash = "your switcharoo had a trailing slash (\"/\") at the end of it. This causes the " \
                                  "`?context=x` property to not work. You can resubmit if you delete the slash(es) " \
                                  "at the end of the URL. Don't forget to relink your switcharoo to the " \
                                  "newest switcharoo submission!"
    submission_not_reddit = "the link leads outside of reddit. Did you mean to submit a meta " \
                            "post? Read the sidebar for more information."
    submission_is_meta = "your post appears to be a roo submitted as a text post. All switcharoos should be " \
                         "submitted as link posts for clarity and subreddit organization.\n\nIf you are submitting " \
                         "a discussion post and not a roo, reply \"Not a roo\" to this comment and I'll approve it. " \
                         "If this is roo, please resubmit it as a link post.\n\nThank you!\n" \
                         f"{format_context({'decision-type': 'meta-roo'})}"
    submission_linked_post = "your comment linked the r/switcharoo post for the next roo, not the link to it's " \
                             "comment. Your comment should link to the posted link given by the previous roo. The " \
                             "correct link is {last_good_url}"
    submission_bad_url = "something seems wrong with your submitted URL and I couldn't recognize it as a Reddit URL. " \
                         "Did you copy it correctly?"
    user_noncompliance = "you have ignored the request to fix the linking problems. Contact the moderators " \
                         "to have your post reinstated."
    submission_deleted = None
    user_mismatch = "the user submitting this roo is not the same as the user who created the roo comment. Both the " \
                    "commenter and poster should be the same for the sake of consistency and to avoid duplicate " \
                    "posting."
    subreddit_privated = "the subreddit this roo is from is privated so most users will be unable to continue down " \
                         "the roo chain through this one. If it has only temporarily been privated, try submitting " \
                         "again after it has unprivated."
    user_blocked = "you have blocked the switcharoohelper bot. This means any time the bot needs your help to make a" \
                   " change to the switcharoo chain, you won't be able to see its messages. Please unblock the bot " \
                   "and message the mods to have your roos reinstated."


class WarnIssues(ModIssueStrings):
    comment_linked_wrong = "Can you link your comment here instead? I'm not sure exactly what you linked but it " \
                           "doesn't seem quite right to me. Remember to sort by new when copying your link!" \
                           "\n\n{last_good_url}"
    comment_lacks_context = "Can you add context to the link in your comment? You might want to double check but I " \
                            "think it should be {last_good_context}, so the link should look like \n\n{last_good_url}"
    comment_linked_bad_roo = "It looks like you linked the wrong roo. Can you link your comment here instead? " \
                             "Remember to sort by new when copying your link!" \
                             "\n\n{last_good_url}"
    submission_linked_post = "Can you link your comment here instead? It looks like you linked an r/switcharoo " \
                             "thread rather than the link to their comment. Don't forget to copy the right link!" \
                             "\n\n{last_good_url}."


class NewIssueIssues(ModIssueStrings):
    comment_linked_wrong = "link your comment to this link instead? {last_good_url}"
    comment_linked_bad_roo = "link your comment to this link instead? {last_good_url}"
    comment_lacks_context = "add/change the context in your comment's link? It's possible the previous poster left " \
                            "it out but you may have also missed it when copying. Go to the switcharoo your " \
                            "comment links to and count how many comments above it are needed to understand the " \
                            "joke. Then, in the link in your comment, append `?context=x` to the end of the link, " \
                            "replacing x with the number of levels you counted."


class NewIssueMessageIssues(NewIssueIssues):
    comment_linked_wrong = "change your comment here\n\n{comment_url}\n\n" \
                           "to link to this comment instead? \n\n{last_good_url}"
    comment_linked_bad_roo = "change your comment here\n\n{comment_url}\n\n" \
                             "to link to this comment instead? \n\n{last_good_url}"
    comment_lacks_context = "add/change the context in the link in your comment here?\n\n{comment_url}\n\n" \
                            "I think it " \
                            "should be {last_good_context}, so the link should look like \n\n{last_good_url}"


class MultiNewIssueIssues(NewIssueIssues):
    comment_linked_wrong = "link your comment to this link instead. {last_good_url}"
    comment_linked_bad_roo = "link your comment to this link instead. {last_good_url}"
    comment_lacks_context = "add/change the context in your comment's link. It's possible the previous poster left " \
                            "it out but you may have also missed it when copying. Go to the switcharoo your " \
                            "comment links to and count how many comments above it are needed to understand the " \
                            "joke. Then, in the link in your comment, append `?context=x` to the end of the link, " \
                            "replacing x with the number of levels you counted."


class MultiNewIssueMessageIssues(NewIssueMessageIssues):
    pass


# Strings regarding the main structure of a response the bot may make
class ModActionStrings:
    issue_strings = ModIssueStrings
    multi_issue_strings = None
    message_issue_strings = None
    message_multi_issue_strings = None

    subject = "Help needed to fix the switcharoo chain!"
    header = "{} First, thank you for contributing to /r/switcharoo! The sub only exists thanks to people " \
             "such as yourself who are willing to put the time in to keep the chain going. \n\n"

    resubmit_text = "Your switcharoo does still seem like it could be added to the chain. First, reread " \
                    "the sidebar and if you need to, the [wiki](https://www.reddit.com/r/switcharoo/wiki/index). " \
                    "Then, fix the {} above. Finally, change the link in your switcharoo comment to the newest " \
                    "submission in /r/switcharoo/new and make a new submission linking to your switcharoo.\n\n"

    single_reason = "Unfortunately, {}\n\n"

    multiple_reason = "There are a few things that need to be fixed with your roo:\n\n{}\n\n"

    thank_you = "Thank you for fixing your switcharoo!\n\n"

    thank_you20220210 = "Hello again!\n\nIt appears that there was an error with the Reddit API last night that " \
                        "caused switcharoohelper to send out several incorrect fix requests. This should now be " \
                        "resolved and you can ignore the previous correction message. Thank you to those " \
                        "that reported the issue and thank you all for your patience!\n\n" \
                        "If you would like more information, you can find the discussion thread on the issue [here]" \
                        "(https://www.reddit.com/r/switcharoo/comments/spa2yp/february_10th_switcharoohelper_" \
                        "incident/).\n\n"

    footer = "---\nI am a bot. [Report an issue](https://www.reddit.com/message/" \
             "compose?to=%2Fu%2Fpmdevita&subject=Switcharoohelper%20Issue&message=)"

    old_footer = "---\nI am a bot currently fixing the last 10 years of the switcharoo. Reply to report an issue " \
                 "or ask the mods a question. You can also visit us at r/switcharoo for more information."


# Strings used when a roo is not marked as a bad issue and will simply be warned
class WarnStrings(ModActionStrings):
    issue_strings = WarnIssues
    single_reason = "There's just one thing I need fixed with your roo. {}\n\nThank you!\n\n"
    multiple_reason = "There are a few things that need to be fixed with your roo:\n\n{}\n\n"


# Strings used when a roo is marked with a bad issue and will be removed
class DeleteStrings(ModActionStrings):
    subject = "Notice about your switcharoo"
    single_reason = "Unfortunately, your submission was removed because {}\n\n"
    multiple_reason = "Unfortunately, your submission was removed for the following reasons:\n\n{}\n\n"


class NewIssueStrings(ModActionStrings):
    issue_strings = NewIssueIssues
    multi_issue_strings = MultiNewIssueIssues
    message_issue_strings = NewIssueMessageIssues
    message_multi_issue_strings = MultiNewIssueMessageIssues
    header = "{} It looks like there has been some changes to switcharoo chain around your roo. "
    single_reason = "Could you {}\n\nThank you!\n\n"
    multiple_reason = "Could you do the fix the following in your roo? \n\n{}\n\nThank you!\n\n"


class ReminderStrings(NewIssueStrings):
    header = "{}  "
    single_reason = "It looks like you haven't quite fixed this yet. Could you {}\n\nThank you!\n\n"
    multiple_reason = "It looks like you haven't quite fixed these issues yet. Could you do the fix " \
                      "the following in your roo? \n\n{}\n\nThank you!\n\n"


class NewIssueDeleteStrings(DeleteStrings):
    header = "{}\n\n"
    single_reason = "Unfortunately,your submission had to be removed because {}\n\n"
    multiple_reason = "Unfortunately, your submission had to be removed for the following reasons:\n\n{}\n\n"


class ModMail:
    privated_sub_subject = "Decide what to do with a privated sub"
    privated_sub_body = "The subreddit r/{subreddit} appears to be privated, what action should be taken with " \
                        "roos linked there?\n\nExample response:\n\n- `deny`\n- `allow for 7 days`\n" \
                        "- `allow for 2 months`\n" \
                        f"{format_context({'decision-type': 'private-subreddit', 'subreddit': '{subreddit}'})}" \
                        "\n\n"
    footer = "---\nI am a bot. [Report an issue](https://www.reddit.com/message/" \
             "compose?to=%2Fu%2Fpmdevita&subject=Switcharoohelper%20Issue&message=)"


if __name__ == '__main__':
    print(issubclass(DeleteStrings, DeleteStrings))
    print(issubclass(DeleteStrings, NewIssueDeleteStrings))
