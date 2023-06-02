import requests
import re
import os
import tweepy
import bs4
import time
from deta import Deta
from datetime import datetime
import sys
import pusher
statusdb = Deta(os.environ.get('SPSOKUHOU_DETA', "")).Base("SSStatus")
ver_saisin = statusdb.get("Version")
print("現在のバージョンは"+ver_saisin["value"]+"です。")
splatoonurl = "https://www.nintendo.co.jp/support/switch/software_support/av5ja/"
print(requests.get(splatoonurl).text)
KAKUTEIVERSION = "401"
if KAKUTEIVERSION in ver_saisin["value"]:
    VERSION_KAKUTEI = False
else:
    #バージョンが確定しているか(例えばシーズン変更時など)
    VERSION_KAKUTEI = True
if not VERSION_KAKUTEI:
    while True:
        print("アクセス中...")
        targeturl = re.search("URL=(.*?).html", requests.get("https://www.nintendo.co.jp/support/switch/software_support/av5ja/").text).group(0).replace("URL=","")
        print("アクセスしました。urlは"+targeturl+"でした。")
        if targeturl != ver_saisin["value"]:
            print("最新バージョンがあったので、処理を行います。")
            response = requests.get(splatoonurl + targeturl)
            break
        print("最新バージョンがなかったので、待機を行います。")
        utcnow = datetime.utcnow()
        if utcnow.hour > 1 and utcnow.hour < 22:
            print("終了時間だったので終了")
            sys.exit()
        elif utcnow.hour == 22 or utcnow.minute > 20:
            continue
        time.sleep(30)
else:
    while True:
        print("アクセス中...")
        response = requests.get("https://www.nintendo.co.jp/support/switch/software_support/av5ja/"+KAKUTEIVERSION+".html")
        if response.status_code == 404:
            print("最新バージョンがなかったので、待機を行います。")
        else:
            print("最新バージョンがあったので、処理を行います。")
            break
        utcnow = datetime.utcnow()
        if utcnow.hour > 1 and utcnow.hour < 22:
            print("確定：終了時間だったので終了")
            sys.exit()
        elif utcnow.hour == 22 or utcnow.minute > 20:
            continue
        if utcnow.hour == 23:
            time.sleep(30)
        else:
            time.sleep(10)
#print(splatoonurl + targeturl)
response.encoding = "utf-8"
reversion = re.search("Ver. (.*?) ",response.text).group(0)
version = reversion.replace("Ver. ", "").replace(" ","")
reupdateday = re.search("［(.*?)］",response.text).group(0)
updateday = reupdateday.replace("［","").replace("］","")
#print(response.text)
tweetid = None
print(requests.get(splatoonurl).text)
#secretsで設定した値をとる
CONSUMER_KEY = os.environ.get('CONSUMER_KEY', "")
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET', "")
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN', "")
ACCESS_SECRET = os.environ.get('ACCESS_SECRET', "")
#print(os.environ)
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
tweetcount = 20
def tweet(text, IsTweetCount = True, in_reply_to_tweet_id = None):
    global tweetcount
    if IsTweetCount:
        tweetcount -= 1
    result = "0"
    result = client.create_tweet(text=text, in_reply_to_tweet_id=in_reply_to_tweet_id).data["id"]
    #print(text)
    print("ツイートしました。残りツイート可能数:"+str(tweetcount))
    return result

tweettext =  "スプラトゥーンの更新データが発表されました。\n"
tweettext += "▼バージョン\n"
tweettext += version + "\n"
if len(tweettext) > 140:
    print("バージョン長すぎ！")
elif len(tweettext) + len("▼更新日\n") > 140:
    tweetid = tweet(tweettext,in_reply_to_tweet_id=tweetid)
    tweettext = ""
tweettext += "▼更新日\n"
tweettext += updateday + "\n"
if len(tweettext) + len("詳細は公式サイトやこのツイートの返信などをご覧ください。\n") > 140:
    tweetid = tweet(tweettext,in_reply_to_tweet_id=tweetid)
    tweettext = ""
tweettext += "詳細は公式サイトやこのツイートの返信などをご覧ください。\n"
if len(tweettext) * 2 + len(response.url) > 280:
    tweetid = tweet(tweettext,in_reply_to_tweet_id=tweetid)
    tweettext = ""
tweettext += response.url
tweetid = tweet(tweettext,in_reply_to_tweet_id=tweetid)
try:
    payload = {"title":"更新データ発表",
           "url":"https://twitter.com/SplatoonSokuhou/status/"+str(tweetid),
           "body":"スプラトゥーンの更新データ「"+version+"」が発表されました。"}
    pusher.PushMsg("Update",payload)
except Exception as e:
    print(str(e))
#リプライ
idx = response.text.find("<!-- 更新データ内容 -->")
idx2 = response.text.find("<!-- /更新データ内容 -->")
targettext = response.text[idx:idx2] + "<!-- /更新データ内容 -->"
html = bs4.BeautifulSoup(targettext, 'html.parser')
h3items = html.find_all("h3")
items = {}
index = 0
bugcount = 0
parenth3 = None
textitems = None
for item in targettext.split("\n"):
    if "<h3" in item:
        if textitems != None:
            items[parenth3] = textitems
        textitems = ""
        parenth3 = item
    elif parenth3 != None:
        textitems += item + "\n"
