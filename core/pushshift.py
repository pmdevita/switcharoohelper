import requests
import urllib.parse


# Weird other way to get the data but it returns the edited version?
def get_comment_from_psaw(parent_id, comment_id):
    params = {'parent_id': f"t1_{parent_id}", "filter": "id,created_utc,edited,body"}
    # Come on PushShift, percent coding is a standard
    payload_str = urllib.parse.urlencode(params, safe=",")
    r = requests.get("https://api.pushshift.io/reddit/comment/search/",
                     params=payload_str)
    try:
        j = r.json()
    except Exception as e:
        print(r.status_code, r.text)
        raise e
    for i in j['data']:
        if i['id'] == comment_id:
            return i
    return None


def get_original_comment_from_psaw(comment_id):
    params = {'ids': comment_id, "filter": "id,created_utc,body"}
    # Come on PushShift, percent coding is a standard
    payload_str = urllib.parse.urlencode(params, safe=",")
    r = requests.get("https://api.pushshift.io/reddit/comment/search/",
                     params=payload_str)
    j = r.json()
    if j.get('data', None):
        if len(j['data']) > 0:
            return j['data'][0]
    return None

