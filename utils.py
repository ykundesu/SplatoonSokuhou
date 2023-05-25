import requests
import os
import json
from bs4 import BeautifulSoup
import re
WEB_VIEW_VER_FALLBACK = "3.0.0-0742bda0" # fallback for current splatnet 3 ver
SPLATNET3_URL         = "https://api.lp1.av5ja.srv.nintendo.net"
USE_OLD_NSOAPP_VER    = False
GRAPHQL_URL = f'{SPLATNET3_URL}/api/graphql'
APP_USER_AGENT = 'Mozilla/5.0 (Linux; Android 11; Pixel 5) ' \
                 'AppleWebKit/537.36 (KHTML, like Gecko) ' \
                 'Chrome/94.0.4606.61 Mobile Safari/537.36'
NSOAPP_VERSION        = "unknown"
NSOAPP_VER_FALLBACK   = "2.5.0"
WEB_VIEW_VERSION      = "unknown"
session = requests.Session()
def get_nsoapp_version():
	'''Fetches the current Nintendo Switch Online app version from the Apple App Store and sets it globally.'''

	if USE_OLD_NSOAPP_VER:
		return NSOAPP_VER_FALLBACK

	global NSOAPP_VERSION
	if NSOAPP_VERSION != "unknown": # already set
		return NSOAPP_VERSION
	else:
		try:
			page = requests.get("https://apps.apple.com/us/app/nintendo-switch-online/id1234806557")
			soup = BeautifulSoup(page.text, 'html.parser')
			elt = soup.find("p", {"class": "whats-new__latest__version"})
			ver = elt.get_text().replace("Version ", "").strip()

			NSOAPP_VERSION = ver

			return NSOAPP_VERSION
		except: # error with web request
			return NSOAPP_VER_FALLBACK
#参考:https://github.com/frozenpandaman/s3s
def gen_graphql_body(sha256hash, varname=None, varvalue=None):
	'''Generates a JSON dictionary, specifying information to retrieve, to send with GraphQL requests.'''
	great_passage = {
		"extensions": {
			"persistedQuery": {
				"sha256Hash": sha256hash,
				"version": 1
			}
		},
		"variables": {}
	}

	if varname is not None and varvalue is not None:
		great_passage["variables"][varname] = varvalue

	return json.dumps(great_passage)
def headbutt(bullettoken,forcelang=None):
	'''Returns a (dynamic!) header used for GraphQL requests.'''

	if forcelang:
		lang    = forcelang
		country = forcelang[-2:]
	else:
		lang    = USER_LANG
		country = USER_COUNTRY
	graphql_head = {
		'Authorization':    f'Bearer {bullettoken}', # update every time it's called with current global var
		'Accept-Language':  lang,
		'User-Agent':       APP_USER_AGENT,
		'X-Web-View-Ver':   get_web_view_ver(),
		'Content-Type':     'application/json',
		'Accept':           '*/*',
		'Origin':           SPLATNET3_URL,
		'X-Requested-With': 'com.nintendo.znca',
		'Referer':          f'{SPLATNET3_URL}?lang={lang}&na_country={country}&na_lang={lang}',
		'Accept-Encoding':  'gzip, deflate'
	}
	return graphql_head
