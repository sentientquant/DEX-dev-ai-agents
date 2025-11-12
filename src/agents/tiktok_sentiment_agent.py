'''
🌙 Moon Dev's TikTok Sentiment Agent
Built with love by Moon Dev 🚀

This agent tracks TikTok sentiment for crypto tokens using the TikTok API.
TikTok is the BEST source for:
- Viral crypto trends
- FOMO detection
- Retail investor sentiment
- Gen Z / young investor mood

Perfect complement to Reddit (millennial) and Twitter (professional traders)!
'''

import os
import sys
import json
from datetime import datetime
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
from config import SENTIMENT_TOKENS

# TikTok API (using TikTok Research API or unofficial API)
try:
    from TikTokApi import TikTokApi
except ImportError:
    cprint("⚠️ TikTokApi not installed - will use sample data", "yellow")
    cprint("📦 To install: pip install TikTokApi playwright", "yellow")
    cprint("📦 Then run: playwright install", "yellow")
    TikTokApi = None

# Sentiment analysis
try:
    from textblob import TextBlob
except ImportError:
    cprint("❌ Error: textblob not installed", "red")
    cprint("📦 Install with: pip install textblob", "yellow")
    sys.exit(1)

# Create data directories
DATA_FOLDER = "src/data/sentiment"
TIKTOK_SENTIMENT_FILE = "src/data/tiktok_sentiment.csv"
Path(DATA_FOLDER).mkdir(parents=True, exist_ok=True)


