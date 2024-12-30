import os
import sys

import discord
from discord.ext import tasks

from fastapi import FastAPI

import chromadb

import time
from dotenv import load_dotenv

import config

import json

from scrape import updateContext
from tweetLogic import runTweetLoop

app = FastAPI()
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


@app.get("/")
async def hello_fly():
    return 'hello from fly.io'

# intents = discord.Intents.default()
# intents.message_content = True
# bot = discord.Client(intents=intents)


# @bot.event
# async def on_ready():
#     print(f"Logged in as {bot.user}")


# @bot.event
# async def on_message(message):
#     print(f"Received message: {message.content}")
#     if message.author == bot.user:
#         return
#     ### TO DO - add discord logic here for responding to messages 




while True:

    start_time = time.time()
    try : 
        runTweetLoop()
    except Exception as e:
        print(e)
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Time taken: {duration} seconds")
    time.sleep(max(60, 120 - duration))