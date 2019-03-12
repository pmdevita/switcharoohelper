# The submission link does not have a ?context suffix
submission_lacks_context = 1

# The submission linked a thread, not a comment
submission_linked_thread = 2

# The submission links to a deleted comment
comment_deleted = 3

# The submission links to a comment with no link
comment_has_no_link = 4

# The switcharoo comment is linked to the wrong thing
comment_linked_wrong = 5

# The switcharoo comment link does not have the ?context suffix
comment_lacks_context = 6

# The switcharoo was correctly linked to a bad roo. Ask for edit to new one
comment_linked_bad_roo = 7

# The switcharoo tried to have multiple sections of url params (multiple '?')
submission_multiple_params = 8

# The switcharoo had a slash at the end of the params
submission_link_final_slash = 9

# The submission links outside of reddit
submission_not_reddit = 10

# The submission is a meta post when it should have been a link
submission_is_meta = 11

# The submission has linked the post on r/switcharoo, not the link
submission_linked_post = 12

issues = [
    # The submission link does not have a ?context suffix
    {"type": "submission_lacks_context", "bad": True},

    # The submission linked a thread, not a comment
    {"type": "submission_linked_thread", "bad": True},

    # The submission links to a deleted comment
    {"type": "comment_deleted", "bad": True},

    # The submission links to a comment with no link
    {"type": "comment_has_no_link", "bad": True},

    # The switcharoo comment is linked to the wrong thing
    {"type": "comment_linked_wrong", "bad": False},

    # The switcharoo comment link does not have the ?context suffix
    {"type": "comment_lacks_context", "bad": False},

    # The switcharoo was correctly linked to a bad roo. Ask for edit to new one
    {"type": "comment_linked_bad_roo", "bad": False},

    # The switcharoo tried to have multiple sections of url params (multiple '?')
    {"type": "submission_multiple_params", "bad": True},

    # The switcharoo had a slash at the end of the params
    {"type": "submission_link_final_slash", "bad": True},

    # The submission links outside of reddit
    {"type": "submission_not_reddit", "bad": True},

    # The submission is a meta post when it should have been a link
    {"type": "submission_is_meta", "bad": True},

    # The submission has linked the post on r/switcharoo, not the link
    {"type": "submission_linked_post", "bad": True},

    # The r/switcharoo submission has been deleted
    {"type": "submission_deleted", "bad": True}
]

issues_dict = {}

for i, issue in enumerate(issues):
    issues_dict[issue['type']] = i