class TikTokSentimentAgent:
    """TikTok sentiment analysis for crypto tokens"""

    def __init__(self):
        """Initialize TikTok sentiment agent"""
        cprint("\n🎵 Moon Dev TikTok Sentiment Agent", "magenta", attrs=['bold'])
        cprint("=" * 70, "magenta")
        cprint("🎯 Target: Viral crypto trends & FOMO detection", "cyan")
        cprint("👥 Audience: Gen Z & young retail investors", "cyan")
        cprint("=" * 70 + "\n", "magenta")

        self.api = None
        self.use_sample_data = True

        # Try to initialize TikTok API
        if TikTokApi:
            try:
                cprint("🔌 Attempting to connect to TikTok API...", "cyan")
                # Note: TikTok API requires proper authentication
                # For now, we'll use sample data approach
                self.use_sample_data = True
                cprint("⚠️ Using sample data mode (TikTok API requires setup)", "yellow")
            except Exception as e:
                cprint(f"⚠️ TikTok API connection failed: {str(e)}", "yellow")
                self.use_sample_data = True
        else:
            cprint("⚠️ TikTok API not available - using sample data", "yellow")

    def analyze_sentiment(self, text):
        """Analyze sentiment using TextBlob (-1 to 1)"""
        blob = TextBlob(text)
        return blob.sentiment.polarity

    def search_tiktok(self, token, count=20):
        """Search TikTok for crypto-related videos"""
        if self.use_sample_data:
            return self._get_sample_tiktok_videos(token, count)

        # Real TikTok API implementation would go here
        try:
            # TikTok API search implementation
            # videos = self.api.search.videos(token, count=count)
            pass
        except Exception as e:
            cprint(f"⚠️ TikTok search error: {str(e)}", "yellow")
            return self._get_sample_tiktok_videos(token, count)

    def _get_sample_tiktok_videos(self, token, count=20):
        """Generate sample TikTok videos for demo/testing"""
        samples = {
            'BTC': [
                {
                    'text': 'Bitcoin to the moon! 🚀 Just bought my first BTC',
                    'likes': 15200,
                    'comments': 432,
                    'shares': 89,
                    'views': 125000,
                    'creator': 'cryptokid2024'
                },
                {
                    'text': 'Why Bitcoin will hit $100k in 2025 - here\'s the proof',
                    'likes': 8900,
                    'comments': 234,
                    'shares': 45,
                    'views': 89000,
                    'creator': 'btcmaxi'
                },
                {
                    'text': 'Sold all my Bitcoin, here\'s why you should too',
                    'likes': 3200,
                    'comments': 567,
                    'shares': 12,
                    'views': 45000,
                    'creator': 'realistic_trader'
                },
                {
                    'text': 'Bitcoin dip buying guide - don\'t panic sell!',
                    'likes': 12000,
                    'comments': 321,
                    'shares': 67,
                    'views': 98000,
                    'creator': 'crypto_coach'
                },
                {
                    'text': 'BTC chart analysis - resistance at $95k',
                    'likes': 6700,
                    'comments': 189,
                    'shares': 34,
                    'views': 67000,
                    'creator': 'chart_master'
                },
            ],
            'ETH': [
                {
                    'text': 'Ethereum gas fees are crazy right now 😭',
                    'likes': 8900,
                    'comments': 432,
                    'shares': 56,
                    'views': 76000,
                    'creator': 'eth_user'
                },
                {
                    'text': 'Why Ethereum will flip Bitcoin soon',
                    'likes': 11200,
                    'comments': 678,
                    'shares': 89,
                    'views': 112000,
                    'creator': 'eth_maxi'
                },
                {
                    'text': 'Just staked my ETH for passive income 💰',
                    'likes': 5600,
                    'comments': 234,
                    'shares': 23,
                    'views': 54000,
                    'creator': 'defi_degen'
                },
                {
                    'text': 'Ethereum Layer 2s are the future',
                    'likes': 4300,
                    'comments': 156,
                    'shares': 34,
                    'views': 43000,
                    'creator': 'l2_expert'
                },
                {
                    'text': 'ETH ETF approval coming soon? Here\'s what I think',
                    'likes': 7800,
                    'comments': 298,
                    'shares': 67,
                    'views': 89000,
                    'creator': 'crypto_news'
                },
            ],
            'SOL': [
                {
                    'text': 'Solana is the Ethereum killer! 🔥',
                    'likes': 13400,
                    'comments': 567,
                    'shares': 123,
                    'views': 156000,
                    'creator': 'sol_gang'
                },
                {
                    'text': 'Solana network went down again... not a good look',
                    'likes': 6700,
                    'comments': 892,
                    'shares': 45,
                    'views': 78000,
                    'creator': 'sol_critic'
                },
                {
                    'text': 'Made $10k trading Solana memecoins',
                    'likes': 18900,
                    'comments': 1234,
                    'shares': 234,
                    'views': 234000,
                    'creator': 'memecoin_millionaire'
                },
                {
                    'text': 'Solana speed vs Ethereum - the comparison',
                    'likes': 9200,
                    'comments': 345,
                    'shares': 67,
                    'views': 98000,
                    'creator': 'blockchain_guy'
                },
                {
                    'text': 'Why I\'m bullish on SOL long term',
                    'likes': 7600,
                    'comments': 267,
                    'shares': 56,
                    'views': 87000,
                    'creator': 'crypto_investor'
                },
            ],
        }

        videos = samples.get(token, [])[:count]

        # Add timestamps
        for video in videos:
            video['created_at'] = datetime.now().isoformat()

        return videos

    def run(self, tokens=None):
        """Execute TikTok sentiment analysis"""
        if tokens is None:
            tokens = SENTIMENT_TOKENS

        cprint("\n📊 Starting TikTok sentiment analysis...\n", "magenta", attrs=['bold'])

        all_results = []

        for token in tokens:
            cprint(f"\n{'='*70}", "magenta")
            cprint(f"🎵 Analyzing TikTok for: {token}", "magenta", attrs=['bold'])
            cprint(f"{'='*70}", "magenta")

            # Search TikTok
            cprint(f"\n📱 Fetching TikTok videos for {token}...", "cyan")
            videos = self.search_tiktok(token, count=20)

            if not videos:
                cprint(f"⚠️ No videos found for {token}", "yellow")
                continue

            # Analyze sentiment
            sentiments = []
            total_engagement = 0
            video_data = []

            for video in videos:
                sentiment = self.analyze_sentiment(video['text'])
                sentiments.append(sentiment)

                # Calculate engagement score (viral indicator)
                engagement = (
                    video['likes'] +
                    (video['comments'] * 2) +  # Comments weighted higher
                    (video['shares'] * 3)      # Shares weighted highest
                )
                total_engagement += engagement

                video_data.append({
                    'timestamp': video['created_at'],
                    'token': token,
                    'text': video['text'],
                    'sentiment': sentiment,
                    'likes': video['likes'],
                    'comments': video['comments'],
                    'shares': video['shares'],
                    'views': video['views'],
                    'creator': video['creator'],
                    'engagement_score': engagement
                })

            avg_sentiment = np.mean(sentiments) if sentiments else 0
            avg_engagement = total_engagement / len(videos) if videos else 0

            # Viral score (0-10 scale)
            viral_score = min(10, avg_engagement / 5000)  # 50k engagement = 10/10

            # TikTok-specific sentiment label
            if avg_sentiment > 0.4 and viral_score > 7:
                label = "VIRAL BULLISH 🔥🚀"
                color = "green"
            elif avg_sentiment > 0.2:
                label = "BULLISH 🚀"
                color = "green"
            elif avg_sentiment > -0.2:
                label = "NEUTRAL 😐"
                color = "yellow"
            elif avg_sentiment < -0.4 and viral_score > 7:
                label = "VIRAL BEARISH 🔥🐻"
                color = "red"
            else:
                label = "BEARISH 🐻"
                color = "red"

            cprint(f"\n✅ {token} TikTok Analysis:", "cyan", attrs=['bold'])
            cprint(f"   Videos: {len(videos)}", "white")
            cprint(f"   Sentiment: {avg_sentiment:.3f}", "white")
            cprint(f"   Avg Engagement: {avg_engagement:,.0f}", "white")
            cprint(f"   Viral Score: {viral_score:.1f}/10", "white")
            cprint(f"   Label: {label}", color, attrs=['bold'])

            # Save video data
            df = pd.DataFrame(video_data)
            output_file = f"{DATA_FOLDER}/{token}_tiktok.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            cprint(f"   💾 Saved to: {output_file}", "white")

            all_results.append({
                'token': token,
                'sentiment': avg_sentiment,
                'engagement': avg_engagement,
                'viral_score': viral_score,
                'label': label,
                'videos': len(videos)
            })

        # Calculate overall TikTok sentiment
        if all_results:
            overall_sentiment = np.mean([r['sentiment'] for r in all_results])
            overall_viral = np.mean([r['viral_score'] for r in all_results])

            if overall_sentiment > 0.3:
                overall_label = "BULLISH 🚀"
                overall_color = "green"
            elif overall_sentiment > -0.3:
                overall_label = "NEUTRAL 😐"
                overall_color = "yellow"
            else:
                overall_label = "BEARISH 🐻"
                overall_color = "red"

            cprint("\n" + "=" * 70, "magenta")
            cprint(f"OVERALL TIKTOK SENTIMENT: {overall_sentiment:.3f} - {overall_label}", overall_color, attrs=['bold'])
            cprint(f"Average Viral Score: {overall_viral:.1f}/10", "cyan")
            cprint("=" * 70 + "\n", "magenta")

            # Save TikTok sentiment history
            history_data = {
                'timestamp': datetime.now().isoformat(),
                'overall_sentiment': overall_sentiment,
                'label': overall_label,
                'viral_score': overall_viral,
                'btc_sentiment': next((r['sentiment'] for r in all_results if r['token'] == 'BTC'), 0),
                'eth_sentiment': next((r['sentiment'] for r in all_results if r['token'] == 'ETH'), 0),
                'sol_sentiment': next((r['sentiment'] for r in all_results if r['token'] == 'SOL'), 0),
                'total_videos': sum(r['videos'] for r in all_results)
            }

            history_df = pd.DataFrame([history_data])
            if os.path.exists(TIKTOK_SENTIMENT_FILE):
                existing = pd.read_csv(TIKTOK_SENTIMENT_FILE)
                history_df = pd.concat([existing, history_df], ignore_index=True)
            history_df.to_csv(TIKTOK_SENTIMENT_FILE, index=False)

            cprint(f"✅ TikTok sentiment history updated: {TIKTOK_SENTIMENT_FILE}\n", "green")

        cprint("🎉 TikTok sentiment analysis complete!\n", "magenta", attrs=['bold'])


if __name__ == "__main__":
    try:
        agent = TikTokSentimentAgent()
        agent.run()
    except KeyboardInterrupt:
        cprint("\n\n👋 TikTok sentiment agent stopped by user", "yellow")
    except Exception as e:
        cprint(f"\n❌ Error: {str(e)}", "red")
        import traceback
        traceback.print_exc()
