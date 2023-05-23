import utils
import random
import os
import tweepy
import io
import requests
import sys
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from deta import Deta
statusdb = Deta(os.environ.get('SPSOKUHOU_DETA', "")).Base("SSStatus")
lastquiz = statusdb.get("lastquiz")

lastquizid = None
lastquizanswer = None
lastquizanswerimg = None
if lastquiz is not None:
    lastquizid = lastquiz["tweetid"]
    lastquizanswer = lastquiz["answer"]
    lastquizanswerimg = lastquiz["answerimg"]
utcnow = datetime.utcnow()
if utcnow.hour != 14 and utcnow.hour != 15 and utcnow.hour != 2 and utcnow.hour != 3:
    sys.exit()
QuizTypes = ["このブキの名前はなにだろう？",
             "このブキのサブはなんだ？",
             "このブキのスペシャルは何？",
             "このスペシャルの名前は？",
             "このサブの名前は？"]
weapons = utils.GetWeapons()
quiztype = random.choice(range(len(QuizTypes)))
weaponids = list(range(len(weapons)))
answer = None
quizweaponname = None
Options = []
if quiztype == 0:
    targetweaponindex = random.choice(range(len(weapons)))
    targetweapon = weapons[targetweaponindex]
    answer = targetweapon["name"]
    quizimage = targetweapon["image3d"]
    answerimage = targetweapon["image3d"]
    Options.append(answer)
    weapons.remove(targetweapon)
    for index in range(3):
        randomweaponindex = random.choice(range(len(weapons)))
        randomweapon = weapons[randomweaponindex]
        weapons.remove(randomweapon)
        Options.append(randomweapon["name"])
elif quiztype==1:
    targetweaponindex = random.choice(range(len(weapons)))
    targetweapon = weapons[targetweaponindex]
    answer = targetweapon["subWeapon"]["name"]
    quizimage = targetweapon["image3d"]
    quizweaponname = targetweapon["name"]
    answerimage = targetweapon["subWeapon"]["image"]
    Options.append(answer)
    weapons.remove(targetweapon)
    for index in range(3):
        randomweaponindex = random.choice(range(len(weapons)))
        randomweapon = weapons[randomweaponindex]
        weapons.remove(randomweapon)
        Options.append(randomweapon["subWeapon"]["name"])
elif quiztype==2:
    targetweaponindex = random.choice(range(len(weapons)))
    targetweapon = weapons[targetweaponindex]
    answer = targetweapon["specialWeapon"]["name"]
    quizimage = targetweapon["image3d"]
    quizweaponname = targetweapon["name"]
    answerimage = targetweapon["specialWeapon"]["image"]
    Options.append(answer)
    weapons.remove(targetweapon)
    for index in range(3):
        randomweaponindex = random.choice(range(len(weapons)))
        randomweapon = weapons[randomweaponindex]
        weapons.remove(randomweapon)
        Options.append(randomweapon["specialWeapon"]["name"])
elif quiztype==3:
    targetweaponindex = random.choice(range(len(weapons)))
    targetweapon = weapons[targetweaponindex]
    answer = targetweapon["specialWeapon"]["name"]
    quizimage = targetweapon["specialWeapon"]["image"]
    quizweaponname = None
    answerimage = targetweapon["specialWeapon"]["image"]
    Options.append(answer)
    specials = []
    for ws in weapons:
        if not (ws["specialWeapon"]["name"] in specials):
            specials.append(ws["specialWeapon"]["name"])
    specials.remove(targetweapon["specialWeapon"]["name"])
    for index in range(3):
        randomweaponindex = random.choice(range(len(specials)))
        randomweapon = specials[randomweaponindex]
        specials.remove(randomweapon)
        Options.append(randomweapon)
