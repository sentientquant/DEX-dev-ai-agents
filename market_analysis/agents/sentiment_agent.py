'''
🌙 Moon Dev's HYBRID Sentiment Agent
Built with love by Moon Dev 🚀

REAL MARKET DATA using:
- Twitter API (3 accounts rotation = 300 tweets/month)
- Reddit API (unlimited, free forever)
- TextBlob sentiment analysis (fast!)

Trading pairs: BTCUSDT, ETHUSDT, SOLUSDT
'''

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

# Fix Windows encoding
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, codecs.StreamWriter):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from termcolor import cprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config import (
    SENTIMENT_TOKENS,
    SENTIMENT_TWEETS_PER_TOKEN,
    SENTIMENT_REDDIT_POSTS_PER_TOKEN,
    SENTIMENT_TWITTER_ROTATION_DAYS,
    SENTIMENT_TWITTER_BUDGET_PER_ACCOUNT,
    SENTIMENT_SUBREDDITS,
    SENTIMENT_CHECK_INTERVAL_MINUTES
)

# Twitter API (tweepy for official API)
try:
    import tweepy
except ImportError:
    cprint("❌ Error: tweepy not installed", "red")
    cprint("📦 Install with: pip install tweepy", "yellow")
    sys.exit(1)

# Reddit API (praw)
try:
    import praw
except ImportError:
    cprint("❌ Error: praw not installed", "red")
    cprint("📦 Install with: pip install praw", "yellow")
    sys.exit(1)

# Sentiment analysis
try:
    from textblob import TextBlob
except ImportError:
    cprint("❌ Error: textblob not installed", "red")
    cprint("📦 Install with: pip install textblob", "yellow")
    sys.exit(1)

# Create data directories
DATA_FOLDER = "src/data/sentiment"
SENTIMENT_HISTORY_FILE = "src/data/sentiment_history.csv"
TWITTER_USAGE_FILE = "src/data/twitter_usage.json"
Path(DATA_FOLDER).mkdir(parents=True, exist_ok=True)


