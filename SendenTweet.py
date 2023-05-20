import tweepy
import os
import random
#secretsで設定した値をとる

CONSUMER_KEY = os.environ.get('CONSUMER_KEY', "")

CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', "")

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', "")

ACCESS_SECRET = os.environ.get('ACCESS_SECRET', "")

#認証

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)

auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

#オブジェクト作成

api = tweepy.API(auth)

client = tweepy.Client(

	consumer_key = CONSUMER_KEY,	consumer_secret = CONSUMER_SECRET,

	access_token = ACCESS_TOKEN,

	access_token_secret = ACCESS_SECRET

)a
sendens = []
sendens.append("このアカウントはスケジュール更新やゲソタウン更新など、n様々な情報をツイートするスプラトゥーンのbotです！/n素早く新情報を伝えるので是非フォローしてください！/n#スプラトゥーン/n#サーモンラン")
client.create_tweet(text=random.choice(sendens))