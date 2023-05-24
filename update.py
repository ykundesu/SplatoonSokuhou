from apiclient.discovery import build
from datetime import datetime,timedelta
from deta import Deta
import tweepy
import time
import os
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
	consumer_key = CONSUMER_KEY,
	consumer_secret = CONSUMER_SECRET,
	access_token = ACCESS_TOKEN,
	access_token_secret = ACCESS_SECRET
)

statusdb = Deta(os.environ.get('SPSOKUHOU_DETA', "")).Base("SSStatus")
lastsplatoonid = statusdb.get("lastsplatoonid")
if lastsplatoonid is not None:
    lastsplatoonid = lastsplatoonid["value"]

API_KEY = os.environ.get("YOUTUBEAPIKEY","")
API_VER = 'v3'

youtube = build('youtube', API_VER, developerKey=API_KEY)
def getChannelPlaylistId(channel_id):
  channel = youtube.channels().list(part='snippet,contentDetails', id=channel_id).execute()
  item = channel['items'][0]
  playlist_id = item['contentDetails']['relatedPlaylists']['uploads']
  return playlist_id
def getNSVideos():
    items_info = youtube.playlistItems().list(part='snippet,contentDetails', playlistId="UUkH3CcMfqww9RsZvPRPkAJA", maxResults=50).execute()
    videos = []
    for item in items_info["items"]:
        if "スプラトゥーン" not in item["snippet"]["title"]:
            continue
        video = {}
        video["title"] = item["snippet"]["title"]
        video["strtime"] = item["snippet"]["publishedAt"]
        video["time"] = datetime.strptime(item["snippet"]["publishedAt"], '%Y-%m-%dT%H:%M:%SZ')
        video["Id"] = item["contentDetails"]["videoId"]
        videos.append(video)
    return videos
while True:
    spVideos = getNSVideos()
    if len(spVideos) > 0:
        if spVideos[0]["Id"] != lastsplatoonid:
            targetVideos = []
            for vd in spVideos:
                if vd["Id"] == lastsplatoonid:
                    break
                tweettext =  "新しいスプラトゥーンの公式動画がアップロードされました！\n"
                tweettext += "▼動画名\n"
                tweettext += vd["title"]+"\n"
                tweettext += "▼公開時間\n"
                tweettext += (vd["time"] + timedelta(hours=9)).strftime('%Y年%m月%d日%H時%M分%S秒') +"\n"
                tweettext += "https://www.youtube.com/watch?v="+vd["Id"]
                print(tweettext)
                client.create_tweet(text=tweettext)
            lastsplatoonid = spVideos[0]["Id"]
            statusdb.put(lastsplatoonid,"lastsplatoonid")
    utcnow = datetime.utcnow()
    if utcnow.hour == 0 or utcnow.hour == 4 or utcnow.hour == 8 or utcnow.hour == 12 or utcnow.hour == 16 or utcnow.hour == 20:
        if utcnow.minute == 47:
            break
    time.sleep(20)
#print(youtube.search().list(q = '任天堂',
#    part = 'snippet',
#    type = 'channel', # channel, playlist, video
#		maxResults = 10).execute())
