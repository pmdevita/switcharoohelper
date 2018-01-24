# Switcharoo Helper

Verifies the switcharoo chain is correctly linked and unbroken. This bot focuses 
on verifying new additions to the chain. A future project may verify the chain 
going down.

## How it works

### Basic Logic
When someone posts a comment to r/switcharoo, the bot

* Checks the link
    * is to a comment that
        * is a correct link to the previous switcharoo
        * is not a duplicate (future feature)
    * has the `?context=x` end

I have yet to find a duplicate link to test how such a thing would happen. I did 
find a duplicate but strangely it lacked a submission.

We can (theoretically) check a link is not a duplicate by

* Check if link to thread (not just comment) has been posted
    * Check if link is to identical comment
    * Check if link is under the same parent comment

### Recommendations for action

If the switcharoo post is just missing the `?context=` add-on, comment on 
it to alert the poster and flair it to alert the next switcharoo poster in the 
chain. We could delete it if we want to take a very strong approach to preserving
the chain but hopefully the OP would be responsive.

If it is an exact duplicate link or only separated by one level of comments, delete 
it. If it separated by more levels, comment on it to alert the poster and flair it 
to alert the next switcharoo poster in the chain.

## More info

This bot is being run from user /u/switcharoohelper. If the r/switcharoo mods would 
like to use it for something else, I will send them the account.