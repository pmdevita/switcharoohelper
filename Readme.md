# Switcharoo Helper

Verifies new additions to the switcharoo chain are correctly linked and unbroken.

## Setup/Running

Create a file called `credentials.json` in the root directory of this project 
and in it place the following:
```json
{
  "client_id": "reddit api client id",
  "client_secret": "reddit api client secret",
  "username": "username of bot",
  "password": "password of bot"
}
```

then run `main.py`.

This bot currently runs under the user account /u/switcharoohelper

## How it works

### Basic Logic
When someone posts a submission (that should be linking to the switcharoo comment) to 
r/switcharoo, the bot

* Checks the link
    * is to a comment that
        * contains a switcharoo
        * is a correct link to the previous correct switcharoo
        * has the context suffix
    * has the `?context=x` suffix

In testing, I found it is common for people to link to the wrong comment (i.e. 
the parent comment to the actual link). In the future, adding a search algorithm for the 
correct comment would be useful.

### Action

If there is anything wrong with how the submission is linked (not linked to the right comment, missing 
context suffix, etc.), the post is deleted and the user is given instruction to try 
again if they wish. 

If there is an issue with the comment (wrong link), the user is given the correct link and 
asked to fix the problem.

## To do
* Switch config from json to configparser
* Search for correct comment when linked incorrectly
* Refactor and tidy up the place