class TwitterAccountRotator:
    """Manages 3 Twitter API accounts with automatic rotation"""

    def __init__(self):
        """Initialize with 3 bearer tokens from .env"""
        self.accounts = [
            {
                'name': 'Account 1',
                'bearer': os.getenv('TWITTER_BEARER_TOKEN_1'),
                'budget': SENTIMENT_TWITTER_BUDGET_PER_ACCOUNT,
                'used': 0
            },
            {
                'name': 'Account 2',
                'bearer': os.getenv('TWITTER_BEARER_TOKEN_2'),
                'budget': SENTIMENT_TWITTER_BUDGET_PER_ACCOUNT,
                'used': 0
            },
            {
                'name': 'Account 3',
                'bearer': os.getenv('TWITTER_BEARER_TOKEN_3'),
                'budget': SENTIMENT_TWITTER_BUDGET_PER_ACCOUNT,
                'used': 0
            }
        ]

        # Load usage from file
        self._load_usage()

    def _load_usage(self):
        """Load Twitter usage from JSON file"""
        if os.path.exists(TWITTER_USAGE_FILE):
            try:
                with open(TWITTER_USAGE_FILE, 'r') as f:
                    data = json.load(f)
                    for i, account in enumerate(self.accounts):
                        if i < len(data.get('accounts', [])):
                            account['used'] = data['accounts'][i].get('used', 0)
            except:
                pass

    def _save_usage(self):
        """Save Twitter usage to JSON file"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'accounts': [
                {'name': acc['name'], 'used': acc['used'], 'budget': acc['budget']}
                for acc in self.accounts
            ]
        }
        with open(TWITTER_USAGE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def get_active_account(self):
        """Get currently active account based on day of month"""
        day = datetime.now().day

        if day <= SENTIMENT_TWITTER_ROTATION_DAYS:
            account_idx = 0
        elif day <= (SENTIMENT_TWITTER_ROTATION_DAYS * 2):
            account_idx = 1
        else:
            account_idx = 2

        account = self.accounts[account_idx]

        # Check if account has budget
        if account['used'] >= account['budget']:
            cprint(f"⚠️ {account['name']} budget exhausted ({account['used']}/{account['budget']})", "yellow")
            # Try next account
            for i in range(3):
                alt_idx = (account_idx + i + 1) % 3
                alt_account = self.accounts[alt_idx]
                if alt_account['used'] < alt_account['budget']:
                    cprint(f"🔄 Switching to {alt_account['name']}", "cyan")
                    return alt_account
            # All accounts exhausted
            return None

        return account

    def record_usage(self, account, count):
        """Record Twitter API usage"""
        account['used'] += count
        self._save_usage()
        cprint(f"📊 {account['name']}: {account['used']}/{account['budget']} tweets used", "cyan")


class RedditSentiment:
    """Unlimited Reddit sentiment analysis"""

    def __init__(self):
        """Initialize Reddit API"""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD')
        )
        cprint("✅ Reddit API connected (unlimited!)", "green")

    def get_sentiment(self, token, count=20):
        """Get Reddit posts and analyze sentiment"""
        subreddits = SENTIMENT_SUBREDDITS.get(token, ['CryptoCurrency'])
        posts = []

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                search_query = token if token != 'BTC' else 'bitcoin'

                for post in subreddit.search(search_query, time_filter='day', limit=count//len(subreddits)):
                    # Combine title + selftext
                    text = f"{post.title} {post.selftext}"
                    if len(text) > 20:  # Filter out short posts
                        posts.append({
                            'text': text,
                            'score': post.score,
                            'created_at': datetime.fromtimestamp(post.created_utc).isoformat(),
                            'url': f"https://reddit.com{post.permalink}",
                            'subreddit': subreddit_name
                        })
            except Exception as e:
                cprint(f"⚠️ Error fetching from r/{subreddit_name}: {str(e)}", "yellow")

        return posts[:count]


class TwitterSentiment:
    """Twitter API with account rotation"""

    def __init__(self, rotator):
        """Initialize with account rotator"""
        self.rotator = rotator
        self.client = None
        self.current_account = None

    def _get_client(self):
        """Get Twitter client with active account"""
        account = self.rotator.get_active_account()
        if not account:
            cprint("❌ All Twitter accounts exhausted for this month!", "red")
            return None

        if self.current_account != account:
            self.current_account = account
            self.client = tweepy.Client(bearer_token=account['bearer'])
            cprint(f"✅ Using {account['name']} ({account['budget'] - account['used']} tweets left)", "green")

        return self.client

    def get_sentiment(self, token, count=20):
        """Get tweets and analyze sentiment"""
        client = self._get_client()
        if not client:
            return []  # No Twitter budget available

        try:
            # Free tier doesn't support $ cashtags, use text search instead
            search_terms = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'SOL': 'solana'
            }
            search_term = search_terms.get(token, token.lower())

            # Search for recent tweets (no cashtags for free tier)
            query = f"{search_term} -is:retweet lang:en"
            response = client.search_recent_tweets(
                query=query,
                max_results=min(count, 100),  # Twitter API limit
                tweet_fields=['created_at', 'public_metrics']
            )

            if not response.data:
                cprint(f"⚠️ No tweets found for {token}", "yellow")
                return []

            tweets = []
            for tweet in response.data:
                tweets.append({
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count']
                })

            # Record usage
            self.rotator.record_usage(self.current_account, len(tweets))

            return tweets

        except Exception as e:
            cprint(f"❌ Twitter API error: {str(e)}", "red")
            return []


class HybridSentimentAgent:
    """Combines Reddit + Twitter for production-grade sentiment analysis"""

    def __init__(self):
        """Initialize hybrid agent"""
        cprint("\n🌙 Moon Dev Hybrid Sentiment Agent (Production Edition)", "cyan", attrs=['bold'])
        cprint("=" * 70, "cyan")

        # Initialize components
        self.twitter_rotator = TwitterAccountRotator()
        self.reddit = RedditSentiment()
        self.twitter = TwitterSentiment(self.twitter_rotator)

        cprint(f"✅ Tracking: {', '.join(SENTIMENT_TOKENS)}", "green")
        cprint(f"✅ Reddit: Unlimited | Twitter: 300 tweets/month (3 accounts)", "green")
        cprint("=" * 70 + "\n", "cyan")

    def analyze_sentiment(self, text):
        """Analyze sentiment using TextBlob (-1 to 1)"""
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def run(self):
        """Execute hybrid sentiment analysis"""
        cprint("\n📊 Starting hybrid sentiment analysis...\n", "yellow", attrs=['bold'])

        all_results = []

        for token in SENTIMENT_TOKENS:
            cprint(f"\n{'='*70}", "cyan")
            cprint(f"🔍 Analyzing: {token}", "cyan", attrs=['bold'])
            cprint(f"{'='*70}", "cyan")

            # REDDIT SENTIMENT (Primary - Unlimited)
            cprint(f"\n📱 Fetching Reddit posts for {token}...", "yellow")
            reddit_posts = self.reddit.get_sentiment(token, SENTIMENT_REDDIT_POSTS_PER_TOKEN)

            reddit_sentiments = []
            for post in reddit_posts:
                sentiment = self.analyze_sentiment(post['text'])
                reddit_sentiments.append(sentiment)

            reddit_avg = np.mean(reddit_sentiments) if reddit_sentiments else 0
            cprint(f"✅ Reddit: {len(reddit_posts)} posts, sentiment: {reddit_avg:.3f}", "green")

            # TWITTER SENTIMENT (Confirmation - 300/month)
            cprint(f"\n🐦 Fetching Twitter posts for {token}...", "yellow")
            tweets = self.twitter.get_sentiment(token, SENTIMENT_TWEETS_PER_TOKEN)

            twitter_sentiments = []
            for tweet in tweets:
                sentiment = self.analyze_sentiment(tweet['text'])
                twitter_sentiments.append(sentiment)

            twitter_avg = np.mean(twitter_sentiments) if twitter_sentiments else None
            if twitter_avg is not None:
                cprint(f"✅ Twitter: {len(tweets)} tweets, sentiment: {twitter_avg:.3f}", "green")
            else:
                cprint(f"⚠️ Twitter: No data (budget exhausted or API issue)", "yellow")

            # COMBINED SENTIMENT (Weighted average)
            if twitter_avg is not None:
                # 60% Reddit, 40% Twitter (Reddit more reliable for volume)
                combined = (reddit_avg * 0.6) + (twitter_avg * 0.4)
            else:
                # Reddit only if Twitter unavailable
                combined = reddit_avg

            # Sentiment label
            if combined > 0.3:
                label = "VERY BULLISH 🚀🚀🚀"
                color = "green"
            elif combined > 0.1:
                label = "BULLISH 🚀"
                color = "green"
            elif combined > -0.1:
                label = "NEUTRAL 😐"
                color = "yellow"
            elif combined > -0.3:
                label = "BEARISH 🐻"
                color = "red"
            else:
                label = "VERY BEARISH 🐻🐻🐻"
                color = "red"

            cprint(f"\n📊 {token} COMBINED SENTIMENT: {combined:.3f} - {label}", color, attrs=['bold'])

            # Save individual token data
            all_data = []

            # Add Reddit posts
            for post in reddit_posts:
                all_data.append({
                    'timestamp': post['created_at'],
                    'token': token,
                    'source': 'reddit',
                    'text': post['text'][:200],  # Limit text length
                    'sentiment': self.analyze_sentiment(post['text']),
                    'subreddit': post.get('subreddit', ''),
                    'score': post.get('score', 0)
                })

            # Add tweets
            for tweet in tweets:
                all_data.append({
                    'timestamp': tweet['created_at'],
                    'token': token,
                    'source': 'twitter',
                    'text': tweet['text'][:200],
                    'sentiment': self.analyze_sentiment(tweet['text']),
                    'likes': tweet.get('likes', 0),
                    'retweets': tweet.get('retweets', 0)
                })

            # Save to CSV
            if all_data:
                df = pd.DataFrame(all_data)
                output_file = f"{DATA_FOLDER}/{token}_hybrid.csv"
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                cprint(f"💾 Saved {len(all_data)} items to: {output_file}", "white")

            # Store for overall sentiment
            all_results.append({
                'token': token,
                'reddit_sentiment': reddit_avg,
                'twitter_sentiment': twitter_avg,
                'combined_sentiment': combined,
                'label': label,
                'data_points': len(all_data)
            })

        # Calculate overall market sentiment
        overall = np.mean([r['combined_sentiment'] for r in all_results])

        if overall > 0.3:
            overall_label = "VERY BULLISH 🚀🚀🚀"
            overall_color = "green"
        elif overall > 0.1:
            overall_label = "BULLISH 🚀"
            overall_color = "green"
        elif overall > -0.1:
            overall_label = "NEUTRAL 😐"
            overall_color = "yellow"
        elif overall > -0.3:
            overall_label = "BEARISH 🐻"
            overall_color = "red"
        else:
            overall_label = "VERY BEARISH 🐻🐻🐻"
            overall_color = "red"

        cprint("\n" + "=" * 70, "cyan")
        cprint(f"OVERALL MARKET SENTIMENT: {overall:.3f} - {overall_label}", overall_color, attrs=['bold'])
        cprint("=" * 70 + "\n", "cyan")

        # Save sentiment history
        history_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_sentiment': overall,
            'label': overall_label,
            'btc_sentiment': next((r['combined_sentiment'] for r in all_results if r['token'] == 'BTC'), 0),
            'eth_sentiment': next((r['combined_sentiment'] for r in all_results if r['token'] == 'ETH'), 0),
            'sol_sentiment': next((r['combined_sentiment'] for r in all_results if r['token'] == 'SOL'), 0),
            'total_data_points': sum(r['data_points'] for r in all_results)
        }

        history_df = pd.DataFrame([history_data])
        if os.path.exists(SENTIMENT_HISTORY_FILE):
            existing = pd.read_csv(SENTIMENT_HISTORY_FILE)
            history_df = pd.concat([existing, history_df], ignore_index=True)
        history_df.to_csv(SENTIMENT_HISTORY_FILE, index=False)

        cprint(f"✅ Sentiment history updated: {SENTIMENT_HISTORY_FILE}\n", "green")
        cprint("🎉 Hybrid sentiment analysis complete!\n", "green", attrs=['bold'])


if __name__ == "__main__":
    try:
        agent = HybridSentimentAgent()
        agent.run()
    except KeyboardInterrupt:
        cprint("\n\n👋 Sentiment agent stopped by user", "yellow")
    except Exception as e:
        cprint(f"\n❌ Error: {str(e)}", "red")
        import traceback
        traceback.print_exc()
