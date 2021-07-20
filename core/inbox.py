import praw
import json
import praw.models
from core.history import SwitcharooLog
from core.parse import REPatterns
from core import constants as consts
from core.action import modmail_action, inbox_action
from core.process import reprocess
from core.reddit import ReplyObject


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


def process_message(reddit: praw.Reddit, last_switcharoo: SwitcharooLog, message: praw.models.Message, action):
    if message.was_comment:
        # Comment reply, maybe a fix?
        body = message.body.lower()
        if "fixed" in body or "done" in body:
            roo = last_switcharoo.get_roo(submission_id=message.submission.id)
            if roo:
                reprocess(reddit, roo, last_switcharoo, action, consts.ALL_ROOS, mute=False,
                          reply_object=ReplyObject.from_roo(roo, message))
            else:
                print(message, "Doesn't exist in db")
            return True
        context = find_context(reddit, message)
        if context:
            roo = last_switcharoo.get_roo(submission_id=message.submission.id)
            reply_object = ReplyObject.from_roo(roo, message)
            response = inbox_action(reply_object, last_switcharoo, context, message)
            if response:
                reply_object.reply("Reply from switcharoohelper", response)
        return True
    else:
        return True


def find_context(reddit, comment):
    if comment.author == reddit.user.me():
        new_context = get_context(comment.body)
        if new_context:
            return new_context
    if isinstance(comment, praw.models.Comment):
        return find_context(reddit, comment.parent())
    else:
        return None


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


