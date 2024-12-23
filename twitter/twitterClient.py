import requests
import json
import time
from typing import Optional, Dict, List, Any
from datetime import datetime
from urllib.parse import urlencode
import os

from dotenv import load_dotenv

load_dotenv()

import chromadb 

class TwitterClient:
    BASE_URL = "https://twitter.com"
    API_URL = "https://api.twitter.com"
    
    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        email: Optional[str] = None,
        cookies: Optional[str] = None,
        poll_interval: int = 120,
        chroma_client: Optional[chromadb.Client] = None,
        postLogger=None
    ):
        self.username = username
        self.password = password
        self.email = email
        self.poll_interval = poll_interval
        self.session = requests.Session()
        self.bearer_token = "AAAAAAAAAAAAAAAAAAAAAFQODgEAAAAAVHTp76lzh3rFzcHbmHVvQxYYpTw%3DckAlMINMjmCwxUcaXbAN4XqJVdgMJaHqNOFgPMK0zN1qLqLQCF"
        self.chroma_client = chroma_client
        self.postLogger = postLogger
        
        # Set up default headers
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
            "Accept": "*/*"
        })
        
        # Set up cookies directly from environment variables
        auth_token = os.getenv('TWITTER_COOKIES_AUTH')
        ct0_token = os.getenv('TWITTER_COOKIES_CT0')
        guest_id = os.getenv('TWITTER_COOKIES_GUEST_ID')
        
        if auth_token and ct0_token:
            self.session.cookies.set('auth_token', auth_token, domain='.twitter.com', path='/')
            self.session.cookies.set('ct0', ct0_token, domain='.twitter.com', path='/')
            if guest_id:
                self.session.cookies.set('guest_id', guest_id, domain='.twitter.com', path='/')
            
            # Debug print
            print("Session cookies after setup:", self.session.cookies.get_dict())

    def _get_default_features(self) -> Dict[str, bool]:
        """Get default feature flags required by Twitter"""
        return {
            # Core features
            "verified_phone_label_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_enhance_cards_enabled": False,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            
            # Missing required features that caused the error
            "vibe_api_enabled": False,
            "responsive_web_text_conversations_enabled": False,
            "interactive_text_enabled": True,
            "blue_business_profile_image_shape_enabled": False,
            
            # Additional features
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "rweb_tipjar_consumption_enabled": True,
            "articles_preview_enabled": True,
            "creator_subscriptions_quote_tweet_preview_enabled": True,
            "communities_web_enable_tweet_community_results_fetch": True,
            "android_graphql_skip_api_media_color_palette": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            
            # Additional conversation and UI features
            "responsive_web_enhance_cards_enabled": False,
            "unified_cards_ad_metadata_container_dynamic_card_content_query_enabled": False,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "longform_notetweets_rich_text_read_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True
        }
            
    def _setup_cookies(self, cookies_str: str) -> None:
        """Set up session cookies from a cookie string"""
        try:
            # Remove single quotes if present
            cookies_str = cookies_str.strip("'")
            
            # Parse the JSON string
            cookie_list = json.loads(cookies_str)
            
            # Debug print
            print("Parsed cookies:", cookie_list)
            
            for cookie in cookie_list:
                self.session.cookies.set(
                    cookie["name"],
                    cookie["value"],
                    domain=cookie.get("domain", ".twitter.com"),
                    path=cookie.get("path", "/")
                )
            
            # Debug print after setting cookies
            print("Session cookies after setup:", self.session.cookies.get_dict())
            
        except json.JSONDecodeError as e:
            print(f"Error parsing cookies: {e}")
            print(f"Cookie string received: {cookies_str}")
            # Handle raw cookie string format as fallback
            for cookie in cookies_str.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    self.session.cookies.set(name, value, domain=".twitter.com", path="/")
    
    def get_csrf_token(self) -> str:
        """Get CSRF token from cookies"""
        return self.session.cookies.get("ct0", domain=".twitter.com")

    def _update_headers_with_csrf(self) -> None:
        """Update headers with CSRF token"""
        csrf_token = self.get_csrf_token()
        if csrf_token:
            self.session.headers.update({
                "x-csrf-token": csrf_token,
            })



    def search_tweets(self, query: str, max_tweets: int = 20) -> List[Dict]:
        """
        Search for tweets using Twitter's search API
        """
        self._update_headers_with_csrf()
        
        variables = {
            "rawQuery": query,
            "count": min(max_tweets, 40),
            "querySource": "typed_query",
            "product": "Latest",
            "includePromotedContent": False,
            "withDownvotePerspective": False,
            "withReactionsMetadata": False,
            "withReactionsPerspective": False
        }

        features = self._get_default_features()
        
        # Field toggles are also required for some requests
        field_toggles = {
            "withArticleRichContentState": False
        }

        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(features),
            "fieldToggles": json.dumps(field_toggles)
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/i/api/graphql/gkjsKepM6gl_HmFWoWKfgg/SearchTimeline",
                params=params
            )
            
            if response.status_code != 200:
                print(f"Search request failed: {response.text}")
                return []

            data = response.json()
            tweets = []
            
            # Navigate through the response structure
            instructions = data.get('data', {}).get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])
            
            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    for entry in entries:
                        if not entry.get('entryId', '').startswith('tweet-'):
                            continue
                            
                        result = entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                        if not result:
                            continue

                        legacy = result.get('legacy', {})
                        user_result = result.get('core', {}).get('user_results', {}).get('result', {})
                        user_legacy = user_result.get('legacy', {})

                        if not legacy or not user_legacy:
                            continue

                        tweet = {
                            'id': legacy.get('id_str'),
                            'text': legacy.get('full_text'),
                            'username': user_legacy.get('screen_name'),
                            'name': user_legacy.get('name'),
                            'user_id': user_legacy.get('id_str'),
                            'created_at': legacy.get('created_at'),
                            'conversation_id': legacy.get('conversation_id_str'),
                            'in_reply_to_status_id': legacy.get('in_reply_to_status_id_str'),
                            'in_reply_to_user_id': legacy.get('in_reply_to_user_id_str'),
                        }
                        
                        tweets.append(tweet)

            return tweets

        except Exception as e:
            print(f"Error during search: {str(e)}")
            return []

    def _get_default_features_user_profile(self) -> Dict[str, bool]:
        """Get default feature flags required by Twitter"""
        return {
            # Core features
            "verified_phone_label_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_enhance_cards_enabled": False,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            
            # Additional required features for user profile
            "hidden_profile_likes_enabled": False,
            "hidden_profile_subscriptions_enabled": False,
            "highlights_tweets_tab_ui_enabled": True,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "subscriptions_verification_info_is_identity_verified_enabled": True,
            "subscriptions_verification_info_verified_since_enabled": True,
            
            # Other features
            "vibe_api_enabled": False,
            "responsive_web_text_conversations_enabled": False,
            "interactive_text_enabled": True,
            "blue_business_profile_image_shape_enabled": False,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "rweb_tipjar_consumption_enabled": True,
            "articles_preview_enabled": True,
            "creator_subscriptions_quote_tweet_preview_enabled": True,
            "communities_web_enable_tweet_community_results_fetch": True,
            "android_graphql_skip_api_media_color_palette": False,
            "unified_cards_ad_metadata_container_dynamic_card_content_query_enabled": False
        }

    def _get_user_id(self, username: str) -> Optional[str]:
        """
        Get user ID for a given username
        """
        self._update_headers_with_csrf()
        
        variables = {
            "screen_name": username,
            "withSafetyModeUserFields": True,
            "withSuperFollowsUserFields": True,
        }

        features = self._get_default_features_user_profile()
        
        field_toggles = {
            "withAuxiliaryUserLabels": False
        }

        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(features),
            "fieldToggles": json.dumps(field_toggles)
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/i/api/graphql/G3KGOASz96M-Qu0nwmGXNg/UserByScreenName",
                params=params
            )
            
            if response.status_code != 200:
                print(f"Failed to get user ID: {response.text}")
                return None

            data = response.json()
            return data.get('data', {}).get('user', {}).get('result', {}).get('rest_id')
        
        except Exception as e:
            print(f"Error getting user ID: {str(e)}")
            return None
    
    def get_followers(self, username: str, max_followers: int = 100) -> List[Dict]:
        """
        Get followers of a specific Twitter account
        
        Args:
            username (str): Twitter username/handle (without the @ symbol)
            max_followers (int): Maximum number of followers to fetch (default 100)
            
        Returns:
            List[Dict]: List of follower objects containing user data
        """
        # First get the user ID
        user_id = self._get_user_id(username)
        if not user_id:
            print(f"Could not find user ID for username: {username}")
            return []

        self._update_headers_with_csrf()
        
        # Ensure max_followers doesn't exceed reasonable API limits
        max_followers = min(max_followers, 100)
        
        variables = {
            "userId": user_id,
            "count": max_followers,
            "includePromotedContent": False,
            "withSuperFollowsUserFields": True,
            "withDownvotePerspective": False,
            "withReactionsMetadata": False,
            "withReactionsPerspective": False,
            "withSuperFollowsTweetFields": True,
        }

        features = self._get_default_features()

        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(features),
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/i/api/graphql/rRXFSG5vR6drKr5M37YOTw/Followers",
                params=params
            )
            
            if response.status_code != 200:
                print(f"Followers request failed: {response.text}")
                return []

            data = response.json()
            followers = []
            
            # Navigate through the response structure
            instructions = data.get('data', {}).get('user', {}).get('result', {}).get('timeline', {}).get('timeline', {}).get('instructions', [])
            
            for instruction in instructions:
                if instruction.get('type') == 'TimelineAddEntries':
                    entries = instruction.get('entries', [])
                    for entry in entries:
                        # Skip non-user entries
                        if not entry.get('entryId', '').startswith('user-'):
                            continue
                            
                        user_result = entry.get('content', {}).get('itemContent', {}).get('user_results', {}).get('result', {})
                        if not user_result:
                            continue

                        legacy = user_result.get('legacy', {})
                        
                        if not legacy:
                            continue

                        # Extract follower data
                        follower = {
                            'user_id': user_result.get('rest_id'),
                            'username': legacy.get('screen_name'),
                            'name': legacy.get('name'),
                            'description': legacy.get('description'),
                            'followers_count': legacy.get('followers_count'),
                            'following_count': legacy.get('friends_count'),
                            'tweet_count': legacy.get('statuses_count'),
                            'created_at': legacy.get('created_at'),
                            'location': legacy.get('location'),
                            'verified': legacy.get('verified', False),
                            'profile_image_url': legacy.get('profile_image_url_https'),
                            'protected': legacy.get('protected', False)
                        }
                        
                        followers.append(follower)

            return followers
        
        except Exception as e:
            print(f"Error getting followers: {str(e)}")
            return []

    def send_tweet(self, text: str, reply_to_tweet_id: Optional[str] = None) -> dict:
        """Send a tweet or reply to another tweet"""
        # Check for required cookies before proceeding
        auth_token = self.session.cookies.get("auth_token")
        csrf_token = self.session.cookies.get("ct0")
        
        if not auth_token or not csrf_token:
            raise Exception(f"Missing required cookies. auth_token: {'present' if auth_token else 'missing'}, "
                           f"ct0: {'present' if csrf_token else 'missing'}")
        
        self._update_headers_with_csrf()
        
        # Update headers with additional required fields
        self.session.headers.update({
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
            "x-twitter-active-user": "yes",
            "Referer": "https://twitter.com/compose/tweet",
            "Origin": "https://twitter.com",
            "x-csrf-token": csrf_token
        })
        
        # Debug output
        # print("\nRequest Details:")
        # print("Headers:", json.dumps(dict(self.session.headers), indent=2))
        # print("Cookies:", json.dumps(dict(self.session.cookies.get_dict()), indent=2))
        
        variables = {
            "tweet_text": text,
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False
            },
            "semantic_annotation_ids": []
        }

        if reply_to_tweet_id:
            variables["reply"] = {"in_reply_to_tweet_id": reply_to_tweet_id}

        payload = {
            "variables": variables,
            "features": self._get_default_features(),
            "queryId": "a1p9RWpkYKBjWv_I3WzS-A"
        }

        # Check if we have proper authentication
        if not self.session.cookies.get_dict():
            raise Exception("No authentication cookies found. Please provide valid cookies.")

        response = self.session.post(
            f"{self.BASE_URL}/i/api/graphql/a1p9RWpkYKBjWv_I3WzS-A/CreateTweet",
            json=payload
        )
        
        if response.status_code != 200:
            # Add more detailed error information
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response body: {response.text}")
            raise Exception(f"Failed to send tweet: Status {response.status_code} - {response.text}")
            
        return response.json()
    
    def post_tweet(self, text: str, reply_to_tweet_id: Optional[str] = None) -> dict:
        if len(text) > 280:
            print("Long tweet detected")
            return self.send_thread(text, reply_to_tweet_id)
        else:
            return self.send_tweet(text, reply_to_tweet_id)

    def get_tweet(self, tweet_id: str) -> dict:
        """Fetch a specific tweet by ID"""
        self._update_headers_with_csrf()
        
        variables = {
            "focalTweetId": tweet_id,
            "with_rux_injections": False,
            "includePromotedContent": False,
            "withCommunity": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withBirdwatchNotes": False,
            "withVoice": True,
            "withV2Timeline": True
        }

        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(self._get_default_features())
        }

        response = self.session.get(
            f"{self.BASE_URL}/i/api/graphql/xOhkmRac04YFZmOzU9PJHg/TweetDetail",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch tweet: {response.text}")
            
        return response.json()

    def get_user_tweets(self, user_id: str, max_tweets: int = 40) -> List[dict]:
        """Fetch tweets from a specific user"""
        self._update_headers_with_csrf()
        
        variables = {
            "userId": user_id,
            "count": min(max_tweets, 40),
            "includePromotedContent": False,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True
        }

        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(self._get_default_features())
        }

        response = self.session.get(
            f"{self.BASE_URL}/i/api/graphql/V7H0Ap3_Hh2FyS75OCDO3Q/UserTweets",
            params=params
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch user tweets: {response.text}")
            
        return response.json()
            
    def send_thread(self, text: str, reply_to_tweet_id: Optional[str] = None) -> List[dict]:
        """
        Send a long text as a thread of tweets with fixed feature flags
        """
        def split_into_tweets(text: str, max_length: int = 270) -> List[str]:
            """
            Split text into tweets by first breaking into sentences, then combining them into tweets
            that don't exceed max_length.
            """
            # Reduce max_length to account for potential "...cont" suffix
            effective_max_length = max_length - 8  # Leave room for "...cont" suffix
            
            # Split into sentences (handling ., ?, and ! endings)
            sentences = []
            current_sentence = []
            
            # First split by newlines to preserve paragraph structure
            paragraphs = text.split('\n')
            
            for paragraph in paragraphs:
                # Skip empty paragraphs
                if not paragraph.strip():
                    continue
                    
                # Split each paragraph into potential sentences
                raw_sentences = []
                current = []
                
                for char in paragraph:
                    current.append(char)
                    if char in '.!?':
                        # Check if this is really the end (e.g., not "Mr." or "U.S.")
                        sentence = ''.join(current).strip()
                        if not any(abbrev in sentence[-4:] for abbrev in [
                            'Mr.', 'Ms.', 'Mrs.', 'Dr.', 'Jr.', 'Sr.', 'U.S.',
                            'i.e.', 'e.g.', 'etc.', 'vs.'
                        ]):
                            raw_sentences.append(''.join(current).strip())
                            current = []
                
                # Add any remaining text as a sentence
                if current:
                    raw_sentences.append(''.join(current).strip())
                    
                sentences.extend(raw_sentences)
            
            # Now combine sentences into tweets
            tweets = []
            current_tweet = []
            current_length = 0
            
            for sentence in sentences:
                # Skip empty sentences
                if not sentence.strip():
                    continue
                    
                sentence_length = len(sentence.strip())
                
                # If this single sentence is longer than effective_max_length, split it by words
                if sentence_length > effective_max_length:
                    if current_tweet:  # First save any existing tweet content
                        tweets.append("\n".join(current_tweet))
                        current_tweet = []
                        current_length = 0
                    
                    # Split long sentence into words
                    words = sentence.split()
                    temp_tweet = []
                    temp_length = 0
                    
                    for word in words:
                        word_length = len(word) + (1 if temp_length > 0 else 0)  # Add 1 for space
                        
                        # Check if adding this word would exceed the limit
                        if temp_length + word_length <= effective_max_length:
                            if temp_length > 0:
                                temp_tweet.append(" ")
                            temp_tweet.append(word)
                            temp_length += word_length
                        else:
                            # Save current tweet and start new one
                            if temp_tweet:
                                tweets.append(''.join(temp_tweet) + "\n...")
                            temp_tweet = [word]
                            temp_length = len(word)
                    
                    # Add remaining words if any
                    if temp_tweet:
                        current_tweet = temp_tweet
                        current_length = temp_length
                    continue
                
                # For normal sentences, check if adding would exceed limit
                new_length = current_length + (1 if current_length > 0 else 0) + sentence_length
                
                if new_length <= effective_max_length:
                    if current_length > 0:
                        current_tweet.append(" ")
                    current_tweet.append(sentence.strip())
                    current_length = new_length
                else:
                    # Save current tweet and start new one
                    if current_tweet:
                        tweets.append("\n".join(current_tweet) + "\n...")
                    current_tweet = [sentence.strip()]
                    current_length = sentence_length
            
            # Add the last tweet if there's content
            if current_tweet:
                tweets.append(' '.join(current_tweet))
            
            # Verify all tweets are within limit
            for i, tweet in enumerate(tweets):
                if len(tweet) > max_length:
                    print(f"Warning: Tweet {i+1} is {len(tweet)} characters (exceeds {max_length})")
                    # Emergency split if still too long
                    tweets[i] = tweet[:max_length-8] + "\n..."
            
            return tweets

        # Update headers
        self._update_headers_with_csrf()
        csrf_token = self.get_csrf_token()
        
        headers = {
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
            "x-twitter-active-user": "yes",
            "Referer": "https://twitter.com/compose/tweet",
            "Origin": "https://twitter.com",
            "x-csrf-token": csrf_token,
            "Content-Type": "application/json",
        }
        
        self.session.headers.update(headers)

        # Split text into tweets
        tweet_chunks = split_into_tweets(text)
        print(f"\nDebug - Splitting into {len(tweet_chunks)} tweets")
        
        responses = []
        current_reply_to = reply_to_tweet_id

        # Updated feature flags based on error message
        features = {
            # Required features that can't be null (from error message)
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            
            # Other necessary features
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "responsive_web_enhance_cards_enabled": False,
            "vibe_api_enabled": False,
            "responsive_web_text_conversations_enabled": False,
            "interactive_text_enabled": True,
            "responsive_web_media_download_video_enabled": False
        }

        for i, chunk in enumerate(tweet_chunks, 1):
            print(f"\nDebug - Sending tweet {i}/{len(tweet_chunks)}")
            print(f"Length: {len(chunk)} characters")
            
            try:
                variables = {
                    "tweet_text": chunk,
                    "dark_request": False,
                    "media": {
                        "media_entities": [],
                        "possibly_sensitive": False
                    },
                    "semantic_annotation_ids": []
                }

                if current_reply_to:
                    variables["reply"] = {"in_reply_to_tweet_id": current_reply_to}

                payload = {
                    "variables": variables,
                    "features": features,
                    "queryId": "a1p9RWpkYKBjWv_I3WzS-A"
                }

                #print("\nDebug - Request Payload:")
                #print(json.dumps(payload, indent=2))

                response = self.session.post(
                    f"{self.BASE_URL}/i/api/graphql/a1p9RWpkYKBjWv_I3WzS-A/CreateTweet",
                    json=payload
                )
                
                #print(f"\nDebug - Response Status: {response.status_code}")
                
                # Handle response
                if response.status_code != 200:
                    error_text = response.text
                    print(f"\nDebug - Error Response: {error_text}")
                    raise Exception(f"Failed to send tweet {i}: {error_text}")
                
                response_data = response.json()
                
                # Handle API errors in response
                if "errors" in response_data:
                    print(f"\nDebug - API Errors: {json.dumps(response_data['errors'], indent=2)}")
                    raise Exception(f"API errors in tweet {i}: {json.dumps(response_data['errors'], indent=2)}")
                
                # Extract tweet ID for thread
                tweet_result = response_data.get("data", {}).get("create_tweet", {}).get("tweet_results", {}).get("result", {})
                tweet_id = tweet_result.get("rest_id")
                
                if not tweet_id:
                    raise Exception(f"Failed to get tweet ID from response for tweet {i}")
                
                responses.append(response_data)
                current_reply_to = tweet_id
                
                # Delay between tweets
                if i < len(tweet_chunks):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"\nError sending tweet {i}: {str(e)}")
                raise

        return responses
    
    def scrape_tweets(self, query: str, max_tweets: int = 1000, delay_between_requests: int = 2) -> List[Dict]:
        """
        Scrape tweets with pagination handling and rate limit awareness
        
        Args:
            query (str): Search query
            max_tweets (int): Maximum number of tweets to fetch
            delay_between_requests (int): Delay in seconds between pagination requests
        
        Returns:
            List[Dict]: List of tweet objects
        """
        all_tweets = []
        tweets_per_request = 40  # Twitter's typical max per request
        total_requests = (max_tweets + tweets_per_request - 1) // tweets_per_request
        
        try:
            for i in range(total_requests):
                if len(all_tweets) >= max_tweets:
                    break
                    
                current_batch = self.search_tweets(query, tweets_per_request)
                
                # If we got no tweets back, we've hit the end
                if not current_batch:
                    break
                    
                # Filter out duplicates based on tweet ID
                new_tweets = []
                seen_ids = {tweet['id'] for tweet in all_tweets}
                
                for tweet in current_batch:
                    if tweet['id'] not in seen_ids:
                        new_tweets.append(tweet)
                        seen_ids.add(tweet['id'])
                
                all_tweets.extend(new_tweets)
                
                # If we got fewer tweets than requested, we've hit the end
                if len(current_batch) < tweets_per_request:
                    break
                    
                # Sleep between requests to avoid rate limits
                if i < total_requests - 1:
                    time.sleep(delay_between_requests)
                    
            return all_tweets[:max_tweets]  # Trim to max_tweets if we went over
            
        except Exception as e:
            print(f"Error during tweet scraping: {str(e)}")
            return all_tweets  # Return what we got before the error

    def get_tweet_updated(self, tweet_id: str, get_context: bool = True) -> Dict:
        """
        Get a tweet and its previous replies by parsing the conversation up to the target tweet.
        
        Args:
            tweet_id (str): ID of the tweet to fetch
            get_context (bool): Whether to fetch reply/quote context
        
        Returns:
            Dict: Tweet object with context including previous replies in the conversation
        """
        def extract_tweet_data(tweet_result: Dict) -> Dict:
            """Helper function to extract consistent tweet data"""
            if not tweet_result:
                return {}
                
            # Handle visibility results wrapper
            if tweet_result.get('__typename') == 'TweetWithVisibilityResults':
                tweet_result = tweet_result.get('tweet', {})
                
            legacy = tweet_result.get('legacy', {})
            core = tweet_result.get('core', {})
            user_results = core.get('user_results', {}).get('result', {})
            user_legacy = user_results.get('legacy', {})
            
            return {
                'id': legacy.get('id_str'),
                'text': legacy.get('full_text'),
                'username': user_legacy.get('screen_name'),
                'name': user_legacy.get('name'),
                'user_id': user_results.get('rest_id'),
                'created_at': legacy.get('created_at'),
                'conversation_id': legacy.get('conversation_id_str'),
                'in_reply_to_status_id': legacy.get('in_reply_to_status_id_str'),
                'in_reply_to_user_id': legacy.get('in_reply_to_user_id_str'),
                'quoted_status_id': legacy.get('quoted_status_id_str')
            }

        try:
            # Get the tweet data from API
            tweet_data = self.get_tweet(tweet_id)
            
            # Get all entries from the response
            entries = (tweet_data.get('data', {})
                    .get('threaded_conversation_with_injections_v2', {})
                    .get('instructions', [{}])[0]
                    .get('entries', []))

            reply_chain = []
            reached_target = False
            
            # Process all entries to get tweets
            for entry in entries:
                entry_id = entry.get('entryId', '')
                
                # Handle direct tweet entries
                if entry_id.startswith('tweet-'):
                    tweet_result = (entry.get('content', {})
                                .get('itemContent', {})
                                .get('tweet_results', {})
                                .get('result', {}))
                    if tweet_result:
                        tweet = extract_tweet_data(tweet_result)
                        if tweet and tweet.get('id'):
                            if tweet['id'] == tweet_id:
                                reached_target = True
                                reply_chain.append(tweet)
                                break  # Stop processing once we hit our target tweet
                            reply_chain.append(tweet)
                            
                # Handle conversation thread entries
                elif entry_id.startswith('conversationthread-'):
                    items = (entry.get('content', {})
                            .get('items', []))
                    for item in items:
                        if item.get('entryId', '').startswith('conversationthread-'):
                            tweet_result = (item.get('item', {})
                                        .get('itemContent', {})
                                        .get('tweet_results', {})
                                        .get('result', {}))
                            if tweet_result:
                                tweet = extract_tweet_data(tweet_result)
                                if tweet and tweet.get('id'):
                                    if tweet['id'] == tweet_id:
                                        reached_target = True
                                        reply_chain.append(tweet)
                                        break  # Stop processing once we hit our target tweet
                                    reply_chain.append(tweet)
                    if reached_target:
                        break

            # Format the reply chain
            
            formatted_reply_chain = "### The below is additional context on the full conversation prior to the tweet in question. \n\n"
            for tweet in reply_chain[:-1]:
                formatted_reply_chain += f"""
                ###Sender @{tweet['username']}  
                ###Message : 
                {tweet['text']}
                ###End of Tweet
                """


            # Get the main tweet (should be the last one in the chain)
            main_tweet = reply_chain[-1] if reply_chain else None
            
            # Construct response
            response = {
                'tweet': main_tweet,
                'context': {
                    'reply_chain': reply_chain,
                    'n_replies': len(reply_chain),
                    'formatted_reply_chain': formatted_reply_chain
                }
            }
            
            return response
            
        except Exception as e:
            print(f"Error fetching tweet {tweet_id}: {str(e)}")
            raise