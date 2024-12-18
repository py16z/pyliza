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

chroma_db_path = os.path.join(os.getcwd(), "data/chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)

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



while True:

    start_time = time.time()
    try : 
        runTweetLoop()
    except Exception as e:
        print(e)
    
    end_time = time.time()
    duration = end_time - start_time
    print(f"Time taken: {duration} seconds")
    time.sleep(max(60, 180 - duration))