import os
import tweepy
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
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
transjson = requests.get("https://splatoon3.ink/data/locale/ja-JP.json").json()
def GetTranlsation(transtype, textid):
    return transjson.get(transtype,{}).get(textid, {}).get("name","翻訳できませんでした。")
def GetSchedulesData(jsonobj, mode):
    objs = []
    for sch in jsonobj["data"][mode + "Schedules"]["nodes"]:
        obj = {}
        obj["start"] = datetime.strptime(sch.get("startTime"), '%Y-%m-%dT%H:%M:%SZ')
        obj["end"] = datetime.strptime(sch.get("endTime"), '%Y-%m-%dT%H:%M:%SZ')
        obj["settings"] = []

        if mode == "bankara":
            settings = sch.get(mode+"MatchSettings", [])
        else:
            settings = [sch.get(mode+"MatchSetting", {})]
        for setting in settings:
            settingobj = {}
            settingobj["rule"] = setting.get("vsRule", {}).get("id", "")
            stages = []
            for stage in setting.get("vsStages", []):
                stageobj = {}
                stageobj["name"] = stage.get("id")
                stageobj["image"] = stage.get("image", {}).get("url", "")
                stages.append(stageobj)
            settingobj["stages"] = stages
            obj["settings"].append(settingobj)
        objs.append(obj)
    return objs
schjson = requests.get("https://splatoon3.ink/data/schedules.json").json()

def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop((
        (img_width - crop_width) // 2,
        (img_height - crop_height) // 2,
        (img_width + crop_width) // 2,
        (img_height + crop_height) // 2
        ))

def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))

def make(pil_img, r=100, fil=True):
    mask = DrawBack(pil_img, r)
    if fil:
        mask = mask.filter(ImageFilter.SMOOTH)
    result = pil_img.copy()
    result.putalpha(mask)

    return result


def DrawBack(img, r=100):
    #角丸四角を描画する[3]を参考。というかほぼコピペ。
    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    rx = r
    ry = r
    fillcolor = "#ffffff"
    draw.rectangle((0,ry)+(mask.size[0]-1,mask.size[1]-1-ry), fill=fillcolor)
    draw.rectangle((rx,0)+(mask.size[0]-1-rx,mask.size[1]-1), fill=fillcolor)
    draw.pieslice((0,0)+(rx*2,ry*2), 180, 270, fill=fillcolor)
    draw.pieslice((0,mask.size[1]-1-ry*2)+(rx*2,mask.size[1]-1), 90, 180, fill=fillcolor)
    draw.pieslice((mask.size[0]-1-rx*2,mask.size[1]-1-ry*2)+
    (mask.size[0]-1,mask.size[1]-1), 0, 180, fill=fillcolor)
    draw.pieslice((mask.size[0]-1-rx*2,0)+
    (mask.size[0]-1,ry*2), 270, 360, fill=fillcolor)
    return mask

def CreateSchImage(jsons, text, text_x, IsBackPaste = True):
    back = Image.open("SplatoonBack_White.png").crop((0,0,800,920))
    img = Image.open("SplatoonBack_Black.png").crop((0,0,600,900))
    #img = make(img, 10, False)
    #Image.new("RGBA", (600, 900), (107, 107, 107))
    
    rx = 10
    ry = 20
    fillcolor = "#000000"

    font = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 60)

    mask = Image.new("L", img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle((0,ry)+(mask.size[0]-1,mask.size[1]-1-ry), fill=fillcolor)
    draw.rectangle((rx,0)+(mask.size[0]-1-rx,mask.size[1]-1), fill=fillcolor)
    draw.pieslice((0,0)+(rx*2,ry*2), 180, 270, fill=fillcolor)
    draw.pieslice((0,mask.size[1]-1-ry*2)+(rx*2,mask.size[1]-1), 90, 180, fill=fillcolor)
    draw.pieslice((mask.size[0]-1-rx*2,mask.size[1]-1-ry*2)+
                  (mask.size[0]-1,mask.size[1]-1), 0, 180, fill=fillcolor)
    draw.pieslice((mask.size[0]-1-rx*2,0)+
                 (mask.size[0]-1,ry*2), 270, 360, fill=fillcolor)
    
    im_2 = Image.new(mode=img.mode, size=img.size, color=(0,0,0,0))
    Image.composite(img, im_2, mask)
    
    draw = ImageDraw.Draw(img)
    draw.text((text_x, 0), text, font = font , fill = "#FFFFFF")
    
    page = Image.open(io.BytesIO(requests.get(jsons["stages"][0]["image"]).content))
    page = page.resize((int(page.width * 1.25), int(page.height * 1.25)))
    draw.text((160, 70), GetTranlsation("rules", jsons["rule"]), font = font , fill = "#FFFFFF")
    img.paste(page, (50, 150))
    draw.text((120, 420), GetTranlsation("stages", jsons["stages"][0]["name"]), font = font , fill = "#FFFFFF")

    page = Image.open(io.BytesIO(requests.get(jsons["stages"][1]["image"]).content))
    page = page.resize((int(page.width * 1.25), int(page.height * 1.25)))    
    img.paste(page, (50, 490))
    draw.text((120, 760), GetTranlsation("stages", jsons["stages"][1]["name"]), font = font , fill = "#FFFFFF")
    
    del draw
    if IsBackPaste:
        back.paste(img, (105,10))
        img = back
    return img
while True:
    utcnow = datetime.utcnow()
    if utcnow.hour % 2 == 0:
        break
    if utcnow.minute >= 50:        #ツイートする
        medias = []
        bankaradata = GetSchedulesData(schjson, "bankara")
        CreateSchImage(GetSchedulesData(schjson, "regular")[1]["settings"][0], "レギュラーマッチ", 120).save("regular.png")

        bankaraopen = CreateSchImage(bankaradata[1]["settings"][0], "バンカラマッチ(チャレンジ)", 10, False)
        bankarachallenge = CreateSchImage(bankaradata[1]["settings"][1], "バンカラマッチ(オープン)", 40, False)

        back = Image.open("SplatoonBack_White.png").crop((0,0,1450,920))
        back.paste(bankaraopen, (105,10))
        back.paste(bankarachallenge, (755,10))
        back.save("bankara.png")
        
        CreateSchImage(GetSchedulesData(schjson, "x")[1]["settings"][0], "Xマッチ", 200).save("xmatch.png")
        medias.append(api.media_upload(filename="regular.png").media_id)
        medias.append(api.media_upload(filename="bankara.png").media_id)
        medias.append(api.media_upload(filename="xmatch.png").media_id)
        tweettext = "もうすぐでスケジュール更新！\n"
        hourtime = utcnow.hour + 1 + 9
        if hourtime >= 24:
            hourtime -= 24
        tweettext += str(hourtime) + "時からのスケジュールです！"
        client.create_tweet(text=tweettext, media_ids = medias)
        break