def get_web_view_ver(bhead=[], gtoken=""):
		'''Finds & parses the SplatNet 3 main.js file to fetch the current site version and sets it globally.'''
		app_head = {
			'Upgrade-Insecure-Requests':   '1',
			'Accept':                      '*/*',
			'DNT':                         '1',
			'X-AppColorScheme':            'DARK',
			'X-Requested-With':            'com.nintendo.znca',
			'Sec-Fetch-Site':              'none',
			'Sec-Fetch-Mode':              'navigate',
			'Sec-Fetch-User':              '?1',
			'Sec-Fetch-Dest':              'document'
		}
		app_cookies = {
			'_dnt':    '1'     # Do Not Track
		}

		if bhead:
			app_head["User-Agent"]      = bhead.get("User-Agent")
			app_head["Accept-Encoding"] = bhead.get("Accept-Encoding")
			app_head["Accept-Language"] = bhead.get("Accept-Language")
		if gtoken:
			app_cookies["_gtoken"] = gtoken # X-GameWebToken

		home = requests.get(SPLATNET3_URL, headers=app_head, cookies=app_cookies)
		if home.status_code != 200:
			return WEB_VIEW_VER_FALLBACK

		soup = BeautifulSoup(home.text, "html.parser")
		main_js = soup.select_one("script[src*='static']")

		if not main_js: # failed to parse html for main.js file
			return WEB_VIEW_VER_FALLBACK

		main_js_url = SPLATNET3_URL + main_js.attrs["src"]

		app_head = {
			'Accept':              '*/*',
			'X-Requested-With':    'com.nintendo.znca',
			'Sec-Fetch-Site':      'same-origin',
			'Sec-Fetch-Mode':      'no-cors',
			'Sec-Fetch-Dest':      'script',
			'Referer':             SPLATNET3_URL # sending w/o lang, na_country, na_lang params
		}
		if bhead:
			app_head["User-Agent"]      = bhead.get("User-Agent")
			app_head["Accept-Encoding"] = bhead.get("Accept-Encoding")
			app_head["Accept-Language"] = bhead.get("Accept-Language")

		main_js_body = requests.get(main_js_url, headers=app_head, cookies=app_cookies)
		if main_js_body.status_code != 200:
			return WEB_VIEW_VER_FALLBACK

		pattern = r"\b(?P<revision>[0-9a-f]{40})\b[\S]*?void 0[\S]*?\"revision_info_not_set\"\}`,.*?=`(?P<version>\d+\.\d+\.\d+)-"
		match = re.search(pattern, main_js_body.text)
		if match is None:
			return WEB_VIEW_VER_FALLBACK

		version, revision = match.group("version"), match.group("revision")
		ver_string = f"{version}-{revision[:8]}"

		return ver_string
