import os
import tweepy
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import time
import pusher
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
        additional = 140
        img.paste(weaponimg, (40 + additional + (index * 140), 425), weaponimg)
        weapontext = weapon["name"]
        if weapontext is not "6e17fbe20efecca9":
            weapontext = GetTranslation("weapons", weapontext)
        else:
            weapontext = ""
        draw.text((50 + additional + (index * 140), 550), weapontext, font = font_supermini, fill = "#FFFFFF")
        index += 1
    back.paste(img, (30,10))
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
    draw.text((160, 70), GetTranslation("rules", jsons["rule"]), font = font , fill = "#FFFFFF")
    img.paste(page, (50, 150))
    draw.text((120, 420), GetTranslation("stages", jsons["stages"][0]["name"]), font = font , fill = "#FFFFFF")

    page = Image.open(io.BytesIO(requests.get(jsons["stages"][1]["image"]).content))
    page = page.resize((int(page.width * 1.25), int(page.height * 1.25)))    
    img.paste(page, (50, 490))
    draw.text((120, 760), GetTranslation("stages", jsons["stages"][1]["name"]), font = font , fill = "#FFFFFF")
    
    del draw
    if IsBackPaste:
        back.paste(img, (105,10))
        img = back
    return img
def createimage(targetgear):
            font = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 30)
            gearback = img.copy()
            gearbackdraw = ImageDraw.Draw(gearback)
            gearimg = Image.open(io.BytesIO(requests.get(targetgear["image"]).content))
            gearimg = gearimg.resize((int(gearimg.width / 2), int(gearimg.height / 2)))
            gearback.paste(gearimg, (52,2), gearimg)
            print("a:"+targetgear["mainpowerimg"])
            print("b:"+targetgear["brandimage"])
            brandimg = Image.open(io.BytesIO(requests.get(targetgear["brandimage"]).content))
            brandimg = brandimg.convert("RGBA")
            print(brandimg.mode)
            brandimg = brandimg.resize((int(brandimg.width / 2), int(brandimg.height / 2)))
            brandback = Image.new('RGBA', (brandimg.size[0], brandimg.size[1]), 'white')
            gearback.paste(brandback, (180,11))
            gearback.paste(brandimg, (180,11), brandimg)
            gearbackdraw.text((127,135),GetTranslation("gear",targetgear["name"]),font=font, fill = "#FFFFFF",anchor='mm')
            #メインパワー
            mainpower = Image.open(io.BytesIO(requests.get(targetgear["mainpowerimg"]).content))
            mainpower = mainpower.resize((int(mainpower.size[0] / 1.35),
                                          int(mainpower.size[1] / 1.45)))
            gearback.paste(mainpower,(25,150), mainpower)
            subindex = 0
            #サブパワー
            for addpower in targetgear["addpowers"]:
                addpowerimg = Image.open(io.BytesIO(requests.get(addpower["img"]).content))
                addpowerimg = addpowerimg.resize((int(addpowerimg.size[0] / 1.75),
                                              int(addpowerimg.size[1] / 1.75)))
                gearback.paste(addpowerimg,(85 + (subindex * 48),157), addpowerimg)
                subindex += 1
            gearbackdraw.text((107,210), str(targetgear["price"]), font=font, fill = "#FFFFFF")
            gearback.paste(gesocoin, (83, 220), gesocoin)
            return gearback
