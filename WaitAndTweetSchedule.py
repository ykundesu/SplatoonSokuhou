import os
import tweepy
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import time
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
def GetTranslation(transtype, textid):
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
def GetSalmonData(jsonobj, mode):
    objs = []
    for sch in jsonobj["data"]["coopGroupingSchedule"][mode + "Schedules"]["nodes"]:
        obj = {}
        obj["start"] = datetime.strptime(sch.get("startTime"), '%Y-%m-%dT%H:%M:%SZ')
        obj["end"] = datetime.strptime(sch.get("endTime"), '%Y-%m-%dT%H:%M:%SZ')
        obj["stagename"] = sch.get("setting",{}).get("coopStage",{}).get("id","翻訳がありません")
        obj["stageimage"] = sch.get("setting",{}).get("coopStage",{}).get("image",{}).get("url","")
        obj["kingsalmonid"] = sch.get("__splatoon3ink_king_salmonid_guess")
        obj["weapons"] = []
        for weapon in sch.get("setting",{}).get("weapons",[]):
            obj["weapons"].append({
                "name":weapon.get("__splatoon3ink_id","翻訳がありませんでした"),
                "image":weapon.get("image",{}).get("url")
                })
        objs.append(obj)
    return objs
def CreateSalmonImage(jsons, text, text_x, IsBackPaste = True):
    back = Image.open("SplatoonBack_White.png").crop((0,0,960,625))
    img = Image.open("SplatoonBack_Black.png").crop((0,0,900,600))
    font = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 60)
    font_big = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 65)
    font_chu = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 45)
    font_mini = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 30)
    font_supermini = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 20)
    
    # 角丸にするためのマスクを作成
    mask = Image.new("L", img.size, 0)
    radius = 50
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, img.width, img.height), radius, fill=255)

    draw = ImageDraw.Draw(img)
    
    draw.text((text_x, 0), text, font = font, fill = "#FFFFFF")

    draw.text((120, 350), GetTranslation("stages", jsons["stagename"]), font = font, fill = "#FFFFFF")
    stage = Image.open(io.BytesIO(requests.get(jsons["stageimage"]).content))
    stage = stage.resize((int(stage.size[0] / 1.7),
                          int(stage.size[1] / 1.7)))
    img.paste(stage, (50, 80))
    
    if datetime.utcnow() > jsons["start"]:
        starttext = ""
    else:
        starttext = (jsons["start"] + datetime.timedelta(hours=9)).strftime('%Y年%m月%d日%H時')+"開始"
    draw.text((550, 80), starttext, font = font_mini, fill = "#FFFFFF")

    #オカシラシャケ
    draw.text((545, 130), "オカシラシャケ", font = font_big, fill = "#FFFFFF")
    draw.text((615, 200), GetSalmonoidName(jsons["kingsalmonid"]), font = font_chu, fill = "#FFFFFF")
    
    #武器
    index = 0
    for weapon in jsons["weapons"]:
        weaponimg = Image.open(io.BytesIO(requests.get(weapon["image"]).content))
        weaponimg = weaponimg.resize((int(weaponimg.size[0] / 2),
                              int(weaponimg.size[1] / 2)))
        additional = 50
        img.paste(weaponimg, (40 + additional + (index * 190), 425), weaponimg)
        weapontext = weapon["name"]
        if weapontext is not "6e17fbe20efecca9":
            weapontext = GetTranslation("weapons", weapontext)
        else:
            weapontext = ""
        draw.text((50 + additional + (index * 190), 550), weapontext, font = font_supermini, fill = "#FFFFFF")
        index += 1
    back.paste(img, (30,10), mask=mask)
    return back
def GetSalmonoidName(salmonid):
    if salmonid == "Cohozuna":
        return "ヨコズナ"
    elif salmonid == "Horrorboros":
        return "タツ"
    elif salmonid == None:
        return "翻訳がありませんでした"
    else:
        return salmonid
