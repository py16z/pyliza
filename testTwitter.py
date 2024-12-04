import os
import json
from twitter.twitterClient import TwitterClient

def main():
    # Initialize client with environment variables
    client = TwitterClient(
        username=os.getenv('TWITTER_USERNAME'),
        password=os.getenv('TWITTER_PASSWORD'),
        email=os.getenv('TWITTER_EMAIL'),
        cookies=os.getenv('TWITTER_COOKIES'),
        poll_interval=int(os.getenv('TWITTER_POLL_INTERVAL', 120))
    )

    # Example: Send a tweet
    try:
        response = client.send_tweet("Hello from Python Twitter Client!")
        print("Tweet sent successfully:", response)
    except Exception as e:
        print("Failed to send tweet:", str(e))


if __name__ == "__main__":
    main()