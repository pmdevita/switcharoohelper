# SwitcharooHelper

Verifies and maintains correct linking on Reddit's ol' switcharoo. switcharoohelper works by checking a switcharoo for 
a set of known issues, almost like a unit test. 

The bot has several services that can be run:

- main.py - This service logs new incoming roos and, if needed, offers fixing advice to the submitter and deletes 
submissions that are broken or need to be resubmitted to fix. It also reads modmail for moderator commands.
- check_up.py - This service scans the chain, checking for any changes. It then sends comments or messaegs to users 
asking for them to help fix the chain or remind them that they still need to fix it.
- userflair_update.py - This service synchronizes subreddit flair with the database.

Currently, the bot code is a bit of a mess. The logic for adding the check up service was difficult to bang out of my 
head and I'm still in the process of fixing it up. The bot is also still midway through a migration to a more OO design 
and I haven't quite figured out some parts of it yet.

The bot checks up roo linking according to 
[official r/switcharoo instructions](https://www.reddit.com/r/switcharoo/wiki/index#wiki_how_to_submit_a_roo).

Additionally, right now, roos older than March 2021 are given a pass

  * For improperly marking context
  * For linking to roos later removed by AutoModerator
  
And roos older than March 2019 are given an additional pass

  * For linking the wrong comment in the thread

These errors are abundant and trying to fix all of them would be a massive headache. An approach of "if it isn't too 
broke, don't fix it" has been adopted for these old roos.

## Setup/Running

Create a file called `credentials.ini` in the root directory of this project 
and in it place the following:
```ini
[general]
mode = development|production
operator = reddit_username
dry_run = False
award = True

[reddit]
client_id = client-id
client_secret = client-secret
username = bot_username
password = password

[database]
type = mysql|sqlite
host = hostname|ip
username = username
password = password
database = database
```

This bot currently runs under the user account /u/switcharoohelper

