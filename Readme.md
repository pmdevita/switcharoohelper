# SwitcharooHelper

Verifies and maintains correct linking on Reddit's ol' switcharoo. switcharoohelper works by checking a switcharoo for 
a set of known issues, almost like a unit test. 
It then potentially deletes it if is unsalvagable and gives advice to the submitter on how to fix or resubmit it.
As of the upcoming version 3, it also can scan the chain for breaks using logged data in the database and monitor 
current issues in the chain. It can then ask for help to relink around breaks in the chain.

I'm not gonna sugar coat it, the bot as it currently stands a is a mess of highly situational specific logic 
based on how things went wrong and what date the roo was added. I'm hoping I can make it more readable in the 
future but banging this logic out of my head was just a mess in the first place.

Right now, roos older than March 2021 are given a pass

  * For improperly marking context
  * For linking to roos later removed by automoderator
  
And roos older than March 2019 are given an additional pass

  * For linking the wrong comment in the thread


## Setup/Running

Create a file called `credentials.ini` in the root directory of this project 
and in it place the following:
```ini
[reddit]
client_id = your-client-id
client_secret = your-client-secret
username = username-of-account
password = password-of-account

[database]
type = mysql|sqlite
host = ip|domain
username = username
password = password
database = switcharoo
```

then run `main.py`.

This bot currently runs under the user account /u/switcharoohelper

