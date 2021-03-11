# SwitcharooHelper

Verifies and maintains correct linking on Reddit's ol' switcharoo. switcharoohelper works by checking a switcharoo for 
a set of known issues, almost like a unit test. 
It then potentially deletes it if is unsalvagable and gives advice to the submitter on how to fix or resubmit it.
As of the upcoming version 3, it also can scan the chain for breaks using logged data in the database and monitor 
current issues in the chain. It can then ask for help to relink around breaks in the chain.

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