elif quiztype==4:
    targetweaponindex = random.choice(range(len(weapons)))
    targetweapon = weapons[targetweaponindex]
    answer = targetweapon["subWeapon"]["name"]
    quizimage = targetweapon["subWeapon"]["image"]
    quizweaponname = None
    answerimage = targetweapon["subWeapon"]["image"]
    Options.append(answer)
    specials = []
    for ws in weapons:
        if not (ws["subWeapon"]["name"] in specials):
            specials.append(ws["subWeapon"]["name"])
    specials.remove(targetweapon["subWeapon"]["name"])
    for index in range(3):
        randomweaponindex = random.choice(range(len(specials)))
        randomweapon = specials[randomweaponindex]
        specials.remove(randomweapon)
        Options.append(randomweapon)
random.shuffle(Options)
#print(answer)
#print(Options)
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
back = Image.open("SplatoonBack_White.png").crop((0,0,400,575))
img = Image.open("SplatoonBack_Black.png").crop((0,0,250,250))
font_big = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 45)
font = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 30)
font_min = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 28)
quizimg = Image.open(io.BytesIO(requests.get(quizimage).content))
quizimg = quizimg.resize((200,200)).convert("RGBA")
#print(quizimg.size)
draw = ImageDraw.Draw(img)
ypos = 20
if quizweaponname != None:
    draw.text((125,220), quizweaponname, font = font_min, fill = "#FFFFFF",anchor='mm')
    ypos = 0
img.paste(quizimg,(22,ypos),quizimg)
# 角丸にするためのマスクを作成
mask = Image.new("L", img.size, 0)
radius = 50
draw = ImageDraw.Draw(mask)
draw.rounded_rectangle((0, 0, img.width, img.height), radius, fill=255)
back.paste(img,(75,75),mask=mask)
draw = ImageDraw.Draw(back)
draw.text((202,40), QuizTypes[quiztype], font = font, fill = "#000000",anchor='mm')
index = 0
for option in Options:
    draw.text((5,330 + (index*45)), "・"+option, font = font_big, fill = "#000000")
    index += 1
kotaeawase = "0:00"
if utcnow.hour >= 14:
    kotaeawase = "12:00"
draw.text((60,520), "答え合わせは"+kotaeawase+"です！", font = font, fill = "#000000")
back.save("splatoonquiz.png")
tweettext =  "今日の"
if kotaeawase == "0:00":
    tweettext += "午後"
else:
    tweettext += "午前"
tweettext += "のスプラトゥーンクイズ！\n"
tweettext += QuizTypes[quiztype]+"\n"
tweettext += "答え合わせは"+kotaeawase+"です！"
tweettext += "回答は返信にある投票から！\n"
tweettext += "#スプラトゥーンクイズ"
if lastquizid is not None:
    tweettextanswer =  "このクイズの正解は...\n"
    tweettextanswer += lastquizanswer+"！\n"
    tweettextanswer += "みんなは正解できたかな？\n▼次のクイズはこちら！\n"
    #with open("splatoonquizanswer.png",mode="wb") as f:
    #    f.write(requests.get(lastquizanswerimg).content)
while True:
    utcnow = datetime.utcnow()
    if utcnow.hour == 15 or utcnow.hour == 3:
        medias = []
        medias.append(api.media_upload(filename="splatoonquiz.png").media_id)
        tweetid = client.create_tweet(text=tweettext, media_ids = medias).data["id"]
        #回答
        if lastquizid is not None:
            #medias = []
            #medias.append(api.media_upload(filename="splatoonquizanswer.png").media_id)
            tweettextanswer += "https://twitter.com/SplatoonSokuhou/status/"+tweetid
            client.create_tweet(text=tweettextanswer,in_reply_to_tweet_id=lastquizid)
        tweettext = "▼回答はこちら"
        tweetidquiz = client.create_tweet(text=tweettext,in_reply_to_tweet_id=tweetid,poll_duration_minutes=60*12,poll_options=Options).data["id"]
        statusdb.put({"tweetid":tweetidquiz,
                      "answer":answer,
                      "answerimg":answerimage},"lastquiz")
        break
