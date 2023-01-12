# Switcharoo Check Up script

## Introduction

The switcharoo check_up.py script can be used to create services for checking up on older submissions for changes or 
to remind users to fix something.

## Process

The check up script by default performs the following steps. Starting from the newest roo 
in the database and going chronologically older in batches of 50:

1. Determine if roos now have "bad" issues. The database is then updated and roos are removed.
2. Review set of roos again, updating all issues in database, then issuing new requests for new issues and 
reminders for issues not yet fixed.

## Arguments

* `--starting-roo`, `-s` Tells the script to start from the Roo with the given ID. Can also be "last" to be
  the newest roo.
* `--limit`, `-l` Review this many roos and then end
* `--double-check-link`, `-c` Enables a tool to double-check that the Roo's comment as given in the database is linked 
correctly from the submission. Useful for correcting the data for switcharoo's that linked the wrong comment.
If the roo submission was deleted, it'll also ask if you want to reapprove it (this will drop the submission_deleted 
issue later after the rescan).
* `--no-relink`, `-r` Disables asking users to relink their roos. Useful for only updating the database without 
messaging users to ask them to fix, which you may want to do for old roos as their users tend to be grumpier.
* `--no-delete-check`, `-d` Disables the bad issues check, which increases processing speed. However, this can cause 
issues with relinking requests as the bot may ask a user to link to a roo that is not yet known to be bad.
* `--unmute-delete`, `-u` By default, users are not notified that their roos is removed. Enabling this enables the 
mod removal comment for deletions.
* `--include-meta`, `-i` Include meta posts in check up
* `--date-limit`, `-t` Datetime to stop at in ISO format. Check is done up to this time but not on or past it (>)