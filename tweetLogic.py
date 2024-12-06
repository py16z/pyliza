import os
import sys

from twitter.twitterClient import TwitterClient
from twitter.twitterInteractions import TwitterInteractionHandler

from helpers import getResponse, prepareContext, log_message, reflectThoughts, getUserContext, updateUserContext, fetch_context

import chromadb

import time
from dotenv import load_dotenv

import config

import json
import random
from scrape import updateContext

chroma_db_path = os.path.join(os.getcwd(), "chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)

def runTweetLoop(): 

    ponderThoughts()
    r = random.randint(0, 100)
    if r < 10:
        tweet_to_followers()
    elif r < 40 : 
        search_tweets()
    else:
        reply_guy()

    print("Finished tweet loop")


def loadLinks():
    try : 
        links = json.load(open("articles.json"))
        return links["links"]
    except Exception as e:
        print(f"Error: {e}")
        return []


def initTwitterClients(chroma): 
    client = TwitterClient(
        username=config.userName,
        password=os.getenv('TWITTER_PASSWORD'),
        email=os.getenv('TWITTER_EMAIL'),
        chroma_client=chroma,
        postLogger=log_message
    )

    interaction_handler = TwitterInteractionHandler(
        client,
        response_generator=getResponse,
        chroma_client=chroma,
        getUserContext=getUserContext,
        updateUserContext=updateUserContext,
        fetchContext=fetch_context,
        reply_targets=config.reply_targets,
        search_terms=config.search_terms

    )

    return client, interaction_handler

def getCurrentThoughts():
    thoughtProcess = json.load(open("initial_thoughts.json"))
    thoughts = thoughtProcess["thought_process"]
    return thoughts

def ponderThoughts():

    last_tweet = json.load(open("last_tweet.json"))
    last_tweet_time = last_tweet["last_tweet"]

    print("Time since last tweet: ", time.time() - last_tweet_time)
    if time.time() - last_tweet_time < config.postFrequency:
        print("Not posting tweet, too soon...")
        return

    print("Updating context...")
    thoughts = getCurrentThoughts()
    links = loadLinks()

    if (len(links) > 0):
        i = random.randint(0, len(links) - 1)
        link = links[i]
        links.pop(i)
        print("Updating context with link: ", link)
        updateContext(links=[link], thoughtProcess=thoughts)
    else:
        updateContext(thoughtProcess=thoughts)
    
    thoughts = getCurrentThoughts()

    print("Pondering thoughts...")
    try:
        reflectThoughts(additionalContext=thoughts)
        client, interaction_handler = initTwitterClients(chromaClient)
        ### Log history to Chroma DB
        #log_message(chromaClient, thoughts, "user")
        print("Posting thoughts.....")
        tweet = getResponse(config.postPrompt, additionalContext=thoughts)
        print("Tweet: ", tweet)
        client.send_tweet(tweet)
        last_tweet["last_tweet"] = time.time()
        message = f"""
        You tweeted : {tweet}
        """
        log_message(chromaClient, message)

        with open("articles.json", "w") as f:
            json.dump({"links": links}, f)

        with open("last_tweet.json", "w") as f:
            json.dump(last_tweet, f)

    except Exception as e:
        print(f"Error: {e}")


def post_tweet():
    
    last_tweet = json.load(open("last_tweet.json"))
    last_tweet_time = last_tweet["last_tweet"]

    if time.time() - last_tweet_time < config.postFrequency:
        print("Not posting tweet, too soon...")
        return
    


    print("Posting tweet...")
    context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())

    try :
        tweet = getResponse(config.postPrompt, additionalContext=context)
        print("Tweet: ", tweet)

        client, interaction_handler = initTwitterClients(chromaClient)

        log_message(chromaClient, tweet, "user")

        client.send_tweet(tweet)
    except Exception as e:
        print(f"Error: {e}")


def tweet_to_followers():
    print("Tweeting to followers...")
    try:
        client, interaction_handler = initTwitterClients(chromaClient)
        interaction_handler.tweet_to_followers()
    except Exception as e:
        print(f"Error: {e}")

def reply_guy():
    print("Replying to reply guy targets...")
    try:
        client, interaction_handler = initTwitterClients(chromaClient)
        context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())
        interaction_handler.reply_guy(additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")    

def search_tweets():
    try:
        client, interaction_handler = initTwitterClients(chromaClient)
        context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())
        interaction_handler.monitor_mentions(additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")
    
