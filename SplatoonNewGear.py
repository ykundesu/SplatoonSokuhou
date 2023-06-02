import tweepy
from PIL import Image, ImageDraw, ImageFont
import requests
import io
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
json = requests.get("https://splatoon3.ink/data/coop.json").json()["data"]["coopResult"]["monthlyGear"]
transjson = requests.get("https://splatoon3.ink/data/locale/ja-JP.json").json()
def GetTranslation(transtype, textid):
    return transjson.get(transtype,{}).get(textid, {}).get("name","翻訳できませんでした。")
font = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 40)
gearname = GetTranslation("gear", json["__splatoon3ink_id"])
tweettext =  "サーモンランギア更新！\n"
tweettext += "今月のギアは「"+gearname+"」です！"
print(tweettext)
back = Image.open("SplatoonBack_White.png").crop((0,0,320,370))
img = Image.open("SplatoonBack_Black.png")
img = img.resize((int(img.size[0] / 2.5),
                  int(img.size[1] / 2.5))).crop((0,0,280,270))
gear = Image.open(io.BytesIO(requests.get(json["image"]["url"]).content))
img.paste(gear, (10,2), gear)
draw = ImageDraw.Draw(back)
draw.text((160,330),gearname,font=font, fill = "#000000",anchor='mm')
mask = Image.new("L", img.size, 0)
radius = 35
draw = ImageDraw.Draw(mask)
draw.rounded_rectangle((0, 0, img.width, img.height), radius, fill=255)
back.paste(img, (20,20), mask=mask)
back.save("newgear.png")
medias = []
medias.append(api.media_upload(filename="newgear.png").media_id)
tweetid = client.create_tweet(text=tweettext, media_ids = medias).data["id"]
try:
    payload = {"title":"サーモンランギア更新",
               "url":"https://twitter.com/SplatoonSokuhou/status/"+str(tweetid),
               "body":"サーモンランのギアが更新されました！\n今月のギアは「"+gearname+"」です！"
               }
    pusher.PushMsg("SalmonChangeGear",payload)
except Exception as e:
    print(str(e))