def CreateSchImage(jsons, text, text_x, IsBackPaste = True):
    back = Image.open("SplatoonBack_White.png").crop((0,0,800,920))
    img = Image.open("SplatoonBack_Black.png").crop((0,0,600,900))
    #img = make(img, 10, False)
    #Image.new("RGBA", (600, 900), (107, 107, 107))
    
    rx = 10
    ry = 20
    fillcolor = "#FFFFFF"

    font = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 55)

    # 角丸にするためのマスクを作成
    mask = Image.new("L", img.size, 0)
    radius = 50
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, img.width, img.height), radius, fill=255)

    draw = ImageDraw.Draw(img)
    draw.text((text_x, 0), text, font = font , fill = "#FFFFFF")
    
    page = Image.open(io.BytesIO(requests.get(jsons["stages"][0]["image"]).content))
    page = page.resize((int(page.width * 1.25), int(page.height * 1.25)))
    draw.text((160, 70), GetTranslation("rules", jsons["rule"]), font = font , fill = "#FFFFFF")
    img.paste(page, (50, 150))
    draw.text((120, 420), GetTranslation("stages", jsons["stages"][0]["name"]), font = font , fill = "#FFFFFF")

    page = Image.open(io.BytesIO(requests.get(jsons["stages"][1]["image"]).content))
    page = page.resize((int(page.width * 1.25), int(page.height * 1.25)))    
    img.paste(page, (50, 490))
    draw.text((120, 760), GetTranslation("stages", jsons["stages"][1]["name"]), font = font , fill = "#FFFFFF")
    
    del draw
    if IsBackPaste:
        back.paste(img, (105,10),mask=mask)
        img = back
    return img
IsTweeted = False
while True:
    utcnow = datetime.utcnow()
    if utcnow.hour % 2 == 0 and not IsTweeted:
        break
    if utcnow.minute >= 50 and not IsTweeted:        #ツイートする
        medias = []
        bankaradata = GetSchedulesData(schjson, "bankara")
        CreateSchImage(GetSchedulesData(schjson, "regular")[1]["settings"][0], "レギュラーマッチ", 120).save("regular.png")

        bankaraopen = CreateSchImage(bankaradata[1]["settings"][0], "バンカラマッチ(チャレンジ)", 33, False)
        bankarachallenge = CreateSchImage(bankaradata[1]["settings"][1], "バンカラマッチ(オープン)", 40, False)

        back = Image.open("SplatoonBack_White.png").crop((0,0,1450,920))
        back.paste(bankaraopen, (105,10))
        back.paste(bankarachallenge, (755,10))
        back.save("bankara.png")
        
        CreateSchImage(GetSchedulesData(schjson, "x")[1]["settings"][0], "Xマッチ", 200).save("xmatch.png")
        salmondata = GetSalmonData(schjson, "regular")
        medias.append(api.media_upload(filename="regular.png").media_id)
        medias.append(api.media_upload(filename="bankara.png").media_id)
        medias.append(api.media_upload(filename="xmatch.png").media_id)
        isbreak = True
        if ((salmondata[1]["start"] - datetime.utcnow()).total_seconds() <= 3600):
            CreateSalmonImage(salmondata[1],"サーモンラン", 300).save("salmon.png")
            medias.append(api.media_upload(filename="salmon.png").media_id)
            isbreak = False
        tweettext = "もうすぐでスケジュール更新！\n"
        hourtime = utcnow.hour + 1 + 9
        if hourtime >= 24:
            hourtime -= 24
        tweettext += str(hourtime) + "時からのスケジュールです！"
        client.create_tweet(text=tweettext, media_ids = medias)
        IsTweeted = True
        if isbreak:
            break
    elif IsTweeted and utcnow.hour % 2 == 0:
        time.sleep(30)
        schjson = requests.get("https://splatoon3.ink/data/schedules.json").json()
        salmondata = GetSalmonData(schjson, "regular")
        if salmondata[0]["end"] > datetime.utcnow():
            CreateSalmonImage(salmondata[-1],"サーモンラン", 300).save("salmonnew.png")
            medias = []
            medias.append(api.media_upload(filename="salmonnew.png").media_id)
            tweettext =  "新しいサーモンランのスケジュールが公開されました！\n"
            tweettext += "▼開始日時\n"
            tweettext += (jsons["start"] + datetime.timedelta(hours=9)).strftime('%Y年%m月%d日%H時')+"\n"
            client.create_tweet(text=tweettext, media_ids = medias)
            break
        time.sleep(30)
