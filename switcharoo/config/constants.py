bot_name = "SwitcharooHelper"
version = "3.2.3"
user_agent = f"{bot_name} v{version} by /u/pmdevita"
subreddit = "switcharoo"
sleep_time = 120
sleep_time_test = 10
settled_check = 60 * 60 * 24 * 4

ONLY_BAD = 0
ONLY_IGNORED = 1
ALL_ROOS = 2

CONTEXT_HEADER = "/switcharoo-context:"

class FLAIRS:
    PENDING = {"flair_template_id": "393f7464-948a-11ed-ae29-ee9d9b95a22b"}
    CORRECT = {"flair_template_id": "425e042a-948a-11ed-8174-fe97601b3d74"}
    ISSUES = {"flair_template_id": "565afe4c-948a-11ed-8231-c6e52f1114eb"}
    BAD_ISSUES = {"flair_template_id": "76b96cbe-948a-11ed-90dc-ee3e7ec04614"}