def get_gtoken(f_gen_url, session_token, ver):
	'''Provided the session_token, returns a GameWebToken JWT and account info.'''

	nsoapp_version = get_nsoapp_version()

	global S3S_VERSION
	S3S_VERSION = ver

	app_head = {
		'Host':            'accounts.nintendo.com',
		'Accept-Encoding': 'gzip',
		'Content-Type':    'application/json',
		'Content-Length':  '436',
		'Accept':          'application/json',
		'Connection':      'Keep-Alive',
		'User-Agent':      'Dalvik/2.1.0 (Linux; U; Android 7.1.2)'
	}

	body = {
		'client_id':     '71b963c1b7b6d119',
		'session_token': session_token,
		'grant_type':    'urn:ietf:params:oauth:grant-type:jwt-bearer-session-token'
	}

	url = "https://accounts.nintendo.com/connect/1.0.0/api/token"
	r = requests.post(url, headers=app_head, json=body)
	id_response = json.loads(r.text)

	# get user info
	app_head = {
			'User-Agent':      'NASDKAPI; Android',
			'Content-Type':    'application/json',
			'Accept':          'application/json',
			'Authorization':   f'Bearer {id_response["access_token"]}',
			'Host':            'api.accounts.nintendo.com',
			'Connection':      'Keep-Alive',
			'Accept-Encoding': 'gzip'
		}
	url = "https://api.accounts.nintendo.com/2.0.0/users/me"
	r = requests.get(url, headers=app_head)
	user_info = json.loads(r.text)

	user_nickname = user_info["nickname"]
	user_lang     = user_info["language"]
	user_country  = user_info["country"]

	# get access token
	body = {}
	try:
		id_token = id_response["id_token"]
		f, uuid, timestamp = call_f_api(id_token, 1, f_gen_url)

		parameter = {
			'f':          f,
			'language':   user_lang,
			'naBirthday': user_info["birthday"],
			'naCountry':  user_country,
			'naIdToken':  id_token,
			'requestId':  uuid,
			'timestamp':  timestamp
		}
	except SystemExit:
		sys.exit(1)
	except:
		print("Error(s) from Nintendo:")
		print(json.dumps(id_response, indent=2))
		print(json.dumps(user_info, indent=2))
		sys.exit(1)
	body["parameter"] = parameter

	app_head = {
		'X-Platform':       'Android',
		'X-ProductVersion': nsoapp_version,
		'Content-Type':     'application/json; charset=utf-8',
		'Content-Length':   str(990 + len(f)),
		'Connection':       'Keep-Alive',
		'Accept-Encoding':  'gzip',
		'User-Agent':       f'com.nintendo.znca/{nsoapp_version}(Android/7.1.2)',
	}

	url = "https://api-lp1.znc.srv.nintendo.net/v3/Account/Login"
	r = requests.post(url, headers=app_head, json=body)
	splatoon_token = json.loads(r.text)

	try:
		id_token = splatoon_token["result"]["webApiServerCredential"]["accessToken"]
	except:
		# retry once if 9403/9599 error from nintendo
		try:
			f, uuid, timestamp = call_f_api(id_token, 1, f_gen_url)
			body["parameter"]["f"]         = f
			body["parameter"]["requestId"] = uuid
			body["parameter"]["timestamp"] = timestamp
			app_head["Content-Length"]     = str(990 + len(f))
			url = "https://api-lp1.znc.srv.nintendo.net/v3/Account/Login"
			r = requests.post(url, headers=app_head, json=body)
			splatoon_token = json.loads(r.text)
			id_token = splatoon_token["result"]["webApiServerCredential"]["accessToken"]
		except:
			print("Error from Nintendo (in Account/Login step):")
			print(json.dumps(splatoon_token, indent=2))
			print("Try re-running the script. Or, if the NSO app has recently been updated, you may temporarily change `USE_OLD_NSOAPP_VER` to True at the top of iksm.py for a workaround.")
			sys.exit(1)

		f, uuid, timestamp = call_f_api(id_token, 2, f_gen_url)

	# get web service token
	app_head = {
		'X-Platform':       'Android',
		'X-ProductVersion': nsoapp_version,
		'Authorization':    f'Bearer {id_token}',
		'Content-Type':     'application/json; charset=utf-8',
		'Content-Length':   '391',
		'Accept-Encoding':  'gzip',
		'User-Agent':       f'com.nintendo.znca/{nsoapp_version}(Android/7.1.2)'
	}

	body = {}
	parameter = {
		'f':                 f,
		'id':                4834290508791808,
		'registrationToken': id_token,
		'requestId':         uuid,
		'timestamp':         timestamp
	}
	body["parameter"] = parameter

	url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
	r = requests.post(url, headers=app_head, json=body)
	web_service_resp = json.loads(r.text)

	try:
		web_service_token = web_service_resp["result"]["accessToken"]
	except:
		# retry once if 9403/9599 error from nintendo
		try:
			f, uuid, timestamp = call_f_api(id_token, 2, f_gen_url)
			body["parameter"]["f"]         = f
			body["parameter"]["requestId"] = uuid
			body["parameter"]["timestamp"] = timestamp
			url = "https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken"
			r = requests.post(url, headers=app_head, json=body)
			web_service_resp = json.loads(r.text)
			web_service_token = web_service_resp["result"]["accessToken"]
		except:
			print("Error from Nintendo (in Game/GetWebServiceToken step):")
			print(json.dumps(web_service_resp, indent=2))
			sys.exit(1)

	return web_service_token, user_nickname, user_lang, user_country
