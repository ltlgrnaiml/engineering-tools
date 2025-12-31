# Source: https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x

---

Omar Diab

Added 9 months ago

# [Real Time Sentiment Analysis with Grok & 𝕏](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#real-time-sentiment-analysis-with-grok--𝕏)

In this guide we'll take a look at the results you can achieve when you combine X's real time data with Grok's natural language understanding, reasoning and intelligence. We'll build a tool that let's us ingest X posts about bitcoin in real time and calculate a score for the market sentiment based on the content of the posts. To do this we'll employ a multi-stage approach that leverages `grok-3`'s speed for filtering/classification and `grok-3-mini`'s reasoning for computing the sentiment for the filtered posts. Whilst this guide focus on bitcoin, the approaches showcased here can easily be adapted for other topics beyond crypto entirely.

## [Table of Contents](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#table-of-contents)

- [Setup and Prerequisites](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#setup-and-prerequisites)
- [High-Level Overview](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#high-level-overview)
- [Working with the Filtered Stream API](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#working-with-the-filtered-stream-api) 
Rules in the Filtered Stream
- [Processing the Stream Data](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#processing-the-stream-data)
- [Brining Grok into the Equation](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#bringing-grok-into-the-equation) 
Filtering Noisy Posts
Computing the Sentiment
- [Piecing it all Together](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#piecing-it-all-together)
- [Conclusion](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#conclusion)
- [Rules in the Filtered Stream](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#rules-in-the-filtered-stream)
- [Filtering Noisy Posts](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#filtering-noisy-posts)
- [Computing the Sentiment](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#computing-the-sentiment)

## [Setup and Prerequisites](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#setup-and-prerequisites)

You’ll need an X Developer account with access to the [Filtered Stream API](https://docs.x.com/x-api/posts/filtered-stream/introduction), an X API key and API secret. You'll also need an xAI API key which you can grab over at the xAI [console](https://console.x.ai)

Python (OpenAI)

```
%pip install -q openai tweepy python-dotenv aiohttp async_lru oauthlib
```

Text

```
Note: you may need to restart the kernel to use updated packages.
```

## [High-Level Overview](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#high-level-overview)

Our tool starts by pulling real-time Bitcoin posts from X using the [Filtered Stream API](https://docs.x.com/x-api/posts/filtered-stream/introduction) according to a filter rule we define upfront.

Every 5 posts that match our rule (arbitrary, but adjustable) we batch them and send them to `grok-3`. It can quickly classify which posts carry signal and are worth scoring—saving those and discarding the rest. Once we hit 5 high-signal posts (again, adjustable), we pass that batch to `grok-3-mini` to leverage it's reasoning capability to compute the sentiment score. After that, for each new high-signal post that joins the batch, we recalculate the score with the full set. It’s a rolling update, simple but effective.

This modular design pays off in a few ways. It gives us fine-grained control over each step, since filtering and scoring get their own prompts, they can be tuned independently. If we want to tweak the filtering criteria or swap in a new xAI model later, it’s a simple change, isolated from the sentiment process and vice-versa. Compare that to a single “super-prompt” approach: one tweak there could ripple across everything, muddying the results.

Another perk is how it plays to model strengths. That’s where `grok-3-mini`'s reasoning shines - as a [reasoning model](https://docs.x.ai/docs/guides/reasoning), it "thinks" before responding allowing for more analytical answers. By splitting the workload this way, we get efficiency and precision, tailored to each task.

More broadly, LLMs like Grok are a natural fit for this. Posts roll in from X in all sorts of languages—not just English—and Grok handles them effortlessly, no extra training needed. Plus, we can tweak classification or sentiment criteria on the fly by just updating the respective prompts, say, to catch different signals or refine scoring. Unlike traditional ML, where you’d retrain a model from scratch, this lets us experiment fast and iterate based on what we see.

The approach outlined above is just one way to do it; you could adjust the batch sizes or only recalculate sentiment with a bigger pile of new posts, depending on your needs.

## [Working with the Filtered Stream API](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#working-with-the-filtered-stream-api)

The Filtered Stream API is an X endpoint that delivers real-time posts based on rules you define. It’s our pipeline for capturing Bitcoin chatter as it happens. You set up stream rules, apply them, and then listen, any post matching a rule comes through with a tag showing which rule it hit. If you want the full breakdown, check [X’s API docs](https://docs.x.com/x-api/posts/filtered-stream/introduction). For this guide, it’s simply our live data source.

### [Rules in the Filtered Stream](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#rules-in-the-filtered-stream)

Rules drive the stream, telling it what posts to grab. You create them with specific keywords, operators, or user filters, then send them to the API to activate. Once live, the stream returns X post data for every match, including a `matching_rules` field to track which rule triggered it. We’ll use a single, broad rule here to catch a wide range of Bitcoin-related posts.

This keeps things simple, but the setup’s flexible. You could add multiple rules to widen the net—say, one for posts from high-profile investors , another for crypto organizations, and another for wallet trackers. Each rule could target a different angle on sentiment, tagged separately for analysis downstream.

Here's the rule we'll roll with:

Python (OpenAI)

```
GENERAL_BTC_RULE = {
    "value": '(BTC OR Bitcoin OR #BTC OR #Bitcoin OR "bit coin") followers_count:1000 -is:retweet -is:reply',
    "tag": "generic_btc",
}
```

This rule grabs posts mentioning `BTC`, `Bitcoin`, `#BTC`, `#Bitcoin` or `bit coin` but only from accounts with at least 1,000 followers, excluding retweets and replies. Even with `grok-3` filtering low-signal posts later, this follower threshold helps cut down noise upfront.

## [Processing the Stream Data](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#processing-the-stream-data)

Once the Filtered Stream API is humming, we need to shape the raw JSON responses into something usable. We’re using [Tweepy](https://docs.tweepy.org/en/stable/), a Python library that simplifies X API interactions, to handle the streaming and parsing. The code below defines `Post` and `Author` classes to store key data (text, author, timestamp) and an XStream class to process incoming posts, stashing them in a dictionary for later steps.

Python (OpenAI)

```
from dataclasses import dataclass
from datetime import datetime

from tweepy import StreamRule

@dataclass
class Author:
    id: int
    name: str
    username: str
    followers_count: int
    following_count: int
    post_count: int
    listed_count: int
    like_count: int
    media_count: int
    verified: bool

@dataclass
class Post:
    id: int
    text: str
    author_id: str
    created_at: datetime
    author: Author
    matching_rule: StreamRule
```

Python (OpenAI)

```
from tweepy import OAuth2AppHandler
from tweepy.asynchronous import AsyncStreamingClient
from tweepy.streaming import StreamResponse

class XStream(AsyncStreamingClient):
    def __init__(self, x_api_key: str, x_api_secret: str):
        auth = OAuth2AppHandler(x_api_key, x_api_secret)
        super().__init__(bearer_token=auth._bearer_token)
        self.received_posts: dict[int, Post] = {}

    async def on_response(self, response: StreamResponse):
        post = response.data
        includes = response.includes
        users = includes.get("users", [])
        user_lookup = {user.id: user for user in users}
        post_author = user_lookup.get(post.author_id)
        if post_author is None:
            raise ValueError(f"Author not found for post {post.id}")

        author = Author(
            id=post_author.id,
            name=post_author.name,
            username=post_author.username,
            followers_count=post_author.public_metrics["followers_count"],
            following_count=post_author.public_metrics["following_count"],
            post_count=post_author.public_metrics["tweet_count"],
            listed_count=post_author.public_metrics["listed_count"],
            like_count=post_author.public_metrics["like_count"],
            media_count=post_author.public_metrics["media_count"],
            verified=post_author.verified,
        )

        post_object = Post(
            id=post.id,
            text=post.text,
            author_id=post.author_id,
            created_at=post.created_at,
            author=author,
            matching_rule=response.matching_rules[0],
        )

        if post_object.matching_rule.tag == GENERAL_BTC_RULE["tag"]:
            print(post_object)
            self.received_posts[post_object.id] = post_object
```

Python (OpenAI)

```
import os

from dotenv import load_dotenv

load_dotenv()

x_api_key = os.getenv("X_API_KEY")
if x_api_key is None:
    raise ValueError("X_API_KEY is not set")

x_api_secret = os.getenv("X_API_SECRET")
if x_api_secret is None:
    raise ValueError("X_API_SECRET is not set")

stream = XStream(x_api_key, x_api_secret)

# Uncomment to add the rule to the stream, if not already added
# await stream.add_rules(StreamRule(value=GENERAL_BTC_RULE["value"], tag=GENERAL_BTC_RULE["tag"]))

# Uncomment to check existing rules
# rules = await stream.get_rules()
# print(rules)
```

Let’s fire up the stream for a quick test:

Python (OpenAI)

```
import asyncio

await asyncio.wait_for(
    stream.filter(
        expansions=["author_id"],
        tweet_fields=["created_at", "author_id", "text"],
        user_fields=["name", "username", "verified", "public_metrics"],
    ),
    timeout=30,
)
```

Text

```
Post(id=1906531882981790069, text='A top trader by PnL on Drift just went long $27.25K of $BTC at $81,808.42', author_id=1884351032693547008, created_at=datetime.datetime(2025, 3, 31, 2, 19, 57, tzinfo=datetime.timezone.utc), author=Author(id=1884351032693547008, name='Whale Watch Perps', username='whalewatchperps', followers_count=11801, following_count=14, post_count=42641, listed_count=89, like_count=219, media_count=0, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531890502217808, text='JUST IN: 🇺🇸 Elon Musk calls to "end" the Federal Reserve. Good or Bad for $BTC?\nhttps://t.co/wigb2zOjju', author_id=1876560469558743040, created_at=datetime.datetime(2025, 3, 31, 2, 19, 59, tzinfo=datetime.timezone.utc), author=Author(id=1876560469558743040, name='Pudgy', username='PudgyWhal3', followers_count=2065, following_count=999, post_count=3922, listed_count=8, like_count=3322, media_count=1048, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531886844830027, text='WARNING: Alliedtopx wallet suspected of being unreliable due to limited reviews. If affected, seek assistance. #Alliedtopx #cryppeak #Zypbit #fobdex #elabits #DpcryptoX #whalliance #ronbit #RippleScam #scam #cryptoscam #cryptorecovery #scamalert #scammed #Crypto #BTC #ETH #XRP https://t.co/FkdY1oE6TQ', author_id=1733963998893137920, created_at=datetime.datetime(2025, 3, 31, 2, 19, 58, tzinfo=datetime.timezone.utc), author=Author(id=1733963998893137920, name='LOGAN ~crypto recovery expert', username='Real_LOD', followers_count=4037, following_count=4119, post_count=7475, listed_count=7, like_count=1071, media_count=3542, verified=False), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531896235786740, text='米国政府が100万ビットコイン購入を計画中🔥\n・マイケル・セイラー氏が追加210億ドル分のBTC購入💼\n・$MARAが20億ドル調達しBTC買い増しへ💸\nこれだけの買い圧が集まる中、弱気材料はどこにある⁉️\n\n#ビットコイン #暗号資産 #米国政府 #マイケルセイラー #MARA https://t.co/VhsRlzWp5O', author_id=1309264512634118144, created_at=datetime.datetime(2025, 3, 31, 2, 20, tzinfo=datetime.timezone.utc), author=Author(id=1309264512634118144, name='エックスウィンリサーチ 「市場変動を先読み、デジタル資産戦略の新基準を学ぶ」', username='xwinfinancejp', followers_count=1337, following_count=123, post_count=4209, listed_count=11, like_count=4518, media_count=2799, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531900098810255, text='🚀 $XRP to the moon! 🌕 Brad Garlinghouse &amp; #Ripple are reshaping the financial system! #Ripple  https://t.co/EQRBxvwFHA @rnhy23  #RLUSD #XRPCommunity #XRPHolders #binance #crypto $XRPL #TRUMP $ETH #XRP #BTC #ETH', author_id=1456035253693341699, created_at=datetime.datetime(2025, 3, 31, 2, 20, 1, tzinfo=datetime.timezone.utc), author=Author(id=1456035253693341699, name='Yankı Haber', username='yedi24yanki', followers_count=55926, following_count=74, post_count=30090, listed_count=70, like_count=45, media_count=26837, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531902086914480, text='Top 3 Bullish Sentiment Cryptos: CROWD\n\n 🟩 $NUTZ $BULL $SC\n\nTop 3 Bullish Cryptos: MP | #SmartMoney\n\n 🟩 $XRP $ETH $BTC\n    \nCheck out sentiment and other crypto stats at https://t.co/HQDyBNuzek\n\n#Crypto #Marketprophit', author_id=1423717651071840258, created_at=datetime.datetime(2025, 3, 31, 2, 20, 1, tzinfo=datetime.timezone.utc), author=Author(id=1423717651071840258, name='Market Prophit', username='MarketProphit', followers_count=98886, following_count=27055, post_count=380243, listed_count=77, like_count=8499, media_count=215420, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531907925594466, text='$AGIX holds firm at $0.20, with $0.73 in sight. $BTC is looking strong too. Traders should enter before momentum peaks, securing gains from $AGIX’s rally. \nMissed the last opportunity? Follow us on Twitter today and be ready for the next one: https://t.co/ZLOlYyTaJE https://t.co/dRTl5iMct6', author_id=1231355240500400128, created_at=datetime.datetime(2025, 3, 31, 2, 20, 3, tzinfo=datetime.timezone.utc), author=Author(id=1231355240500400128, name='Decilizer', username='decilizer', followers_count=5514, following_count=175, post_count=26288, listed_count=40, like_count=45279, media_count=22391, verified=False), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531914095239278, text='📰 Bitcoin Pepe accelerates presale momentum as whale bets on TRUMP\n\nhttps://t.co/TT19zTlZj5\n\n#world', author_id=531415099, created_at=datetime.datetime(2025, 3, 31, 2, 20, 4, tzinfo=datetime.timezone.utc), author=Author(id=531415099, name='invezz.com', username='InvezzPortal', followers_count=5235, following_count=224, post_count=53279, listed_count=74, like_count=798, media_count=21970, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531921179316499, text='Bit Bonds make zero sense to anyone with a basic understanding of finance. This is fanciful. https://t.co/xR8l8aUm4F', author_id=213032123, created_at=datetime.datetime(2025, 3, 31, 2, 20, 6, tzinfo=datetime.timezone.utc), author=Author(id=213032123, name='George Noble', username='gnoble79', followers_count=62209, following_count=3253, post_count=10350, listed_count=1078, like_count=4269, media_count=2578, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531939692994835, text='💥 Huge $XRP news! Garlinghouse &amp; #Ripple are making waves! 🌊 #Blockchain  https://t.co/1kUQJKVux0 @Jumesan3  #RLUSD #XRPCommunity #XRPHolders #binance #crypto $XRPL #TRUMP $ETH #XRP #BTC #ETH', author_id=1289215239372730375, created_at=datetime.datetime(2025, 3, 31, 2, 20, 10, tzinfo=datetime.timezone.utc), author=Author(id=1289215239372730375, name='ShreeTV', username='ShreeTV1', followers_count=6316, following_count=305, post_count=17854, listed_count=12, like_count=3156, media_count=9589, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531965937050090, text='$LADYS gears up for a rally, supported by $BABYDOGE and $MEW. Rising volume fuels confidence, but Bitcoin dominance remains a decisive factor. Monitoring $BTC will determine whether $LADYS capitalizes on momentum or faces resistance. https://t.co/JYI7L6SeQm', author_id=1231355240500400128, created_at=datetime.datetime(2025, 3, 31, 2, 20, 16, tzinfo=datetime.timezone.utc), author=Author(id=1231355240500400128, name='Decilizer', username='decilizer', followers_count=5514, following_count=175, post_count=26289, listed_count=40, like_count=45279, media_count=22392, verified=False), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531966960148668, text='#gothacked\n\n#RecoveryFund #Mywallet You will be capable again to stand in your financial position through our recovery process.💯\nDid you #Gotscammed #Scammed #Drainedwallet #Mywallet got hacked #gothacked #Lostmoney  #btc #Eth #Nft #crypto #solana #usdt SEND A MESSAGE NOW https://t.co/pAE6payNze', author_id=1652876737317838849, created_at=datetime.datetime(2025, 3, 31, 2, 20, 17, tzinfo=datetime.timezone.utc), author=Author(id=1652876737317838849, name='FlawlessCharles', username='Charlesflawless', followers_count=1265, following_count=26, post_count=778, listed_count=0, like_count=421, media_count=336, verified=False), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531979039830516, text='🇺🇸 Strategic reserve discussions! $XRP is in the spotlight – get involved now!   https://t.co/k8esQWzHNW @MScheiterbauer  #RLUSD #XRPCommunity #XRPHolders #binance #crypto $XRPL #TRUMP $ETH #XRP #BTC #ETH', author_id=1456035253693341699, created_at=datetime.datetime(2025, 3, 31, 2, 20, 20, tzinfo=datetime.timezone.utc), author=Author(id=1456035253693341699, name='Yankı Haber', username='yedi24yanki', followers_count=55925, following_count=74, post_count=30091, listed_count=70, like_count=45, media_count=26837, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
```

Ok nice, the posts rolling in match our rule’s criteria, Bitcoin mentions from accounts with 1,000+ followers, no retweets or replies. Next, we’ll sift through them to filter out the noise.

## [Bringing Grok into the Equation](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#bringing-grok-into-the-equation)

### [Filtering Noisy Posts](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#filtering-noisy-posts)

Our stream rule, despite its filters, grabs a lot - but not all of it’s useful. Noise like ads, spam, or vague tweets still creeps in. As laid out in the overview, we batch every 5 posts and send them to `grok-3`. Its job? Quickly classify which ones have signal - posts that could sway sentiment—and which don’t. We’re not computing sentiment here, just picking the keepers to stash for later. `grok-3`'s speed makes it perfect for this, sifting through the batch in no time.

Python (OpenAI)

```
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

class FilteredTweetIDs(BaseModel):
    IDs: list[int]

class GrokSentimentAnalyzer:
    def __init__(self, api_key: str, base_url: str = "https://api.x.ai/v1"):
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    async def classify_tweets(self, tweets: list[Any], prompt: str) -> FilteredTweetIDs:
        response = await self.client.beta.chat.completions.parse(
            model="grok-3-fast",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Here are the tweets: {tweets}"},
            ],
            response_format=FilteredTweetIDs,
        )

        if not response.choices[0].message.parsed:
            raise ValueError("No tweets were returned")

        return response.choices[0].message.parsed

    async def calculate_sentiment(self, tweets: list[Any], prompt: str) -> tuple[str, str]:
        response = await self.client.chat.completions.create(
            model="grok-3-mini",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {"role": "user", "content": f"Here are the tweets: {tweets}"},
            ],
        )

        if not response.choices[0].message.content:
            raise ValueError("No sentiment was returned")

        return response.choices[0].message.content, response.choices[0].message.reasoning_content
```

The prompt below tells `grok-3` to focus on tweet content—does it say something meaningful about Bitcoin market sentiment? While factoring in author details like follower count for credibility. It’s just one way to write it; you could tweak it to weigh authors more, add new rules, trivially changing it in plain English. That’s a perk of using LLMs here—no retraining like with classical ML, just update the prompt and go.

Python (OpenAI)

```
CLASSIFICATION_PROMPT = """You are an expert in bitcoin market sentiment analysis tasked with identifying tweets relevant to assessing bitcoin (BTC) market sentiment. Your goal is to analyze a list of tweets, including their IDs and author details (followers count, following count, tweet count, listed count, like count, media count, and verified status), and determine which tweets contain information useful for bitcoin market sentiment analysis. You will return only the IDs of relevant tweets.

To perform this task effectively, follow these instructions:

1. Examine the text content of each tweet to assess whether it discusses bitcoin (BTC) specifically in a way that could inform market sentiment analysis (e.g., opinions, trends, or observations about BTC’s market behavior).
2. Consider the author’s profile information (e.g., followers count, verified status) to evaluate the tweet’s potential influence or credibility, but prioritize the tweet content over the author’s stats.
3. Exclude tweets that are purely promotional (e.g., ads, spam, or self-serving hype) or unrelated to bitcoin market sentiment (e.g., off-topic or generic cryptocurrency mentions without BTC focus).
4. For each tweet, determine if its content provides meaningful insight into BTC market sentiment, not whether the sentiment is positive or negative—your task is classification, not sentiment prediction.
5. Compile and return a list of tweet IDs that meet the criteria for relevance to BTC market sentiment analysis. If no tweets qualify, return an empty list.

Key reminders:
- Focus solely on BTC-specific content, not general cryptocurrency discussions.
- Do not feel pressured to return IDs just because tweets are provided; it’s acceptable to return none if no tweets are relevant.
- Avoid over-interpreting vague or over-hyped tweets—relevance to market sentiment is the priority.
"""
```

Python (OpenAI)

```
xai_api_key = os.getenv("XAI_API_KEY")
if xai_api_key is None:
    raise ValueError("XAI_API_KEY is not set")

grok_client = GrokSentimentAnalyzer(xai_api_key)
```

Python (OpenAI)

```
filtered_tweets = await grok_client.classify_tweets(stream.received_posts.items(), CLASSIFICATION_PROMPT)
```

Python (OpenAI)

```
filtered_tweet_ids = [tweet_id for tweet_id in filtered_tweets.IDs]
filtered_tweet_list = [stream.received_posts[id] for id in filtered_tweet_ids]
non_filtered_tweet_list = [post for post_id, post in stream.received_posts.items() if post_id not in filtered_tweet_ids]

print("High Signal Tweets")
for tweet in filtered_tweet_list:
    print(tweet)
print("-"*100)
print("Noisy Tweets")
for tweet in non_filtered_tweet_list:
    print(tweet)
```

Text

```
High Signal Tweets
Post(id=1906531882981790069, text='A top trader by PnL on Drift just went long $27.25K of $BTC at $81,808.42', author_id=1884351032693547008, created_at=datetime.datetime(2025, 3, 31, 2, 19, 57, tzinfo=datetime.timezone.utc), author=Author(id=1884351032693547008, name='Whale Watch Perps', username='whalewatchperps', followers_count=11801, following_count=14, post_count=42641, listed_count=89, like_count=219, media_count=0, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531896235786740, text='米国政府が100万ビットコイン購入を計画中🔥\n・マイケル・セイラー氏が追加210億ドル分のBTC購入💼\n・$MARAが20億ドル調達しBTC買い増しへ💸\nこれだけの買い圧が集まる中、弱気材料はどこにある⁉️\n\n#ビットコイン #暗号資産 #米国政府 #マイケルセイラー #MARA https://t.co/VhsRlzWp5O', author_id=1309264512634118144, created_at=datetime.datetime(2025, 3, 31, 2, 20, tzinfo=datetime.timezone.utc), author=Author(id=1309264512634118144, name='エックスウィンリサーチ 「市場変動を先読み、デジタル資産戦略の新基準を学ぶ」', username='xwinfinancejp', followers_count=1337, following_count=123, post_count=4209, listed_count=11, like_count=4518, media_count=2799, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531902086914480, text='Top 3 Bullish Sentiment Cryptos: CROWD\n\n 🟩 $NUTZ $BULL $SC\n\nTop 3 Bullish Cryptos: MP | #SmartMoney\n\n 🟩 $XRP $ETH $BTC\n    \nCheck out sentiment and other crypto stats at https://t.co/HQDyBNuzek\n\n#Crypto #Marketprophit', author_id=1423717651071840258, created_at=datetime.datetime(2025, 3, 31, 2, 20, 1, tzinfo=datetime.timezone.utc), author=Author(id=1423717651071840258, name='Market Prophit', username='MarketProphit', followers_count=98886, following_count=27055, post_count=380243, listed_count=77, like_count=8499, media_count=215420, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531965937050090, text='$LADYS gears up for a rally, supported by $BABYDOGE and $MEW. Rising volume fuels confidence, but Bitcoin dominance remains a decisive factor. Monitoring $BTC will determine whether $LADYS capitalizes on momentum or faces resistance. https://t.co/JYI7L6SeQm', author_id=1231355240500400128, created_at=datetime.datetime(2025, 3, 31, 2, 20, 16, tzinfo=datetime.timezone.utc), author=Author(id=1231355240500400128, name='Decilizer', username='decilizer', followers_count=5514, following_count=175, post_count=26289, listed_count=40, like_count=45279, media_count=22392, verified=False), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
----------------------------------------------------------------------------------------------------
Noisy Tweets
Post(id=1906531890502217808, text='JUST IN: 🇺🇸 Elon Musk calls to "end" the Federal Reserve. Good or Bad for $BTC?\nhttps://t.co/wigb2zOjju', author_id=1876560469558743040, created_at=datetime.datetime(2025, 3, 31, 2, 19, 59, tzinfo=datetime.timezone.utc), author=Author(id=1876560469558743040, name='Pudgy', username='PudgyWhal3', followers_count=2065, following_count=999, post_count=3922, listed_count=8, like_count=3322, media_count=1048, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531886844830027, text='WARNING: Alliedtopx wallet suspected of being unreliable due to limited reviews. If affected, seek assistance. #Alliedtopx #cryppeak #Zypbit #fobdex #elabits #DpcryptoX #whalliance #ronbit #RippleScam #scam #cryptoscam #cryptorecovery #scamalert #scammed #Crypto #BTC #ETH #XRP https://t.co/FkdY1oE6TQ', author_id=1733963998893137920, created_at=datetime.datetime(2025, 3, 31, 2, 19, 58, tzinfo=datetime.timezone.utc), author=Author(id=1733963998893137920, name='LOGAN ~crypto recovery expert', username='Real_LOD', followers_count=4037, following_count=4119, post_count=7475, listed_count=7, like_count=1071, media_count=3542, verified=False), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531900098810255, text='🚀 $XRP to the moon! 🌕 Brad Garlinghouse &amp; #Ripple are reshaping the financial system! #Ripple  https://t.co/EQRBxvwFHA @rnhy23  #RLUSD #XRPCommunity #XRPHolders #binance #crypto $XRPL #TRUMP $ETH #XRP #BTC #ETH', author_id=1456035253693341699, created_at=datetime.datetime(2025, 3, 31, 2, 20, 1, tzinfo=datetime.timezone.utc), author=Author(id=1456035253693341699, name='Yankı Haber', username='yedi24yanki', followers_count=55926, following_count=74, post_count=30090, listed_count=70, like_count=45, media_count=26837, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531907925594466, text='$AGIX holds firm at $0.20, with $0.73 in sight. $BTC is looking strong too. Traders should enter before momentum peaks, securing gains from $AGIX’s rally. \nMissed the last opportunity? Follow us on Twitter today and be ready for the next one: https://t.co/ZLOlYyTaJE https://t.co/dRTl5iMct6', author_id=1231355240500400128, created_at=datetime.datetime(2025, 3, 31, 2, 20, 3, tzinfo=datetime.timezone.utc), author=Author(id=1231355240500400128, name='Decilizer', username='decilizer', followers_count=5514, following_count=175, post_count=26288, listed_count=40, like_count=45279, media_count=22391, verified=False), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531914095239278, text='📰 Bitcoin Pepe accelerates presale momentum as whale bets on TRUMP\n\nhttps://t.co/TT19zTlZj5\n\n#world', author_id=531415099, created_at=datetime.datetime(2025, 3, 31, 2, 20, 4, tzinfo=datetime.timezone.utc), author=Author(id=531415099, name='invezz.com', username='InvezzPortal', followers_count=5235, following_count=224, post_count=53279, listed_count=74, like_count=798, media_count=21970, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531921179316499, text='Bit Bonds make zero sense to anyone with a basic understanding of finance. This is fanciful. https://t.co/xR8l8aUm4F', author_id=213032123, created_at=datetime.datetime(2025, 3, 31, 2, 20, 6, tzinfo=datetime.timezone.utc), author=Author(id=213032123, name='George Noble', username='gnoble79', followers_count=62209, following_count=3253, post_count=10350, listed_count=1078, like_count=4269, media_count=2578, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531939692994835, text='💥 Huge $XRP news! Garlinghouse &amp; #Ripple are making waves! 🌊 #Blockchain  https://t.co/1kUQJKVux0 @Jumesan3  #RLUSD #XRPCommunity #XRPHolders #binance #crypto $XRPL #TRUMP $ETH #XRP #BTC #ETH', author_id=1289215239372730375, created_at=datetime.datetime(2025, 3, 31, 2, 20, 10, tzinfo=datetime.timezone.utc), author=Author(id=1289215239372730375, name='ShreeTV', username='ShreeTV1', followers_count=6316, following_count=305, post_count=17854, listed_count=12, like_count=3156, media_count=9589, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531966960148668, text='#gothacked\n\n#RecoveryFund #Mywallet You will be capable again to stand in your financial position through our recovery process.💯\nDid you #Gotscammed #Scammed #Drainedwallet #Mywallet got hacked #gothacked #Lostmoney  #btc #Eth #Nft #crypto #solana #usdt SEND A MESSAGE NOW https://t.co/pAE6payNze', author_id=1652876737317838849, created_at=datetime.datetime(2025, 3, 31, 2, 20, 17, tzinfo=datetime.timezone.utc), author=Author(id=1652876737317838849, name='FlawlessCharles', username='Charlesflawless', followers_count=1265, following_count=26, post_count=778, listed_count=0, like_count=421, media_count=336, verified=False), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
Post(id=1906531979039830516, text='🇺🇸 Strategic reserve discussions! $XRP is in the spotlight – get involved now!   https://t.co/k8esQWzHNW @MScheiterbauer  #RLUSD #XRPCommunity #XRPHolders #binance #crypto $XRPL #TRUMP $ETH #XRP #BTC #ETH', author_id=1456035253693341699, created_at=datetime.datetime(2025, 3, 31, 2, 20, 20, tzinfo=datetime.timezone.utc), author=Author(id=1456035253693341699, name='Yankı Haber', username='yedi24yanki', followers_count=55925, following_count=74, post_count=30091, listed_count=70, like_count=45, media_count=26837, verified=True), matching_rule=StreamRule(value=None, tag='generic_btc', id='1900694588819451904'))
```

The split above shows it’s working: high-signal tweets carry BTC market insights, while noisy ones are mostly promo, hype/spam or off-topic.

### [Computing the Sentiment](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#computing-the-sentiment)

With our high-signal posts filtered, we’re ready to score Bitcoin’s market sentiment. We batch the first 5 keepers—per the overview—and hand them to `grok-3-mini`. It digs into the text, weighs author influence, and outputs a score from -1 (bearish) to 1 (bullish), with 0 being neutral.

The prompt below tells Grok to analyze tweet content for sentiment, factor in follower count and author prominence, and average it into a final score, formatting its answer such that it includes its reasoning and the key tweets that lead to that score. Again, this prompt is easily modifiable to add/remove instructions/criteria based on your requirements.

Python (OpenAI)

```
SENTIMENT_PROMPT = """You are an expert Bitcoin market analyst tasked with generating a sentiment score for Bitcoin (BTC) based exclusively on provided Twitter (X) posts. Your role is to evaluate these posts and assign a sentiment score ranging from -1 (bearish) to 1 (bullish), with 0 indicating neutral, reflecting the overall market sentiment toward BTC.

To perform this task effectively, follow these numbered instructions:

1. Analyze the content of each X post to determine its sentiment toward Bitcoin—look for expressions of optimism (bullish), pessimism (bearish), or neutrality (e.g., factual statements without clear bias).
2. Assess the author’s follower count to gauge the post’s potential reach and influence on market sentiment.
3. Evaluate whether the author is a prominent figure or a well-known organization in the crypto or finance industry, as this may amplify the post’s credibility or impact.
4. Weigh each post’s influence by combining the sentiment expressed in the content with the author’s reach and credibility—prioritize posts from influential authors with clear sentiment signals.
5. After reviewing all posts, calculate a final sentiment score (between -1 and 1) by averaging the weighted sentiments, rounding to one decimal place if needed.
6. Prepare your response in the specified format: include the BTC sentiment score, a concise reasoning paragraph explaining your conclusion, and a list of key tweet IDs with brief notes on their influence.

Output your response in this format:
BTC Sentiment: <score between -1 and 1>
Reasoning: <brief explanation of how you arrived at the score>
Key tweets: <list of tweet IDs and a short note on why each was influential>

Example output:
BTC Sentiment: 0.8
Reasoning: Most posts expressed optimism about Bitcoin’s price trajectory, with strong influence from high-follower accounts in the crypto space.
Key tweets:
- ID: 12345 (Crypto influencer with 500k followers predicting a bull run)
- ID: 67890 (Finance org with 1M followers citing positive BTC adoption trends)

Key reminders:
- Base your analysis solely on the provided X posts—do not use external data unless explicitly instructed.
- Focus on sentiment specific to Bitcoin (BTC), not cryptocurrencies in general.
- Ensure your reasoning is concise yet clearly justifies the score and key tweet selections.
"""
```

Python (OpenAI)

```
sentiment_result, reasoning_tokens = await grok_client.calculate_sentiment(filtered_tweet_list, SENTIMENT_PROMPT)
```

Python (OpenAI)

```
print(sentiment_result)
```

Text

```
**BTC Sentiment: 0.5**
**Reasoning:** The overall sentiment towards Bitcoin (BTC) is moderately bullish, driven by tweets expressing optimism about its price trajectory and market influence. The most influential tweet came from "Market Prophit," a known crypto insights provider with a large following, listing BTC among the top bullish cryptos. Another tweet reported a top trader going long on BTC, a bullish signal, while a third highlighted significant buying pressure from major players like the US government and Michael Saylor, though its impact was limited by a smaller following. The fourth tweet was neutral, acknowledging BTC's dominance without expressing clear sentiment. Weighing the sentiment of each tweet by the author's reach and credibility, the overall score leans towards bullish but remains moderate due to the mix of sentiments and varying influence levels.

**Key tweets:**
- **ID: 1906531902086914480** (Market Prophit with 98,886 followers, listing BTC as a top bullish crypto, high influence due to large reach and credibility)
- **ID: 1906531882981790069** (Whale Watch Perps with 11,801 followers, reporting a top trader going long on BTC, moderate influence due to verified account and factual reporting)
- **ID: 1906531896235786740** (Xwin Research with 1,337 followers, strongly bullish content about major BTC purchases, low influence due to small following)
- **ID: 1906531965937050090** (Decilizer with 5,514 followers, neutral sentiment acknowledging BTC's dominance, low influence due to lack of clear bias)
```

What’s cool here? Beyond the final sentiment result, we can peek at Grok's reasoning tokens, think of this as Grok's thought process that it went through before coming up with its final sentiment score. This can be very valuable when you're looking to debug or edit your prompt; seeing which paths or choices the model is making means you can make more targeted prompt modifications to achieve your desired behavior.

In the case below, we can see that Grok is actually computing the final score by means of a weighted average of the individual posts, which is an interesting insight.

Python (OpenAI)

```
print(reasoning_tokens)
```

Text

```
I'm analyzing these four tweets to determine the overall sentiment towards Bitcoin (BTC). I'll look at the content, author's follower count, and whether the author is a prominent figure in the crypto or finance industry.

First tweet (ID: 1906531882981790069): "A top trader by PnL on Drift just went long $27.25K of $BTC at $81,808.42"

- Content: This tweet reports a top trader going long on BTC, which is a bullish signal.
- Author: "Whale Watch Perps" with 11,801 followers. Not a huge following, but still significant.
- Prominence: Not a well-known figure in the crypto space, but the account is verified, which adds some credibility.
- Influence: The tweet itself is neutral in tone, just reporting a fact, but the action described (going long) is bullish.

Second tweet (ID: 1906531896235786740): "米国政府が100万ビットコイン購入を計画中🔥\n・マイケル・セイラー氏が追加210億ドル分のBTC購入💼\n・$MARAが20億ドル調達しBTC買い増しへ💸\nこれだけの買い圧が集まる中、弱気材料はどこにある⁉️\n\n#ビットコイン #暗号資産 #米国政府 #マイケルセイラー #MARA https://t.co/VhsRlzWp5O"

- Content: This tweet is in Japanese and translates to: "The US government is planning to purchase 1 million Bitcoins 🔥\n- Michael Saylor is purchasing an additional $2.1 billion worth of BTC 💼\n- MARA has raised $2 billion and is increasing its BTC purchases 💸\nWith this much buying pressure, where are the bearish factors?⁉️\n\n#Bitcoin #Cryptocurrency #USGovernment #MichaelSaylor #MARA"
- Author: "エックスウィンリサーチ 「市場変動を先読み、デジタル資産戦略の新基準を学ぶ」" (Xwin Research) with 1,337 followers. A relatively small following.
- Prominence: Not a well-known figure or organization in the crypto space.
- Influence: The tweet is strongly bullish, mentioning large purchases by the US government, Michael Saylor, and MARA. However, the small following limits its impact.

Third tweet (ID: 1906531902086914480): "Top 3 Bullish Sentiment Cryptos: CROWD\n\n 🟩 $NUTZ $BULL $SC\n\nTop 3 Bullish Cryptos: MP | #SmartMoney\n\n 🟩 $XRP $ETH $BTC\n    \nCheck out sentiment and other crypto stats at https://t.co/HQDyBNuzek\n\n#Crypto #Marketprophit"

- Content: This tweet lists BTC among the top 3 bullish cryptos, which is a positive sentiment.
- Author: "Market Prophit" with 98,886 followers. A significant following.
- Prominence: Market Prophit is a known entity in the crypto space, providing market insights.
- Influence: The tweet is bullish towards BTC, and the large following amplifies its impact.

Fourth tweet (ID: 1906531965937050090): "$LADYS gears up for a rally, supported by $BABYDOGE and $MEW. Rising volume fuels confidence, but Bitcoin dominance remains a decisive factor. Monitoring $BTC will determine whether $LADYS capitalizes on momentum or faces resistance. https://t.co/JYI7L6SeQm"

- Content: This tweet mentions BTC as a decisive factor for another crypto's rally, implying its importance but not directly expressing sentiment towards BTC.
- Author: "Decilizer" with 5,514 followers. A moderate following.
- Prominence: Not a well-known figure in the crypto space.
- Influence: The tweet is neutral towards BTC, focusing on another crypto but acknowledging BTC's dominance.

Now, I'll weigh each tweet's influence by combining the sentiment expressed in the content with the author's reach and credibility.

First tweet: Bullish sentiment, moderate reach, verified account. Influence: Moderate

Second tweet: Strongly bullish sentiment, small reach. Influence: Low

Third tweet: Bullish sentiment, large reach, known entity. Influence: High

Fourth tweet: Neutral sentiment, moderate reach. Influence: Low

I'll assign sentiment scores to each tweet:

First tweet: 0.5 (bullish action reported, but neutral tone)

Second tweet: 0.8 (strongly bullish content)

Third tweet: 0.7 (bullish sentiment, large reach)

Fourth tweet: 0.0 (neutral sentiment)

Now, I'll calculate the final sentiment score by averaging the weighted sentiments. Since the third tweet has the highest influence, I'll give it more weight in the calculation.

Weighted average: (0.5 * 1) + (0.8 * 0.5) + (0.7 * 2) + (0.0 * 0.5) / (1 + 0.5 + 2 + 0.5) = (0.5 + 0.4 + 1.4 + 0.0) / 4.5 = 2.3 / 4.5 ≈ 0.51

Rounding to one decimal place, the final sentiment score is 0.5.
```

## [Piecing it all Together](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#piecing-it-all-together)

This is where it all comes together—stream, filter, and score in real time. Run the cell below to watch posts flow in, get classified by `grok-3`, and see the sentiment update live with `grok-3-mini` all in real-time.

Python (OpenAI)

```
from IPython.display import clear_output

class UpdatedXStream(AsyncStreamingClient):
    def __init__(self, x_api_key: str, x_api_secret: str, grok_client: GrokSentimentAnalyzer):
        auth = OAuth2AppHandler(x_api_key, x_api_secret)
        super().__init__(bearer_token=auth._bearer_token)
        self.grok_client = grok_client
        self.high_quality_tweets: list[Post] = []
        self.current_sentiment = ""
        self.processed_tweets = 0
        self.received_posts: dict[int, Post] = {}
        self.tweet_batch: list[Post] = []

    async def on_response(self, response: StreamResponse):
        post = response.data
        includes = response.includes
        users = includes.get("users", [])
        user_lookup = {user.id: user for user in users}
        post_author = user_lookup.get(post.author_id)
        if post_author is None:
            raise ValueError(f"Author not found for post {post.id}")

        author = Author(
            id=post_author.id,
            name=post_author.name,
            username=post_author.username,
            followers_count=post_author.public_metrics["followers_count"],
            following_count=post_author.public_metrics["following_count"],
            post_count=post_author.public_metrics["tweet_count"],
            listed_count=post_author.public_metrics["listed_count"],
            like_count=post_author.public_metrics["like_count"],
            media_count=post_author.public_metrics["media_count"],
            verified=post_author.verified,
        )

        post_object = Post(
            id=post.id,
            text=post.text,
            author_id=post.author_id,
            created_at=post.created_at,
            author=author,
            matching_rule=response.matching_rules[0],
        )

        if post_object.matching_rule.tag == GENERAL_BTC_RULE["tag"]:

            self.processed_tweets += 1
            # Clear previous output and display new two-line status
            clear_output(wait=True)
            print(f"Processed {self.processed_tweets} tweets")
            print(f"High Quality Candidates: {len(self.high_quality_tweets)}")
            print(f"Latest Tweet: {post_object.text}")
            print(f"Current Sentiment: {self.current_sentiment}")
            self.received_posts[post_object.id] = post
            self.tweet_batch.append(post_object)
            if len(self.tweet_batch) == 5:
                filtered_tweet_ids = await self.grok_client.classify_tweets(self.tweet_batch, CLASSIFICATION_PROMPT)
                self.high_quality_tweets.extend([self.received_posts[tweet_id] for tweet_id in filtered_tweet_ids.IDs])
                self.tweet_batch = []
            if len(self.high_quality_tweets) > 3:
                self.current_sentiment = await self.grok_client.calculate_sentiment(self.high_quality_tweets, SENTIMENT_PROMPT)
```

Python (OpenAI)

```
stream = UpdatedXStream(x_api_key, x_api_secret, grok_client)

await asyncio.wait_for(
    stream.filter(
        expansions=["author_id"],
        tweet_fields=["created_at", "author_id", "text"],
        user_fields=["name", "username", "verified", "public_metrics"],
    ),
    timeout=60,
)
```

Text

```
Processed 12 tweets
High Quality Candidates: 5
Latest Tweet: 🚨 SCAM ALERT!

#Dexozer is restricting access to user funds! ❌If you’ve been affected,DM me now for recovery assistance! #Cryppeak
#ZYPBIT
#Fobdex
#Sixzt
#Ultimaprime #finance #cryptorecovery #cryptoscam #cryptohelp #Scam #XRP #Scammed #Scamalert #BTC https://t.co/R7b4LRLrMq
Current Sentiment: ("BTC Sentiment: -0.1  \nReasoning: The overall sentiment toward Bitcoin (BTC) is slightly bearish, driven by a mix of negative and positive signals. The most influential bearish factor is the Whale Alert tweet, which reports a large whale shorting BTC with high leverage, indicating significant pessimism from a credible source. This is reinforced by a negative tweet comparing BTC unfavorably to the S&P 500, though from a less influential user. On the bullish side, Michael Saylor's mention of MicroStrategy potentially buying more BTC carries strong weight due to his prominence in the crypto space, signaling confidence. However, a bearish price prediction from a less influential user and a neutral/slightly positive tweet about short-term BTC trading from another user with moderate influence do not offset the negative momentum. The weighted average of these sentiments results in a slightly bearish score of -0.1.  \n\nKey tweets:  \n- ID: 1906533644686008357 (Whale Alert reports a whale shorting BTC with high leverage, a credible and bearish signal with significant influence)  \n- ID: 1906533664516690315 (Michael Saylor's mention of MicroStrategy potentially buying more BTC, a bullish signal from a highly influential figure)  \n- ID: 1906533734863790322 (A neutral/slightly positive tweet about preferring to trade BTC short-term, included as a minor key tweet due to moderate influence)", 'Alright, let\'s break this down. I need to analyze these tweets to determine the sentiment towards Bitcoin. The first tweet is about a whale shorting BTC with high leverage. That\'s bearish, right? It indicates someone with a lot of money is betting against Bitcoin\'s price going up. The second tweet is clearly negative, comparing Bitcoin\'s performance unfavorably to the S&P 500 and using strong language. That\'s definitely bearish. The third tweet is about Michael Saylor suggesting MicroStrategy might buy more Bitcoin. That\'s positive, as it shows confidence in Bitcoin\'s value. The fourth tweet is a prediction of Bitcoin\'s price decreasing, which is bearish. The last tweet is in Chinese, but it seems to be about preferring to trade Bitcoin short-term rather than other cryptocurrencies, which might be neutral or slightly positive for Bitcoin, as it indicates some interest in trading it.\n\nNow, I need to consider the authors\' influence. The first tweet is from "Whale Alert," which is a well-known account in the crypto space with a large following. That gives it more weight. The second tweet is from an individual user, and without knowing their follower count, I\'ll assume they have less influence. The third tweet is about Michael Saylor, who is a prominent figure in the crypto world, so that carries significant weight. The fourth tweet is from another individual user, again with unknown influence. The last tweet is also from an individual user, and without context, I\'ll assume moderate influence.\n\nI should also consider the credibility of the sources. Whale Alert is a reputable source for tracking large transactions, so their tweet is credible. Michael Saylor is a well-known advocate for Bitcoin, so his statements carry weight. The other tweets are from individual users, so their credibility is less certain.\n\nNow, I need to weigh these sentiments. The first tweet is bearish and from a credible source, so it should have a significant negative impact. The second tweet is also bearish but from a less influential source, so it should have a smaller negative impact. The third tweet is bullish and from a highly influential source, so it should have a significant positive impact. The fourth tweet is bearish but from a less influential source, so it should have a smaller negative impact. The last tweet is neutral or slightly positive but from a less influential source, so it should have a minimal impact.\n\nLet\'s assign some weights. For the first tweet, I\'ll give it a weight of -0.5. For the second tweet, -0.2. For the third tweet, +0.5. For the fourth tweet, -0.2. For the last tweet, +0.1.\n\nNow, I need to calculate the average of these weights. Adding them up: -0.5 + (-0.2) + 0.5 + (-0.2) + 0.1 = -0.3. Dividing by 5 tweets: -0.3 / 5 = -0.06.\n\nRounding to one decimal place, the sentiment score is -0.1.\n\nI think that\'s a fair assessment. The negative sentiments from the whale shorting and the negative prediction outweigh the positive sentiment from Michael Saylor\'s statement, but the overall sentiment is still slightly negative.\n\nNow, I need to identify the key tweets. The first tweet from Whale Alert is key because it\'s from a credible source and indicates a significant bearish move. The third tweet about Michael Saylor is key because it\'s from a highly influential figure and shows confidence in Bitcoin. The second and fourth tweets are less influential, so I\'ll exclude them from the key tweets list. The last tweet is also less influential, but it does show some interest in Bitcoin, so I\'ll include it as a minor key tweet.\n\nI think I\'ve got it. Let\'s put it all together.')
```

## [Conclusion](https://docs.x.ai/cookbook/examples/sentiment_analysis_on_x#conclusion)

We’ve built a tool that pulls Bitcoin posts from X’s Filtered Stream API, filters noise with `grok-3`, and scores sentiment in real time with `grok-3-mini`'s reasoning. It’s a lean, composable system—each piece (streaming, filtering, scoring) slots together to deliver live market insights.

Here’s what we’ve learned:

- A modular setup can often be favorable to a monolith, swap models or tune parts without breaking the whole.
- Match tasks to model strengths, `grok-3`’s speed for filtering and `grok-3-mini`’s reasoning for sentiment.
- Prompts are flexible—tweak them in plain English to shift focus and adjust behavior according to your needs.
- LLMs like Grok thrive here: multilingual, adaptable, and quick to iterate.

Want to push it further? For high-quality tweets with links or media, let Grok dig into the content—summarize articles or gauge visual sentiment using its [image understanding capabilities](https://docs.x.ai/docs/guides/image-understanding). Or go dynamic: have Grok craft stream rules on the fly based on real-world events (e.g., “BTC crash” after a dip). Experiment, tweak, and see where it takes you.