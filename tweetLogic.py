import os
import sys

from twitter.twitterClient import TwitterClient
from twitter.twitterInteractions import TwitterInteractionHandler

from helpers import getResponse, prepareContext, log_message, reflectThoughts, getUserContext, updateUserContext, fetch_context, fetch_history, getCurrentThoughts, updatePersona

import chromadb

import time
from dotenv import load_dotenv

import config

from onChainReader import monitorChain, processLogs

import json
import random
from scrape import updateContext

chroma_db_path = os.path.join(os.getcwd(), "chromadb")
chromaClient = chromadb.PersistentClient(path=chroma_db_path)

def runTweetLoop(): 

    if not config.TESTMODE:
        logs = monitorChain()
        processLogs(logs)

        if checkQueuedTweets():
            processQueuedTweets()
        else:
            ponderThoughts()
    
    r = random.randint(0, 100)
    if r < 25 : 
        search_tweets()
    elif r <75 : 
        reply_to_followers()
    else:
        reply_guy()

    print("Finished tweet loop")


def checkQueuedTweets():
    try : 
        queuedTweets = json.load(open("queuedTweets.json"))
        print("Tweets in queue: ", len(queuedTweets["tweets"]))

        ### CHeck time since last tweet
        try : 
            last_tweet = json.load(open("last_tweet.json"))
            last_tweet_time = last_tweet["last_tweet"]
            if time.time() - last_tweet_time < config.postFrequency:
                print("Not posting tweet, too soon...")
                return False
        except Exception as e:
            print(f"Error: {e}")

        return len(queuedTweets["tweets"]) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def processQueuedTweets():
    try : 
        print("Processing queued tweets...")
        queuedTweets = json.load(open("queuedTweets.json"))
        instructions = queuedTweets["tweets"][0]
        print("Posting tweet based on instructions: ", instructions)
        post_tweet(instructions=instructions)
        
        queuedTweets["tweets"].pop(0)
        json.dump(queuedTweets, open("queuedTweets.json", "w"))
    except Exception as e:
        print(f"Error: {e}")
        return False


def loadLinks():
    try : 
        links = json.load(open("articles.json"))
        return links["links"]
    except Exception as e:
        print(f"Error: {e}")
        return config.links


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


def ponderThoughts():

    last_tweet = json.load(open("last_tweet.json"))
    last_tweet_time = last_tweet["last_tweet"]

    print("Time since last tweet: ", time.time() - last_tweet_time)
    if time.time() - last_tweet_time < config.ponderFrequency:
        print("Not posting tweet, too soon...")
        return

    print("Updating context...")
    thoughts = getCurrentThoughts()
    links = loadLinks()

    ### SKIP THIS AS FIRECRAWL BUGGING OUT 
    if (len(links) > 0):
        i = random.randint(0, len(links) - 1)
        link = links[i]
        links.pop(i)
        print("Updating context with link: ", link)
        updateContext(ChromaClient=chromaClient, links=[link], thoughtProcess=thoughts)
    else:
        updateContext(ChromaClient=chromaClient, thoughtProcess=thoughts)
    
    thoughts = getCurrentThoughts()


    print("Pondering thoughts...")
    try:
        history = fetch_history(chromaClient, nRecords=10)
        
        reflectThoughts(additionalContext=history)
        client, interaction_handler = initTwitterClients(chromaClient)
        log_message(chromaClient, thoughts, "user", collectionName="Thoughts")
        print("Posting thoughts.....")
        tweet = getResponse(config.getPostPrompt(), additionalContext=thoughts)
        #print("Tweet: ", tweet)
        client.post_tweet(tweet)
        #client.post_tweet(getCurrentThoughts())
        last_tweet["last_tweet"] = time.time()
        message = f"""
        You tweeted : {tweet}
        """
        log_message(chromaClient, message)

        with open("articles.json", "w") as f:
            json.dump({"links": links}, f, indent=4)

        with open("last_tweet.json", "w") as f:
            json.dump(last_tweet, f, indent=4)

        context = prepareContext(thoughts, chromaClient, thoughtProcess=thoughts)
        updatePersona(chromaClient, additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")


def post_tweet(instructions=""):
    
    last_tweet = json.load(open("last_tweet.json"))
    last_tweet_time = last_tweet["last_tweet"]

    if time.time() - last_tweet_time < config.postFrequency:
        print("Not posting tweet, too soon...")
        return
    
    print("Posting tweet...")
    context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())

    try :
        tweet = getResponse(config.getPostPrompt(instructions=instructions), additionalContext=context)
        print("Tweet: ", tweet)

        client, interaction_handler = initTwitterClients(chromaClient)

        log_message(chromaClient, tweet, "user")

        client.post_tweet(tweet)
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

def reply_to_followers():
    print("Replying to followers...")
    try:
        client, interaction_handler = initTwitterClients(chromaClient)
        context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())
        interaction_handler.reply_to_followers(additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")    


def search_tweets():
    try:
        client, interaction_handler = initTwitterClients(chromaClient)
        context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())
        interaction_handler.monitor_mentions(additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")
    
