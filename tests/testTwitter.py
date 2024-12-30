import os
import json
from twitter.twitterClient import TwitterClient
from twitter.twitterInteractions import TwitterInteractionHandler

from helpers import getResponse, chromaClient

import chromadb

def main():
    print("Initializing Twitter client...")
    
    try:
        client = TwitterClient(
            username=os.getenv('TWITTER_USERNAME'),
            password=os.getenv('TWITTER_PASSWORD'),
            email=os.getenv('TWITTER_EMAIL'),
            poll_interval=int(os.getenv('TWITTER_POLL_INTERVAL', 120)),
            chroma_client=chromaClient
        )

        # Search for tweets
        tweets = client.search_tweets("@0xricebowl", max_tweets=20)
        print(f"\nFound {len(tweets)} tweets")
        for tweet in tweets:
            print(f"\n@{tweet['username']}: {tweet['text']}")
            
        interaction_handler = TwitterInteractionHandler(
            client,
            response_generator=getResponse,
            chroma_client=chromaClient
        )
        interaction_handler.monitor_mentions()

    except Exception as e:
        print(f"Error: {e}")
        

        
if __name__ == "__main__":
    main()