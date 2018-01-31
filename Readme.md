# Switcharoo Helper

Verifies the switcharoo chain is correctly linked and unbroken. This bot focuses 
on verifying new additions to the chain. A future project may verify the chain 
going down.

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

I can run the bot for the mods of r/switcharoo if they would like.

## How it works

### Basic Logic
When someone posts a submission (that should be linking to the switcharoo comment) to 
r/switcharoo, the bot

* Checks the link
    * is to a comment that
        * contains a switcharoo
        * is a correct link to the previous switcharoo
        * is not a duplicate (future feature)
    * has the `?context=x` suffix

In testing, I found it is common for people to link to the wrong comment (i.e. 
the parent comment to the actual link). In the future, adding a search algorithm for the 
correct comment would be useful.

I have yet to find a duplicate link to test how such a thing would happen. I did 
find a duplicate but strangely it lacked a submission.

We can (theoretically) check a link is not a duplicate by

* Check if link to thread (not just comment) has been posted
    * Check if link is to identical comment
    * Check if link is under the same parent comment

### Recommendations for action

If the switcharoo post is just missing the `?context=` suffix, comment on 
it to alert the poster and flair it to alert the next switcharoo poster in the 
chain. We could delete it if we want to take a very strong approach to preserving
the chain but hopefully the OP would be responsive.

If it is an exact duplicate link or only separated by one level of comments, delete 
it. If it separated by more levels, comment on it to alert the poster and flair it 
to alert the next switcharoo poster in the chain.

If incorrectly linked, comment on it to alert the poster and flair it to alert the
next switcharoo poster in the chain. We could also take a strong approach and just
delete it.

## More info

This bot is being run from user /u/switcharoohelper. If the r/switcharoo mods would 
like to use it for something else, I will send them the account.

## To do
* Switch config from json to configparser
* Search for correct comment when linked incorrectly
