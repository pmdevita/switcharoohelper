import praw
import json
import praw.models
from core.history import SwitcharooLog
from core.parse import REPatterns
from core import constants as consts
from core.action import modmail_action


def get_context(message):
    matches = REPatterns.link.findall(message)
    if matches:
        for i in matches:
            if i[1][:len(consts.CONTEXT_HEADER)] == consts.CONTEXT_HEADER:
                try:
                    context_json = json.loads(i[1][len(consts.CONTEXT_HEADER):])
                except json.decoder.JSONDecodeError:
                    continue
                return context_json
    return None


def process_message(reddit: praw.Reddit, last_switcharoo: SwitcharooLog, message: praw.models.Message):
    print(message)
    if message.was_comment:
        # Comment reply, maybe a fix?
        if "fixed" in message.body.lower():
            pass
    else:
        pass


def process_modmail(reddit: praw.Reddit, last_switcharoo: SwitcharooLog, conversation):
    if conversation.is_internal:
        context = None
        responded = False
        for i, message in enumerate(conversation.messages):
            if i == 0:
                # This message either needs to be started by the bot or ask for the bot
                if message.author != reddit.user.me():
                    return
            if message.author == reddit.user.me():
                new_context = get_context(message.body_markdown)
                if new_context:
                    context = new_context
        # If we weren't the last to respond, then we were probably commanded to do something
        if message.author != reddit.user.me() and context:
            response = modmail_action(last_switcharoo, context, message.body_markdown)
            if response:
                conversation.reply(response)


