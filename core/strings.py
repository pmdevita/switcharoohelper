BLANK = 0


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

    def __str__(self):
        return self.__class__.__name__


class ModIssueStrings:
    submission_lacks_context = "the link to your switcharoo does not contain the `?context=x` suffix. Read "\
                               "the sidebar for more information."
    submission_linked_thread = "your post's link is to a Reddit thread, not a comment permalink. Make sure to "\
                               "click the permalink button on the comment (or on mobile, grab the link to the "\
                               "comment)."
    comment_deleted = "your switcharoo comment was deleted. If you deleted your comment, please don't do "\
                      "that. If you can still see the comment, then the subreddit moderators probably "\
                      "removed it. If you want to double check, log out or log into a "\
                      "different account and look for your comment.\n\nIf you think your comment was "\
                      "removed by was that subreddit's moderators, please let us know so we can add it to "\
                      "the forbidden subs list. Also, sorry. It sucks when this happens."
    comment_has_no_link = "your submission does not link to a switcharoo. It's very likely you linked the "\
                          "wrong comment. Read the sidebar or stickied \"how to\" post for more information."
    comment_linked_wrong = "your switcharoo is not linked to the correct roo. Did you remember to sort the "\
                           "subreddit by new? The correct link is \n\n{last_good_url}\n\nCan you please change it to "\
                           "that? Thanks!"
    comment_lacks_context = "the roo you have **linked to in your comment** (not the URL you have submitted) is "\
                            "missing a `?context=x` suffix. Most likely, the roo'er previous to you left it out "\
                            "but it's possible you missed it in copying their link.\n\nGo to the switcharoo your "\
                            "comment links to and count how many comments above it are needed to understand the "\
                            "joke. Then, in the link in your comment, append `?context=x` to the end of the link, "\
                            "replacing x with the number of levels you counted. Thanks for fixing it!"
    comment_linked_bad_roo = "your switcharoo links to a broken roo. Can you please change it to this link?\n\n"\
                             "{last_good_url}\n\nThanks!"
    submission_multiple_params = "your switcharoo had multiple '?' sections at the end of it. You can resubmit if you "\
                                 "delete everything after and including the '?' in your URL and then append "\
                                 "`?context=x` to the end of the URL. Don't forget to relink your switcharoo to the "\
                                 "newest switcharoo submission!"
    submission_link_final_slash = "your switcharoo had a trailing slash (\"/\") at the end of it. This causes the "\
                                  "`?context=x` property to not work. You can resubmit if you delete the slash(es) "\
                                  "at the end of the URL. Don't forget to relink your switcharoo to the "\
                                  "newest switcharoo submission!"
    submission_not_reddit = "the link leads outside of reddit. Did you mean to submit a meta "\
                            "post? Read the sidebar for more information."
    submission_is_meta = "your post appears to be a roo submitted as a text post. All switcharoos should be "\
                         "submitted as link posts for clarity and subreddit organization."
    submission_linked_post = "your post linked the r/switcharoo post for the next roo, not the link to it's comment. "\
                             "Your comment should link to the posted link given by the previous roo. The correct " \
                             "link is {last_good_url}"
    submission_bad_url = "something seems wrong with your submitted URL and I couldn't recognize it as a Reddit URL. "\
                         "Did you copy it correctly?"
    user_noncompliance = "you have ignored the request to fix the linking problems. Contact the moderators "\
                         "to have your post reinstated."
    submission_deleted = BLANK


class NewIssueIssues(ModIssueStrings):
    comment_linked_wrong = "link your comment to this link instead? {last_good_url}"
    comment_linked_bad_roo = "link your comment to this link instead? {last_good_url}"
    comment_lacks_context = "add/change the context in your comment's link? It's possible the previous poster left " \
                            "it out but you may have also missed it when copying. Go to the switcharoo your "\
                            "comment links to and count how many comments above it are needed to understand the "\
                            "joke. Then, in the link in your comment, append `?context=x` to the end of the link, "\
                            "replacing x with the number of levels you counted."


class MultiNewIssueIssues(NewIssueIssues):
    comment_linked_wrong = "link your comment to this link instead. {last_good_url}"
    comment_linked_bad_roo = "link your comment to this link instead. {last_good_url}"
    comment_lacks_context = "add/change the context in your comment's link. It's possible the previous poster left " \
                            "it out but you may have also missed it when copying. Go to the switcharoo your "\
                            "comment links to and count how many comments above it are needed to understand the "\
                            "joke. Then, in the link in your comment, append `?context=x` to the end of the link, "\
                            "replacing x with the number of levels you counted."


class ModActionStrings:
    issue_strings = ModIssueStrings
    multi_issue_strings = None
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

    footer = "---\nI am a bot. [Report an issue](https://www.reddit.com/message/" \
             "compose?to=%2Fu%2Fpmdevita&subject=Switcharoohelper%20Issue&message=)"

    old_footer = "---\nI am a bot currently fixing the last 10 years of the switcharoo. Reply to report an issue " \
                 "or ask the mods a question. You can also visit us at r/switcharoo for more information."


class WarnStrings(ModActionStrings):
    single_reason = "Unfortunately, {}\n\n"
    multiple_reason = "There are a few things that need to be fixed with your roo:\n\n{}\n\n"


class DeleteStrings(ModActionStrings):
    subject = "Notice about your switcharoo"
    single_reason = "Unfortunately, your submission was removed because {}\n\n"
    multiple_reason = "Unfortunately, your submission was removed for the following reasons:\n\n{}\n\n"


class NewIssueStrings(ModActionStrings):
    issue_strings = NewIssueIssues
    multi_issue_strings = MultiNewIssueIssues
    header = "{} It looks like there has been some changes to switcharoo chain around your comment. "
    single_reason = "Could you {}\n\nThank you!\n\n"
    multiple_reason = "Could you do the fix the following in your roo? \n\n{}\n\nThank you!\n\n"


class ReminderStrings(NewIssueStrings):
    header = "{}  "
    single_reason = "It looks like you haven't quite fixed this yet. Could you {} Thank you!\n\n"
    multiple_reason = "It looks like you haven't quite fixed these issues yet. Could you do the fix " \
                      "the following in your roo? \n\n{}\n\nThank you!\n\n"


class NewIssueDeleteStrings(DeleteStrings):
    header = "{}\n\n"
    single_reason = "Unfortunately,your submission had to be removed because {}\n\n"
    multiple_reason = "Unfortunately, your submission had to be removed for the following reasons:\n\n{}\n\n"


if __name__ == '__main__':
    print(issubclass(DeleteStrings, DeleteStrings))
    print(issubclass(DeleteStrings, NewIssueDeleteStrings))
