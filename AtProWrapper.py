from atproto import Client, models
from PIL import Image
from io import BytesIO
import os
currentclient = None
def getclient(client):
    if client == None:
        global currentclient
        if currentclient != None:
            client = currentclient
        else:
            client = Client()
            profile = client.login(os.environ.get('BSKY_ID', ""), os.environ.get('BSKY_APPPASS', ""))
            print(profile.displayName+'でログインしました')
            currentclient = client
    return client
def PostMessage(text, reply_to = None, imagedata = None, client=None):
    client = getclient(client)
    if reply_to != None:
        reply_to = models.AppBskyFeedPost.ReplyRef(reply_to, reply_to)
    if imagedata == None:
        return client.send_post(text=text, reply_to=reply_to)
    else:
        images = []
        index = 0
        for ib in imagedata:
            upload = client.com.atproto.repo.upload_blob(GetFileAndAssyuku(ib[0]))
            images.append(models.AppBskyEmbedImages.Image(alt=ib[1], image=upload.blob))
            index += 1
        return client.send_post(
            text,
            reply_to=reply_to,
            embed=models.AppBskyEmbedImages.Main(images=images),
        )
def Like(msg, client=None):
    client = getclient(client)
    return client.like(msg)
def GetFileAndAssyuku(name):
   with open(name, 'rb') as inputfile:
    # バイナリモードファイルをPILイメージで取得
    im = Image.open(inputfile)
    # JPEG形式に変換して、圧縮を実行
    im = im.convert('RGB')
    im_io = BytesIO()
    im.save(im_io, 'JPEG', quality = 80)
    return im_io.getvalue()
with open("Assyukuzumi.jpg",mode="wb") as f:
    f.write(GetFileAndAssyuku("salmon.png"))
#if __name__ == '__main__':
    #data = PostMessage("うぃっす")
