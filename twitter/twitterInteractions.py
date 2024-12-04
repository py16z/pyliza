import json
import time
from typing import Optional, Dict, List, Any
from datetime import datetime
import os

class TwitterInteractionHandler:
    def __init__(self, twitter_client, response_generator=None, chroma_client=None):
        self.client = twitter_client
        self.response_generator = response_generator or self.default_response
        self.last_checked_tweet_id = self.load_last_checked_tweet_id()
        self.chroma_client = chroma_client
        self.search_terms = ["@0xricebowl"]
        
        
    def load_last_checked_tweet_id(self) -> Optional[int]:
        """Load the ID of the last checked tweet from file"""
        try:
            with open('last_checked_tweet.json', 'r') as f:
                data = json.load(f)
                return data.get('last_checked_tweet_id')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def save_last_checked_tweet_id(self, tweet_id: int):
        """Save the ID of the last checked tweet"""
        with open('last_checked_tweet.json', 'w') as f:
            json.dump({'last_checked_tweet_id': tweet_id}, f)

    def log_response(self, original_tweet_id: str, response_tweet_id: str, tweet_content: str, response_text: str):
        """Log when we've responded to a tweet"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'original_tweet_id': original_tweet_id,
            'response_tweet_id': response_tweet_id,
            'tweet_content': tweet_content,
            'response_text': response_text
        }
        
        if self.chroma_client:
            client = self.chroma_client
            collection = client.get_or_create_collection("tweet_responses")
            collection.add(
                ids = [original_tweet_id],
                documents = [tweet_content],
                metadatas = [log_entry]
            )
            print("Successfully logged response to Chroma DB")

            

    def has_responded_to_tweet(self, tweet_id: str) -> bool:
        """Check if we've already responded to a tweet"""
        try:
            client = self.chroma_client
            collection = client.get_or_create_collection("tweet_responses")
            results = collection.query(
                query_texts=[tweet_id],
                n_results=1
            )
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def default_response(self, tweet_text: str) -> str:
        """Default response if no response generator is provided"""
        return "Hi there! I'm Rice "

    def generate_response(self, tweet_text: str) -> str:
        """Generate a response using the provided response generator"""
        return self.response_generator(tweet_text)

    def check_mentions(self, searchTerm : str):
        """Check for new mentions and respond to them"""
        username = os.getenv('TWITTER_USERNAME')
        print(f"Checking mentions for @{username}")
        
        try:
            # Use the same search query format that works in your test
            search_response = self.client.search_tweets(searchTerm, max_tweets=20)
            
            # Add debug logging to help diagnose
            print(f"Raw search response: {json.dumps(search_response, indent=2)}")
            
            if not search_response:
                print("No new mentions found")
                return
                
            # Filter and sort tweets
            tweets = sorted(
                [tweet for tweet in search_response 
                 if int(tweet['id']) > (self.last_checked_tweet_id or 0)],
                key=lambda x: int(x['id'])
            )
            
            for tweet in tweets:
                tweet_id = tweet['id']
                
                # Skip if we've already responded to this tweet
                if self.has_responded_to_tweet(tweet_id):
                    print(f"Already responded to tweet {tweet_id}")
                    continue
                
                # Skip our own tweets
                if tweet['username'] == username:
                    continue
                
                print(f"Processing tweet {tweet_id} from @{tweet['username']}")
                tweetContent = tweet['text']
                print("TWEET CONTENT: ", tweetContent)
                # Generate and send response
                response_text = self.generate_response(tweetContent)
                print("RESPONSE TEXT: ", response_text)

                #response = self.client.send_tweet(response_text, tweet_id)
                responseId = "XOXOXOX"
                
                ### Log Response to Chroma DB
                self.log_response(original_tweet_id=tweet_id, response_tweet_id=responseId, tweet_content=tweetContent, response_text=response_text)
                # Wait a bit between responses to avoid rate limiting
                time.sleep(5)
                
        except Exception as e:
            print(f"Error checking mentions: {str(e)}")

    def monitor_mentions(self, check_interval: int = 120):
        """Start monitoring mentions at regular intervals"""
        print("Starting mention monitoring...")
        
        try:
            for searchTerm in self.search_terms:
                self.check_mentions(searchTerm)
                bufferInterval = 5
                time.sleep(bufferInterval)
            time.sleep(check_interval)  # Wait between checks
        except Exception as e:
            print(f"Error in mention monitoring loop: {str(e)}")
