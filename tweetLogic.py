import os
import sys

from twitter.twitterClient import TwitterClient
from twitter.twitterInteractions import TwitterInteractionHandler

from helpers import getResponse, prepareContext, log_message, reflectThoughts, getUserContext, updateUserContext, fetch_context, fetch_history, getCurrentThoughts, updatePersona, getChromaClient

import chromadb

import time
from dotenv import load_dotenv

import config

from onChainReader import monitorChain, processLogs

import json
import random
from scrape import updateContext

from search import search

chromaClient = getChromaClient()

def runTweetLoop(): 

    if not config.TESTMODE:
        # ponderThoughts()
        try : 
            # NOTE : Need to have logic set up for monitoring events + mapping to functions
            logs = monitorChain()
            processLogs(logs)
        except Exception as e:
            print(f"Error: {e}")
        if checkQueuedTweets():
            #processQueuedTweets()
            print("Skipping queued tweets")
    
    search_tweets()
    
    r = random.randint(0, 100)

    if r < 10 : 
        reply_to_followers()
    else:
        reply_guy()

    print("Finished tweet loop")

def reply_topics():
    print("Replying to topics...")
    try:
        client, interaction_handler = initTwitterClients(chromaClient)
        interaction_handler.reply_topics()
    except Exception as e:
        print(f"Error: {e}")

def checkQueuedTweets():
    try : 
        queuedTweets = json.load(open("data/queuedTweets.json"))
        print("Tweets in queue: ", len(queuedTweets["tweets"]))

        ### CHeck time since last tweet
        try : 
            last_tweet = json.load(open("data/last_tweet.json"))
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
        queuedTweets = json.load(open("data/queuedTweets.json"))
        instructions = queuedTweets["tweets"][0]
        print("Posting tweet based on instructions: ", instructions)
        post_tweet(instructions=instructions, useSearch=True)
        
        queuedTweets["tweets"].pop(0)
        json.dump(queuedTweets, open("data/queuedTweets.json", "w"))
    except Exception as e:
        print(f"Error: {e}")
        return False


def loadLinks():
    try : 
        links = json.load(open("data/articles.json"))
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
        reply_targets=config.getReplyGuyTargets(),
        topics=config.getTopics(),
        search_terms=config.search_terms,
        ignore_users=config.ignore_users,
    )

    return client, interaction_handler


def ponderThoughtsViaSearch():

    message = "Refect on your current thoughts process & decide what are potential future areas of interest to explore / additional information you could search for to "
    thoughts = getCurrentThoughts()
    context = prepareContext(thoughts, chromaClient, thoughtProcess=thoughts)
    query, searchResults = search(chromaClient, message=message, context=context)

    print("Query: ", query)
    print("Search Results: ", searchResults)


    history = fetch_history(chromaClient, nRecords=10)

    additionalContext = f"""
    Here is a history of your recent interactions 
    {history}

    Additionally you recently completed the following search 
    {query}

    The results of the search are as follows 
    {searchResults}
    """


    updatedThoughts = reflectThoughts(additionalContext=additionalContext, saveThoughts=False)

    print("Updated Thoughts: ", updatedThoughts)

    return updatedThoughts


def ponderThoughts(postTweet = True):

    last_tweet = json.load(open("data/last_tweet.json"))
    last_tweet_time = last_tweet["last_tweet"]

    print("Time since last tweet: ", time.time() - last_tweet_time)
    if time.time() - last_tweet_time < config.ponderFrequency:
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
        updateContext(ChromaClient=chromaClient, links=[link], thoughtProcess=thoughts)
    else:
        updateContext(ChromaClient=chromaClient, thoughtProcess=thoughts)
    
    thoughts = getCurrentThoughts()


    print("Pondering thoughts...")
    try:
        history = fetch_history(chromaClient, nRecords=5)
        
        reflectThoughts(additionalContext=history)
        client, interaction_handler = initTwitterClients(chromaClient)
        log_message(chromaClient, thoughts, "user", collectionName="Thoughts")
        print("Posting thoughts.....")
        tweet = getResponse(config.getPostPrompt(), additionalContext=thoughts)
        print("Tweet: ", tweet)
        if postTweet:
            client.post_tweet(tweet)
            #client.post_tweet(getCurrentThoughts())
            last_tweet["last_tweet"] = time.time()
            message = f"""
            You tweeted : {tweet}
            """
            log_message(chromaClient, message)

            with open("data/articles.json", "w") as f:
                json.dump({"links": links}, f, indent=4)

            with open("data/last_tweet.json", "w") as f:
                json.dump(last_tweet, f, indent=4)

        #context = prepareContext(thoughts, chromaClient, thoughtProcess=thoughts)
        #updatePersona(chromaClient, additionalContext=context)

    except Exception as e:
        print(f"Error: {e}")


def post_tweet(instructions="", useSearch=False):
    
    last_tweet = json.load(open("data/last_tweet.json"))
    last_tweet_time = last_tweet["last_tweet"]

    if time.time() - last_tweet_time < config.postFrequency:
        print("Not posting tweet, too soon...")
        return
    
    print("Posting tweet...")
    context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())

    if useSearch : 
        query, searchResults = search(chromaClient, message=instructions, context=context)
        searchContext = f"""
        Note to help you with your next response you complete the following search 
        {query}

        The results of the search are as follows 
        {searchResults}
        """
        context = context + searchContext

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
    tracker = json.load(open("data/last_tweet.json"))
    last_search_time = tracker["last_reply"]

    if time.time() - last_search_time < config.replyGuyFrequency:
        print("Not searching tweets, too soon...")
        return
    print("Replying to reply guy targets...")
    try:
        client, interaction_handler = initTwitterClients(chromaClient)
        context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())
        interaction_handler.reply_guy(additionalContext=context)
        tracker["last_reply"] = time.time()
        with open("data/last_tweet.json", "w") as f:
            json.dump(tracker, f, indent=4)

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

    tracker = json.load(open("data/last_tweet.json"))
    last_search_time = tracker["last_search"]
    

    if time.time() - last_search_time < config.searchFrequency:
        print("Not searching tweets, too soon...")
        return
    
    try:
        client, interaction_handler = initTwitterClients(chromaClient)
        context = prepareContext(getCurrentThoughts(), chromaClient, thoughtProcess=getCurrentThoughts())
        interaction_handler.monitor_mentions(additionalContext=context)

        tracker["last_search"] = time.time()
        with open("data/last_tweet.json", "w") as f:
            json.dump(tracker, f, indent=4)

    except Exception as e:
        print(f"Error: {e}")
    
