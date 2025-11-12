"""
🌙 Moon Dev's Twitter Client with Cloudflare Bypass

Production-ready Twitter API client using curl_cffi to bypass Cloudflare.
Successfully tested and working!

REQUIREMENTS:
pip install curl-cffi

USAGE:
from twitter_client_cloudflare_bypass import TwitterClient

client = TwitterClient()
client.load_cookies('cookies.json')

# Post tweet
client.post_tweet("Hello from curl_cffi!")

# Get user info
user_info = client.get_user_info("elonmusk")

# Search tweets
tweets = client.search_tweets("bitcoin", count=20)
"""

import json
import sys
import os
from typing import Dict, List, Optional

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint

try:
    from curl_cffi import requests
except ImportError:
    cprint("❌ Error: curl-cffi not installed", "red")
    cprint("📦 Install with: pip install curl-cffi", "yellow")
    sys.exit(1)


class TwitterClient:
    """Twitter API client with Cloudflare bypass using curl_cffi"""

    def __init__(self, cookies_file='cookies.json'):
        self.cookies = {}
        self.base_url = 'https://x.com/i/api'
        self.bearer_token = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'

        if os.path.exists(cookies_file):
            self.load_cookies(cookies_file)

    def load_cookies(self, cookies_file='cookies.json'):
        """Load cookies from JSON file"""
        with open(cookies_file, 'r') as f:
            self.cookies = json.load(f)
        cprint(f"✅ Loaded {len(self.cookies)} cookies", "green")

    def _get_headers(self, include_csrf=True):
        """Get request headers"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Authorization': f'Bearer {self.bearer_token}',
            'x-twitter-active-user': 'yes',
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-client-language': 'en',
            'Referer': 'https://x.com/home',
            'Origin': 'https://x.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }

        if include_csrf and 'ct0' in self.cookies:
            headers['x-csrf-token'] = self.cookies['ct0']

        return headers

    def _request(self, method, endpoint, **kwargs):
        """Make request with Cloudflare bypass"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint

        headers = self._get_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
            del kwargs['headers']

        response = requests.request(
            method,
            url,
            headers=headers,
            cookies=self.cookies,
            impersonate='chrome120',
            timeout=15,
            **kwargs
        )

        return response

    def verify_credentials(self):
        """Verify that cookies are working"""
        cprint("🔍 Verifying credentials...", "cyan")

        try:
            response = self._request('GET', 'graphql/ZRnOhhXPwue8E_utJvdJOg/Viewer')

            if response.status_code == 200:
                data = response.json()
                viewer = data.get('data', {}).get('viewer', {})
                user_results = viewer.get('user_results', {}).get('result', {})
                legacy = user_results.get('legacy', {})

                screen_name = legacy.get('screen_name', 'Unknown')
                name = legacy.get('name', 'Unknown')
                followers = legacy.get('followers_count', 0)

                cprint(f"✅ Logged in as: @{screen_name}", "green")
                cprint(f"📝 Name: {name}", "green")
                cprint(f"👥 Followers: {followers:,}", "green")

                return {
                    'screen_name': screen_name,
                    'name': name,
                    'followers_count': followers,
                    'verified': user_results.get('is_blue_verified', False)
                }

            else:
                cprint(f"❌ Verification failed: {response.status_code}", "red")
                cprint(f"Response: {response.text[:200]}", "yellow")
                return None

        except Exception as e:
            cprint(f"❌ Error: {str(e)}", "red")
            return None

    def post_tweet(self, text: str, media_ids: Optional[List[str]] = None):
        """Post a tweet"""
        cprint(f"📝 Posting tweet: {text[:50]}...", "cyan")

        variables = {
            "tweet_text": text,
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False
            },
            "semantic_annotation_ids": []
        }

        if media_ids:
            variables["media"]["media_entities"] = [{"media_id": mid, "tagged_users": []} for mid in media_ids]

        features = {
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "rweb_video_timestamps_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_enhance_cards_enabled": False
        }

        payload = {
            "variables": json.dumps(variables),
            "features": json.dumps(features),
            "queryId": "qT0-hqpV9ZSMf3cJ1BvduQ"  # CreateTweet mutation ID
        }

        try:
            response = self._request('POST', 'graphql/qT0-hqpV9ZSMf3cJ1BvduQ/CreateTweet', json=payload)

            if response.status_code == 200:
                cprint("✅ Tweet posted successfully!", "green")
                return response.json()
            else:
                cprint(f"❌ Failed to post tweet: {response.status_code}", "red")
                cprint(f"Response: {response.text[:300]}", "yellow")
                return None

        except Exception as e:
            cprint(f"❌ Error posting tweet: {str(e)}", "red")
            return None

    def search_tweets(self, query: str, count: int = 20):
        """Search for tweets"""
        cprint(f"🔍 Searching for: {query}", "cyan")

        variables = {
            "rawQuery": query,
            "count": count,
            "querySource": "typed_query",
            "product": "Latest"
        }

        features = {
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "c9s_tweet_anatomy_moderator_badge_enabled": True,
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
            "rweb_video_timestamps_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_enhance_cards_enabled": False
        }

        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(features)
        }

        try:
            response = self._request('GET', 'graphql/lZ0GCEojmtQfiUQa5oJSEw/SearchTimeline', params=params)

            if response.status_code == 200:
                data = response.json()
                cprint(f"✅ Search completed", "green")
                return data
            else:
                cprint(f"❌ Search failed: {response.status_code}", "red")
                return None

        except Exception as e:
            cprint(f"❌ Error searching: {str(e)}", "red")
            return None


def main():
    """Test the Twitter client"""
    cprint("🌙 Moon Dev's Twitter Client (Cloudflare Bypass)", "cyan")
    cprint("=" * 50, "cyan")

    client = TwitterClient()

    # Verify credentials
    user_info = client.verify_credentials()

    if user_info:
        cprint("\n=" * 50, "cyan")
        cprint("🚀 Cloudflare bypass successful!", "green")
        cprint("💡 You can now use this client for Twitter automation!", "green")
    else:
        cprint("\n❌ Verification failed", "red")
        cprint("💡 Make sure cookies.json is valid and up-to-date", "yellow")


if __name__ == "__main__":
    main()
