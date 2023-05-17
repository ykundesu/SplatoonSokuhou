import requests
import re
weapons = requests.get("https://api.koukun.jp/splatoon/3/weapon/").json()["data"]
newtext = ""
with open("SalmonWeapons.json",mode="r",encoding="utf-8") as f:
    newtext = f.read()
for weapon in weapons:
    print("ーーー"+weapon["name"]+"ーーー")
    if input("IS(なにか入力されてたらパス):") is not "":
        continue
    newtext += weapon["name"]+","
    weapondata = requests.get("https://wikiwiki.jp/splatoon3mix/ブキ/"+weapon["name"]).text
    #print(weapondata)
    #ブキ重量
    weaponweighttext = re.search(r"ブキ重量</span></th><td style=\"text-align:center;\">(.*?)<", weapondata).group(0).replace("ブキ重量</span></th><td style=\"text-align:center;\">","").replace("<","")
    if weaponweighttext == "最軽":
        weaponweight = "0"
    elif weaponweighttext == "軽":
        weaponweight = "1"
    elif weaponweighttext == "中":
        weaponweight = "2"
    elif weaponweighttext == "重":
        weaponweight = "3"
    else:
        print("重さが取得できなかった")
    newtext += weaponweight + ","
    #射程
    weaponrangetext = re.search(r"有効射程</th><td style=\"text-align:center;\">(.*?)</td><th style=\"text-align:center;\">", weapondata).group(0).replace("有効射程</th><td style=\"text-align:center;\">","").replace("</td><th style=\"text-align:center;\">","")
    newtext += weaponrangetext + ","
    weapondps = re.search(r"DPS</th><td style=\"text-align:center;\">(.*?)/秒</td></tr>", weapondata).group(0).replace("DPS</th><td style=\"text-align:center;\">","").replace("/秒</td></tr>","")
    newtext += weapondps + ","
    #インク効率
    weaponpointtext = re.search(r"インク効率（塗り）</th><td style=\"text-align:center;\">(.*?)p<", weapondata).group(0).replace("インク効率（塗り）</th><td style=\"text-align:center;\">","").replace("p<","")
    newtext += weaponpointtext + ","
    #役割
    yakuwari = input("役割(0:ザコ処理,1:オオモノ処理,2:塗り,3:金イクラ納品,4:すべて):")
    newtext += yakuwari + ","
    kidouryoku = input("機動力(0:低,1:中,2:高):")
    newtext += kidouryoku + ","
    oomono_tokui = input("得意なオオモノ(00:テッキュウ,01:カタパ,02:タワー,03:コウモリ,04:ヘビ,05:ハシラ\n06:バクダン,07:モグラ,08:ナベブタ,09:テッパン,10:ダイバー):")
    newtext += oomono_tokui + ","
    oomono_nigate = input("苦手なオオモノ(00:テッキュウ,01:カタパ,02:タワー,03:コウモリ,04:ヘビ,05:ハシラ\n06:バクダン,07:モグラ,08:ナベブタ,09:テッパン,10:ダイバー):")
    newtext += oomono_nigate + ","
    map_tokui = input("得意なマップ(0:アラマキ,1:ム二エール,2:シェケナダム,3:ドンブラコ):")
    newtext += map_tokui + ","
    map_nigate = input("苦手なマップ(0:アラマキ,1:ム二エール,2:シェケナダム,3:ドンブラコ):")
    newtext += map_nigate + ","
    specialwave_tokui = input("得意なウェーブ(0:ヒカリバエ,1:霧,2:グリル,3:ドスコイ大量発生)")
    newtext += specialwave_tokui + ","
    specialwave_nigate = input("苦手なウェーブ(0:ヒカリバエ,1:霧,2:グリル,3:ドスコイ大量発生)")
    newtext += specialwave_nigate + ","
    newtext += "\n"
    with open("SalmonWeapons.json",mode="w",encoding="utf-8") as f:
        f.write(newtext)