while True:
    utcnow = datetime.utcnow()
    if utcnow.hour > 1 and utcnow.hour < 23:
        break
    if utcnow.hour == 0:
        time.sleep(25)
        schjson = requests.get("https://splatoon3.ink/data/gear.json").json()
        gears = []
        for data in schjson["data"]["gesotown"]["pickupBrand"]["brandGears"]:
            gear = {}
            gear["price"] = int(data.get("price"))
            gear["end"] = datetime.strptime(data.get("saleEndTime"), '%Y-%m-%dT%H:%M:%SZ')
            gear["name"] = data.get("gear",{}).get("__splatoon3ink_id","名前なし")
            gear["mainpower"] = data.get("gear",{}).get("primaryGearPower",{}).get("__splatoon3ink_id","名前なし")
            gear["mainpowerimg"] = data.get("gear",{}).get("primaryGearPower",{}).get("image",{}).get("url")
            gear["addpowers"] = []
            for power in data["gear"]["additionalGearPowers"]:
                addpower = {}
                addpower["name"] = power.get("__splatoon3ink_id","名前なし")
                addpower["img"] = power.get("image",{}).get("url")
                gear["addpowers"].append(addpower)
            gear["image"] = data.get("gear",{}).get("image",{}).get("url","")
            gear["brandname"] = data.get("gear",{}).get("brand",{}).get("id","翻訳なし")
            gear["brandimage"] = data.get("gear",{}).get("brand",{}).get("image",{}).get("url","")
            gears.append(gear)
            
        font = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 120)
        font_mini = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 60)
        font_supermini = ImageFont.truetype("Corporate-Logo-Rounded-Bold-ver3.otf", 40)
    
        back = Image.open("SplatoonBack_White.png").crop((0,0,1300,800))
        img = Image.open("SplatoonBack_Black.png").crop((0,0,250,250))
        gesocoin = Image.open("GesoTownCoin.png")
        #gesocoin = gesocoin.resize((int(gesocoin.size[0] * 1.2),
        #                            int(gesocoin.size[1] * 1.2)))
        # 角丸にするためのマスクを作成
        mask = Image.new("L", img.size, 0)
        radius = 35
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.width, img.height), radius, fill=255)

        index = 0
        for targetgear in gears:
            if targetgear["name"] == "":
                continue
            gearback = createimage(targetgear)
            #if index < 3:
            back.paste(gearback, (250 + (index * 280),380), mask=mask)
            #else:
            #    back.paste(gearback, (595 + ((index - 3) * 290),350), mask=mask)
            index += 1
        backdraw = ImageDraw.Draw(back)
        #gearbacknew = createimage(gears[-1])
        #back.paste(gearbacknew, (100,250), mask=mask)
        backdraw.text((250,25),"本日のピックアップ",font=font, fill = "#000000")
        brandimage = Image.open(io.BytesIO(requests.get(schjson["data"]["gesotown"]["pickupBrand"]["brandGears"][0]["gear"]["brand"]["image"]["url"]).content)).convert("RGBA")
        brandimage = brandimage.resize((int(brandimage.size[0] * 1.5),
                                        int(brandimage.size[1] * 1.5)))
        back.paste(brandimage,(270,140), brandimage)
        
        brandimage = Image.open(io.BytesIO(requests.get(schjson["data"]["gesotown"]["pickupBrand"]["brand"]["usualGearPower"]["image"]["url"]).content)).convert("RGBA")
        brandimage = brandimage.resize((int(brandimage.size[0] * 1.5),
                                        int(brandimage.size[1] * 1.5)))
        back.paste(brandimage,(680,170), brandimage)

        brandimage = Image.open(io.BytesIO(requests.get(schjson["data"]["gesotown"]["pickupBrand"]["image"]["url"]).content))
        brandimage = brandimage.resize((int(brandimage.size[0] / 5),
                                        int(brandimage.size[1] / 5)))
        mask2 = Image.new("L", brandimage.size, 0)
        radius = 35
        draw2 = ImageDraw.Draw(mask2)
        draw2.rounded_rectangle((0, 0, brandimage.width, brandimage.height), radius, fill=255)

        back.paste(brandimage,(500,640),mask=mask2)
        
        backdraw.text((360,330),GetTranslation("brands",schjson["data"]["gesotown"]["pickupBrand"]["brand"]["id"]),font=font_mini, fill = "#000000",anchor='mm')
        backdraw.text((750,170),"つきやすいギアパワー",font=font_supermini, fill = "#000000",anchor='mm')
        backdraw.text((750,330),GetTranslation("powers",schjson["data"]["gesotown"]["pickupBrand"]["brand"]["usualGearPower"]["__splatoon3ink_id"]),font=font_mini, fill = "#000000",anchor='mm')
        back.save("pickupgear.png")
        medias = []
        medias.append(api.media_upload(filename="pickupgear.png").media_id)
        tweettext =  "ゲソタウンのピックアップが更新されました！\n"
        tweettext += "現在のピックアップはこちらです！\n"
        tweettext += "次回の更新は1日後です！"
        tweetid = client.create_tweet(text=tweettext, media_ids = medias).data["id"]
        try:
            payload = {"title":"ゲソタウン更新(ピックアップ)",
                       "url":"https://twitter.com/SplatoonSokuhou/status/"+str(tweetid),
                       "body":"ゲソタウンのピックアップが更新されました！"
                       }
            pusher.PushMsg("GesoUpdatePickup",payload)
        except Exception as e:
            print(str(e))
        break