if textitems != None:
    items[parenth3] = textitems   
parenth3 = None  
#print(items)
ChangeAbility = {}
SpecialPointUpdates = {}
for item in items.items():
    itemname = bs4.BeautifulSoup(item[0], 'html.parser').find("h3").get_text()
    print("")
    print(itemname)
    print("")
    for item in bs4.BeautifulSoup(item[1], 'html.parser').find_all("li"):
        itemtext = item.get_text()
        if itemname.endswith("問題の修正"):
            bugcount += 1
        elif itemtext.endswith("問題を修正しました。"):
            bugcount += 1
        elif itemtext.startswith("一部の") and itemtext.endswith("の性能を変更しました。"):
            targetitemtext = itemtext.replace("一部の","").replace("の性能を変更しました。","")
            ChangeAbility[targetitemtext] = []
            parenth3 = None
            textitems = None
            for item3 in targettext.split("\n"):
                if itemtext in item3:
                    textitems = ""
                    parenth3 = item
                elif parenth3 != None:
                    if "<li " in item3:
                        break
                    textitems += item3 + "\n"
            for trobj in bs4.BeautifulSoup(textitems, 'html.parser').find_all("tr"):
                tdobj = trobj.find("td")
                if tdobj != None:
                    tobjtext = tdobj.get_text("\n")
                    print(tobjtext.split("\n"))
                    tobjtextold = tobjtext.split("\n")
                    tobjtext = None
                    for tobjnew in tobjtextold:
                        if tobjnew != "":
                            if tobjtext != None:
                                tobjtext += "&" + tobjnew
                            else:
                                tobjtext = tobjnew
                    ChangeAbility[targetitemtext].append(tobjtext.replace("\n",""))
        elif itemtext == "一部のブキのスペシャル必要ポイントを変更しました。":
            parenth3 = None
            textitems = None
            for item3 in targettext.split("\n"):
                if itemtext in item3:
                    textitems = ""
                    parenth3 = item
                elif parenth3 != None:
                    if "<li " in item3:
                        break
                    textitems += item3 + "\n"
            for trobj in bs4.BeautifulSoup(textitems, 'html.parser').find_all("tr")[1:]:
                trobjs = trobj.find_all("td")
                SpecialPointUpdates[trobjs[0].get_text()] = [trobjs[1].get_text(), trobjs[2].get_text()]
                print("　"+trobj.find_all("td")[1].get_text()+"p=>"+trobj.find_all("td")[2].get_text()+"p")
    index += 1
print(ChangeAbility)
tweettext = "▼アップデートの項目▼\n"
for item in items.keys():
    itemname = bs4.BeautifulSoup(item, 'html.parser').find("h3").get_text()
    if (len(tweettext) + len("・") + len(itemname) + len("\n")) > 140:
        if tweetcount > 0:
            tweetid = tweet(text=tweettext, in_reply_to_tweet_id=tweetid)
        tweettext = ""
    tweettext += "・" + itemname + "\n"
if len(tweettext) > 0:
    if tweetcount > 0:
        tweetid = tweet(text=tweettext, in_reply_to_tweet_id=tweetid)
tweettext = ""
#ウェポンとかの変更
for ability in ChangeAbility.items():
    tweettext += "▼"+ability[0]+"の調整対象▼\n"
    for changeab in ability[1]:
        if (len(tweettext) + len("・") + len(changeab) + len("\n")) > 140:
            if tweetcount > 0:
                tweetid = tweet(text=tweettext, in_reply_to_tweet_id=tweetid)
            tweettext = ""
        tweettext += "・" + changeab + "\n"
if len(tweettext) > 0:
    if tweetcount > 0:
        tweetid = tweet(text=tweettext, in_reply_to_tweet_id=tweetid)
tweettext = ""
if len(SpecialPointUpdates) > 0:
    tweettext = "▼スペシャルポイント変更▼\n"
    for spu in SpecialPointUpdates.items():
        newtext = "・" + spu[0] + "\n　"+spu[1][0]+"p=>"+spu[1][1]+"p\n"
        if (len(tweettext) + len(newtext)) > 140:
            if tweetcount > 0:
                tweetid = tweet(text=tweettext, in_reply_to_tweet_id=tweetid)
            tweettext = ""
        tweettext += newtext
newtext = "▼アップデート情報▼\n"
newtext += "バグ修正数："+str(bugcount)
print(str(len(tweettext) + len(newtext)))
#print(newtext)
if len(tweettext) + len(newtext) > 140:
    if tweetcount > 0:
        tweetid = tweet(text=tweettext, in_reply_to_tweet_id=tweetid)
    if tweetcount > 0:
        tweettext = newtext
        tweetid = tweet(text=tweettext, in_reply_to_tweet_id=tweetid)
else:
    tweettext += newtext
    if tweetcount > 0:
        tweetid = tweet(text=tweettext, in_reply_to_tweet_id=tweetid)
print("バグ数:"+str(bugcount))
#tweetid = client.create_tweet(text=tweettext, in_reply_to_tweet_id=tweetid).data["id"]
statusdb = Deta(os.environ.get('SPSOKUHOU_DETA', "")).Base("SSStatus")
if VERSION_KAKUTEI:
    statusdb.put("./"+KAKUTEIVERSION+".html","Version")
else:
    statusdb.put(targeturl,"Version")
