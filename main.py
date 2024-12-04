import os

import discord
from discord.ext import tasks

from fastapi import FastAPI

from twitter.twitterClient import TwitterClient
from twitter.twitterInteractions import TwitterInteractionHandler

from helpers import getResponse, prepareContext, log_message, reflectThoughts

import chromadb

import time
from dotenv import load_dotenv

import config

import json

chroma_db_path = os.path.join(os.getcwd(), "chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)


app = FastAPI()
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

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


# EVENT LISTENER FOR WHEN A NEW MESSAGE IS SENT TO A CHANNEL.
@bot.event
async def on_message(message):

    if bot.user.mentioned_in(message):

        ### TO DO - have some logic to get relevant context i.e. fetch from chroma etc 
        try : 
            context = ""
            response = getResponse(message.content, additionalContext="")
            await send_long_message(message.channel, response)

        except Exception as e:
            print(e)
            await send_long_message(message.channel, "REEEEEEEEEE I'M BROKEN")


def getCurrentThoughts():
    thoughtProcess = json.load(open("initial_thoughts.json"))
    thoughts = thoughtProcess["thought_process"]
    return thoughts

@tasks.loop(seconds=config.ponderFrequency)
async def ponderThoughts():
    print("Pondering thoughts...")
    try:
        reflectThoughts()
    except Exception as e:
        print(f"Error: {e}")


@tasks.loop(seconds=config.postFrequency)
async def post_tweet():
    
    print("Posting tweet...")
    thoughtProcess = json.load(open("initial_thoughts.json"))
    thoughts = thoughtProcess["thought_process"]

    context = prepareContext(thoughts, chromaClient)

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
            reply_targets=config.reply_targets
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
            search_terms=config.search_terms
        )
        context = prepareContext(getCurrentThoughts(), chromaClient)
        interaction_handler.monitor_mentions(additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")
    


@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')
    ponderThoughts.start()
    post_tweet.start()
    search_tweets.start()
    reply_guy.start()


bot.run(DISCORD_TOKEN)