def call_f_api(id_token, step, f_gen_url):
	'''Passes an naIdToken to the f generation API (default: imink) & fetches the response (f token, UUID, and timestamp).'''

	try:
		api_head = {
			'User-Agent':   f's3s/{S3S_VERSION}',
			'Content-Type': 'application/json; charset=utf-8'
		}
		api_body = {
			'token':       id_token,
			'hash_method':  step
		}
		api_response = requests.post(f_gen_url, data=json.dumps(api_body), headers=api_head)
		resp = api_response.json()

		f = resp["f"]
		uuid = resp["request_id"]
		timestamp = resp["timestamp"]
		return f, uuid, timestamp
	except:
		try: # if api_response never gets set
			if api_response.text:
				print(f"Error during f generation:\n{json.dumps(json.loads(api_response.text), indent=2, ensure_ascii=False)}")
			else:
				print(f"Error during f generation: Error {api_response.status_code}.")
		except:
			print(f"Couldn't connect to f generation API ({f_gen_url}). Please try again.")

		sys.exit(1)
def get_bullet(web_service_token, app_user_agent, user_lang, user_country):
	'''Given a gtoken, returns a bulletToken.'''

	app_head = {
		'Content-Length':   '0',
		'Content-Type':     'application/json',
		'Accept-Language':  user_lang,
		'User-Agent':       app_user_agent,
		'X-Web-View-Ver':   get_web_view_ver(),
		'X-NACOUNTRY':      user_country,
		'Accept':           '*/*',
		'Origin':           SPLATNET3_URL,
		'X-Requested-With': 'com.nintendo.znca'
	}
	app_cookies = {
		'_gtoken': web_service_token, # X-GameWebToken
		'_dnt':    '1'                # Do Not Track
	}
	url = f'{SPLATNET3_URL}/api/bullet_tokens'
	r = requests.post(url, headers=app_head, cookies=app_cookies)

	

	try:
		bullet_resp = json.loads(r.text)
		bullet_token = bullet_resp["bulletToken"]
	except (json.decoder.JSONDecodeError, TypeError):
		print("Got non-JSON response from Nintendo (in api/bullet_tokens step):")
		print(r.text)
		bullet_token = ""
	except:
		print("Error from Nintendo (in api/bullet_tokens step):")
		print(json.dumps(bullet_resp, indent=2))

	return bullet_token
def get_gandb(sessiontoken = None):
    if sessiontoken == None:
            sessiontoken = os.environ.get('SESSIONTOKEN', "")
    acc_lang = "en-US" # overwritten by user setting
    acc_country = "US"
    new_gtoken, acc_name, acc_lang, acc_country = get_gtoken("https://api.imink.app/f", sessiontoken, "0.4.0")
    new_bullettoken = get_bullet(new_gtoken, APP_USER_AGENT, acc_lang, acc_country)
    return new_gtoken, new_bullettoken
def GetWeapons(sessiontoken=None):
        GTOKEN,bullettoken = get_gandb(sessiontoken)
        data = requests.post(GRAPHQL_URL,
                  #ブキのやつ
                  data=gen_graphql_body("5f279779e7081f2d14ae1ddca0db2b6e"),
                  headers=headbutt(bullettoken,forcelang="ja-JP"),
                  cookies=dict(_gtoken=GTOKEN)).json()
        nodes = data["data"]["weaponRecords"]["nodes"]
        weapons = []
        for node in nodes:
                weapon = {}
                weapon["image2d"] = node["image2d"]["url"]
                weapon["image3d"] = node["image3d"]["url"]
                weapon["name"] = node["name"]
                weapon["id"] = node["weaponId"]
                weapon["weaponCategoryId"] = node["weaponCategory"]["weaponCategoryId"]
                special = {}
                special["image"] = node["specialWeapon"]["image"]["url"]
                special["name"] = node["specialWeapon"]["name"]
                special["id"] = node["specialWeapon"]["specialWeaponId"]
                weapon["specialWeapon"] = special
                sub = {}
                sub["image"] = node["subWeapon"]["image"]["url"]
                sub["name"] = node["subWeapon"]["name"]
                sub["id"] = node["subWeapon"]["subWeaponId"]
                weapon["subWeapon"] = sub
                weapons.append(weapon)
        return weapons
#for weapon in GetWeapons():
#        print(weapon["name"])
