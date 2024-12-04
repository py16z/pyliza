import json
import time
from typing import Optional, Dict, List, Any
from datetime import datetime
import os

class TwitterInteractionHandler:
    def __init__(self, twitter_client, response_generator=None):
        self.client = twitter_client
        self.response_generator = response_generator or self.default_response
        self.last_checked_tweet_id = self.load_last_checked_tweet_id()
        self.chroma_client = twitter_client.chroma_client
        
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
        return "Hi there! I'm Rice 🍚"

    def generate_response(self, tweet_text: str) -> str:
        """Generate a response using the provided response generator"""
        return self.response_generator(tweet_text)

    def check_mentions(self):
        """Check for new mentions and respond to them"""
        username = os.getenv('TWITTER_USERNAME')
        print(f"Checking mentions for @{username}")
        
        try:
            # Search for tweets mentioning the username
            search_response = self.client.search_tweets(f"@{username}", max_tweets=20)
            
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

                #response = self.client.send_tweet(response_text, reply_to_tweet_id=tweet_id)
                # CREATED MOCK RESPONSE
                response = {
                    "id": "1234567890"
                }

                try : 
                    response_data = response.json()
                    response_tweet_id = response_data['id']
                    print(f"Sent response {response_tweet_id} to tweet {tweet_id}")
                    # Log the response
                    self.log_response(tweet_id, response_tweet_id)
                except Exception as e:
                    print(f"Failed to send response to tweet {tweet_id}")
                
                # Update the last checked tweet ID
                self.last_checked_tweet_id = max(int(tweet_id), self.last_checked_tweet_id or 0)
                self.save_last_checked_tweet_id(self.last_checked_tweet_id)
                
                # Wait a bit between responses to avoid rate limiting
                time.sleep(2)
                
        except Exception as e:
            print(f"Error checking mentions: {str(e)}")

    def start_mention_monitoring(self, check_interval: int = 120):
        """Start monitoring mentions at regular intervals"""
        print("Starting mention monitoring...")
        
        while True:
            try:
                self.check_mentions()
                time.sleep(check_interval)  # Wait between checks
            except Exception as e:
                print(f"Error in mention monitoring loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying on error