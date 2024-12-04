import os

import discord
from discord.ext import tasks

from fastapi import FastAPI

from twitter.twitterClient import TwitterClient
from twitter.twitterInteractions import TwitterInteractionHandler

from helpers import getResponse

import chromadb

import time
from dotenv import load_dotenv

import config

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
        interaction_handler.monitor_mentions()

    except Exception as e:
        print(f"Error: {e}")
    

@tasks.loop(seconds=config.postFrequency)
async def post_tweet():
    
    print("Posting tweet...")

    try :
        tweet = getResponse(config.postPrompt, additionalContext="")
        print("Tweet: ", tweet)
        client = TwitterClient(
            username=os.getenv('TWITTER_USERNAME'),
            password=os.getenv('TWITTER_PASSWORD'),
            email=os.getenv('TWITTER_EMAIL'),
        )
        #client.post_tweet(tweet)
    except Exception as e:
        print(f"Error: {e}")


@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')
    post_tweet.start()
    search_tweets.start()


bot.run(DISCORD_TOKEN)
