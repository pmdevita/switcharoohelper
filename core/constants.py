version = "2.0a"
user_agent = "SwitcharooHelper by /u/pmdevita v{}"
sleep_time = 120
sleep_time_test = 10
settled_check = 60 * 60 * 24 * 4


class ModActionStrings:
    header = "{} First, thank you for contributing to /r/switcharoo! The sub only exists thanks to people " \
             "such as yourself who are willing to put the time in to keep the chain going. \n\n"

    resubmit_text = "Your switcharoo does still seem like it could be added to the chain. First, reread " \
                    "the sidebar and if you need to, the [wiki](https://www.reddit.com/r/switcharoo/wiki/index). " \
                    "Then, fix the {} above. Finally, change the link in your switcharoo comment to the newest " \
                    "submission in /r/switcharoo/new and make a new submission linking to your switcharoo.\n\n"

    delete_single_reason = "Unfortunately, your submission was removed because {}\n\n"

    delete_multiple_reason = "Unfortunately, your submission was removed for the following reasons:\n\n{}\n\n"

    warn_single_reason = "Unfortunately, {}\n\n"

    warn_multiple_reason = "There are a few things that need to be fixed with your roo:\n\n{}\n\n"

    footer = "---\nI am a bot. I'm still new and may make mistakes. [Report an issue](https://www.reddit.com/message/" \
             "compose?to=%2Fu%2Fpmdevita&subject=Switcharoohelper%20Issue&message=)"
