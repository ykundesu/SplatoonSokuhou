import requests
import os
import threading
from deta import Deta
pusherdb = Deta(os.environ.get('SPSOKUHOU_DETA', "")).Base("SSPusher")
def Push(payload, endpoint,authcode,p256dh):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = '''{"subscription":
{"endpoint":"{endpoint}",
"expirationTime":null,
"keys":
{"auth":"{auth}",
"p256dh":"{p256dh}"
}
},"payload":{
 "title":"{title}",
 "body":"{body}",
 "data":{"url":"{url}"}
 }
}'''
    #data = '{"subscription":{"endpoint":"'+endpoint+'","expirationTime":null,"keys": {"auth":"'+authcode+'","p256dh":"'+p256dh+'"}},"payload":{"title":"'+payload.get("title","[テストTitle]")+'","body":"'+payload.get("body","[テストBody]")+'","data": {"url": "{0}",}}}'
    data = data.replace("{endpoint}",endpoint).replace("{auth}",authcode).replace("{p256dh}",p256dh).replace("{title}",payload.get("title","[titleテスト]"))
    data = data.replace("{body}",payload.get("body","[bodyテスト]")).replace("{url}",payload.get("url","[urlテスト]"))
    data = data.encode()
    #print(data1)
    #print()
    #print(data)
    #print('\n'.join(difflib.ndiff(data1.split(), data.split())))

    response = requests.post('https://web-push-server-ue7f.vercel.app/api/send', headers=headers, data=data)
def PushMsg(typename, payload):
    #print("おけ")
    res = pusherdb.fetch({"types?contains":typename})
    all_items = res.items
    while res.last:
        res = pusherdb.fetch(last=res.last)
        all_items += res.items
    threads = []
    for item in all_items:
        #print("プッシュ:"+item.get("key","")+":"+item.get("authcode","")+":"+item.get("p256dh",""))
        thread = threading.Thread(target=Push,args=(payload,
             item.get("endpoint",""),
             item.get("key",""),
             item.get("p256dh","")))
        thread.start()
        threads.append(thread)
    for threa in threads:
        threa.join()
#payload = {"title":"どう？",
#           "url":"https://twitter.com/SplatoonSokuhou/status/1663817736844201984",
#           "body":"うえーい"}
#PushMsg("ChangeSchedule",payload)
