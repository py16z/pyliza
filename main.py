import os
import sys

import discord
from discord.ext import tasks

from fastapi import FastAPI

from twitter.twitterClient import TwitterClient
from twitter.twitterInteractions import TwitterInteractionHandler

from helpers import getResponse, prepareContext, log_message, reflectThoughts, getUserContext, updateUserContext

import chromadb

import time
from dotenv import load_dotenv

import config

import json

from scrape import updateContext

chroma_db_path = os.path.join(os.getcwd(), "chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)


app = FastAPI()
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

class MyBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bg_tasks = []

    async def setup_hook(self):
        # Start background tasks
        self.bg_tasks.append(ponderThoughts.start())
        self.bg_tasks.append(search_tweets.start())
        self.bg_tasks.append(reply_guy.start())

    async def on_ready(self):
        print(f'Bot logged in as {self.user}')

    async def on_disconnect(self):
        print("Bot disconnected. Attempting to reconnect...")

    async def on_message(self, message):
        if self.user.mentioned_in(message):
            try:
                context = ""
                response = getResponse(message.content, additionalContext="")
                await send_long_message(message.channel, response)
            except Exception as e:
                print(f"Error handling message: {e}")
                await send_long_message(message.channel, "REEEEEEEEEE I'M BROKEN")

@app.get("/")
async def hello_fly():
    return 'hello from fly.io'


def split_message(message, limit=2000):
    """Split a message into chunks of maximum length."""
    if len(message) <= limit:
        return [message]
    
    chunks = []
    while message:
        if len(message) <= limit:
            chunks.append(message)
            break
        
        # Find the last space before the limit
        split_index = message.rfind(' ', 0, limit)
        if split_index == -1:
            split_index = limit
        
        chunks.append(message[:split_index])
        message = message[split_index:].lstrip()
    
    return chunks

async def send_long_message(channel, message, updateChannel=""):
    chunks = split_message(message)
    for chunk in chunks:
        await channel.send(chunk)
        print(chunk)


def getCurrentThoughts():
    thoughtProcess = json.load(open("initial_thoughts.json"))
    thoughts = thoughtProcess["thought_process"]
    return thoughts

@tasks.loop(seconds=config.ponderFrequency)
async def ponderThoughts():

    last_tweet = json.load(open("last_tweet.json"))
    last_tweet_time = last_tweet["last_tweet"]

    if time.time() - last_tweet_time < config.postFrequency:
        print("Not posting tweet, too soon...")
        return

    print("Updating context...")
    thoughts = getCurrentThoughts()
    updateContext(thoughtProcess=thoughts)
    thoughts = getCurrentThoughts()

    print("Pondering thoughts...")
    try:
        reflectThoughts(additionalContext=thoughts)
        client = TwitterClient(
            username=config.userName,
            password=os.getenv('TWITTER_PASSWORD'),
            email=os.getenv('TWITTER_EMAIL'),
        )
        ### Log history to Chroma DB
        #log_message(chromaClient, thoughts, "user")
        print("Posting thoughts.....")
        tweet = getResponse(config.postPrompt, additionalContext=thoughts)
        print("Tweet: ", tweet)
        client.send_tweet(tweet)
        last_tweet["last_tweet"] = time.time()

    except Exception as e:
        print(f"Error: {e}")


@tasks.loop(seconds=config.postFrequency)
async def post_tweet():
    
    last_tweet = json.load(open("last_tweet.json"))
    last_tweet_time = last_tweet["last_tweet"]

    if time.time() - last_tweet_time < config.postFrequency:
        print("Not posting tweet, too soon...")
        return
    


    print("Posting tweet...")
    context = prepareContext(getCurrentThoughts(), chromaClient)

    try :
        tweet = getResponse(config.postPrompt, additionalContext=context)
        print("Tweet: ", tweet)
        client = TwitterClient(
            username=os.getenv('TWITTER_USERNAME'),
            password=os.getenv('TWITTER_PASSWORD'),
            email=os.getenv('TWITTER_EMAIL'),
        )
        ### Log history to Chroma DB
        log_message(chromaClient, tweet, "user")

        client.send_tweet(tweet)
    except Exception as e:
        print(f"Error: {e}")

@tasks.loop(seconds=config.replyGuyFrequency)
async def reply_guy():
    print("Replying to reply guy targets...")
    try:
        client = TwitterClient(
            username=os.getenv('TWITTER_USERNAME'),
            password=os.getenv('TWITTER_PASSWORD'),
            email=os.getenv('TWITTER_EMAIL'),
            poll_interval=int(os.getenv('TWITTER_POLL_INTERVAL', 120)),
            chroma_client=chromaClient
        )

        interaction_handler = TwitterInteractionHandler(
            client,
            response_generator=getResponse,
            chroma_client=chromaClient,
            search_terms=config.search_terms,
            reply_targets=config.reply_targets,
            getUserContext=getUserContext,
            updateUserContext=updateUserContext
        )
        context = prepareContext(getCurrentThoughts(), chromaClient)
        interaction_handler.reply_guy(additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")    

@tasks.loop(seconds=config.searchFrequency)
async def search_tweets():
    try:
        client = TwitterClient(
            username=os.getenv('TWITTER_USERNAME'),
            password=os.getenv('TWITTER_PASSWORD'),
            email=os.getenv('TWITTER_EMAIL'),
            poll_interval=int(os.getenv('TWITTER_POLL_INTERVAL', 120)),
            chroma_client=chromaClient
        )

        interaction_handler = TwitterInteractionHandler(
            client,
            response_generator=getResponse,
            chroma_client=chromaClient,
            search_terms=config.search_terms,
            getUserContext=getUserContext,
            updateUserContext=updateUserContext
        )
        context = prepareContext(getCurrentThoughts(), chromaClient)
        interaction_handler.monitor_mentions(additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")
    

# Create bot instance with reconnect enabled
intents = discord.Intents.default()
intents.message_content = True
bot = MyBot(intents=intents, reconnect=False)

# Error handling for the bot
@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error in {event}: {sys.exc_info()}")


while True:
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"Bot crashed with error: {e}")
        # Create a new bot instance and run it
        print("Restarting bot...")
        time.sleep(10)

        bot = MyBot(intents=discord.Intents.default(), reconnect=False)
        bot.run(DISCORD_TOKEN)