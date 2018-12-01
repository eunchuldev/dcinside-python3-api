#!/usr/bin/python3
import time
import requests
import json
from requests.adapters import HTTPAdapter
import lxml.html
#import logging
#logging.basicConfig(level=logging.DEBUG)
GET_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36",
     }
ALTERNATIVE_GET_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36",
    }
XML_HTTP_REQ_HEADERS = {
    "Accept": "*/*",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "X-Requested-With": "XMLHttpRequest",
    }
POST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36",
    }

TIMEOUT = 3
def gen_session():
    sess = requests.Session()
    sess.mount("http://", HTTPAdapter(max_retries=100))
    sess.headers.update(GET_HEADERS)
    sess.head("http://m.dcinside.com")
    return sess
DEFAULT_SESS = gen_session()

def board(board_id, num=-1, start_page=1, skip_contents=False, doc_id_upper_limit=None, sess=DEFAULT_SESS):
    page = start_page
    while num:
        url = "http://m.dcinside.com/board/{}?page={}".format(board_id, page)
        res = sess.get(url, timeout=TIMEOUT)
        parsed = lxml.html.fromstring(res.text)
        doc_headers = (i[0] for i in parsed.xpath("//ul[@class='gall-detail-lst']/li") if not i.get("class", "").startswith("ad"))
        for doc in doc_headers:
            doc_id = doc[0].get("href").split("/")[-1].split("?")[0]
            if doc_id_upper_limit and int(doc_id_upper_limit) <= int(doc_id): continue
            contents, imgs, cmts = document(board_id, doc_id, sess=sess) if not skip_contents else (None, None, None)
            yield({
                "id": doc_id,
                "title": doc[0][0][1].text,
                "has_image": doc[0][0][0].get("class").endswith("img"),
                "author": doc[0][1][0].text,
                "time": doc[0][1][1].text,
                "view_num": int(doc[0][1][2].text.split()[-1]),
                "voteup_num": int(doc[0][1][3].text.split()[-1]),
                "comment_num": int(doc[1][0].text),
                "contents": contents,
                "images": imgs,
                "comments": cmts,
                })
            num-=1
            if num==0: break
        if not doc_headers: break
        else: page+=1

def document(board_id, doc_id, sess=DEFAULT_SESS):
    url = "http://m.dcinside.com/board/{}/{}".format(board_id, doc_id)
    res = sess.get(url, timeout=TIMEOUT)
    parsed = lxml.html.fromstring(res.text)
    doc_content_container = parsed.xpath("//div[@class='thum-txtin']")
    if len(doc_content_container):
        doc_content = parsed.xpath("//div[@class='thum-txtin']")[0]
        for adv in doc_content.xpath("div[@class='adv-groupin']"):
            adv.getparent().remove(adv)
        return '\n'.join(i.strip() for i in doc_content.itertext() if i.strip() and not i.strip().startswith("이미지 광고")), [i.get("src") for i in doc_content.xpath("//img") if not i.get("src","").startswith("https://nstatic")], comments(board_id, doc_id, sess=sess)
    else:
        # fail due to unusual tags in mobile version
        # at now, just skip it
        return "", [], []
    ''' !TODO: use an alternative(PC) protocol to fetch document
    else:
        url = "http://gall.dcinside.com/{}?no={}".format(board_id, doc_id)
        res = sess.get(url, timeout=TIMEOUT, headers=ALTERNATIVE_GET_HEADERS)
        parsed = lxml.html.fromstring(res.text)
        doc_content = parsed.xpath("//div[@class='thum-txtin']")[0]
        return '\n'.join(i.strip() for i in doc_content.itertext() if i.strip() and not i.strip().startswith("이미지 광고")), [i.get("src") for i in doc_content.xpath("//img") if not i.get("src","").startswith("https://nstatic")], comments(board_id, doc_id, sess=sess)
    '''

def comments(board_id, doc_id, sess=DEFAULT_SESS, num=-1, start_page=1):
    url = "http://m.dcinside.com/ajax/response-comment"
    for page in range(start_page, 999999):
        payload = {"id": board_id, "no": doc_id, "cpage": page, "managerskill":"", "del_scope": "1", "csort": ""}
        res = sess.post(url, headers=XML_HTTP_REQ_HEADERS, data=payload, timeout=TIMEOUT)
        parsed = lxml.html.fromstring(res.text)
        if not len(parsed[1].xpath("li")): break
        for li in reversed(parsed[1].xpath("li")):
            if not len(li[0]): continue
            yield({
                "id": li.get("no"),
                "parent_id": li.get("m_no"),
                "author": li[0].text + ("{}".format(li[0][0].text) if li[0][0].text else ""),
                "author_id": li[0][1].text if len(li[0]) > 1 else None,
                "contents": '\n'.join(i.strip() for i in li[1].itertext()),
                "dccon": li[1][0].get("src", None) if len(li[1]) and li[1][0].tag=="img" else None,
                "voice": li[1][0].get("src", None) if len(li[1]) and li[1][0].tag=="iframe" else None,
                "time": li[2].text, })
            num -= 1
            if num <= 0:
                return
        page_num_els = parsed.xpath("span[@class='pgnum']")
        if page_num_els:
            p = page_num_els[0].itertext()
            next(p)
            if page == next(p)[1:]: break
        else: break

def all_user_dccon(sess=DEFAULT_SESS):
    url = "http://m.dcinside.com/dccon/getDccon"
    res = sess.post(url, headers=XML_HTTP_REQ_HEADERS, timeout=TIMEOUT)
    parsed = lxml.html.fromstring(res.text)
    dccon_package_len = len(parsed.xpath("//ul[@class='dccon-top-slide swiper-wrapper']")[0])-1
    dccons = []
    for i in range(dccon_package_len):
        url = "http://m.dcinside.com/dccon/getDccon_tab"
        payload = {"idx": str(i+1)}
        res = sess.post(url, headers=XML_HTTP_REQ_HEADERS, data=payload, timeout=TIMEOUT)
        parsed = lxml.html.fromstring(res.text)
        dccons += [{"id": li[0].get("data-dccon-detail"), "pakage_id": li[0].get("data-dccon-package"), "src": li[0][0][0][0].get("src")} for ul in parsed[0] for li in ul]
    return dccons

def login(id, pw, sess=DEFAULT_SESS):
    con_key = __access("dc_login", "http://m.dcinside.com/auth/login?r_url=http://m.dcinside.com/")
    url = "https://dcid.dcinside.com/join/mobile_login_ok_new.php"
    header = POST_HEADERS
    header["Referer"] = "http://m.dcinside.com/"
    header["Host"] = "dcid.dcinside.com"
    header["Origin"] = "http://m.dcinside.com"
    payload = {
            "user_id": id,
            "user_pw": pw,
            "id_chk": "on",
            "con_key": con_key,
            "r_url": "http://m.dcinside.com/" }
    res = sess.post(url, headers=header, data=payload, timeout=TIMEOUT)
    return sess

def write_comment(board_id, doc_id, contents="", dccon_id="", dccon_src="", parent_comment_id="", name="", pw="", sess=DEFAULT_SESS):
    url = "http://m.dcinside.com/board/{}/{}".format(board_id, doc_id)
    res = sess.get(url, timeout=TIMEOUT)
    parsed = lxml.html.fromstring(res.text)
    hide_robot = parsed.xpath("//input[@class='hide-robot']")[0].get("name")
    csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
    con_key = __access("com_submit", url, require_conkey=False, sess=sess)
    header = XML_HTTP_REQ_HEADERS.copy()
    header["Referer"] = url
    header["Host"] = "m.dcinside.com"
    header["Origin"] = "http://m.dcinside.com"
    header["X-CSRF-TOKEN"] = csrf_token
    url = "http://m.dcinside.com/ajax/comment-write"
    payload = {
            "comment_memo": contents,
            "comment_nick": name,
            "comment_pw": pw,
            "mode": "com_write",
            "comment_no": parent_comment_id,
            "id": board_id,
            "no": doc_id,
            "best_chk": "",
            "subject": "12344",
            "board_id": "0",
            "reple_id":"",
            "cpage": "1",
            "con_key": con_key,
            hide_robot: "1",
            }
    if dccon_id: payload["detail_idx"] = dccon_id
    if dccon_src: payload["comment_memo"] = "<img src='{}'>".format(dccon_src)
    parsed = json.loads(sess.post(url, headers=header, data=payload, timeout=TIMEOUT).text)
    if "data" not in parsed:
        raise Exception("Error while writing comment: " + str(parsed))
    return str(parsed["data"])

def remove_document(board_id, doc_id, pw="", sess=DEFAULT_SESS):
    if not pw:
        url = "http://m.dcinside.com/board/{}/{}".format(board_id, doc_id)
        res = sess.get(url, timeout=TIMEOUT)
        parsed = lxml.html.fromstring(res.text)
        csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
        header = XML_HTTP_REQ_HEADERS.copy()
        header["Referer"] = url
        header["Host"] = "m.dcinside.com"
        header["Origin"] = "http://m.dcinside.com"
        header["X-CSRF-TOKEN"] = csrf_token
        con_key = __access("board_Del", url, require_conkey=False, sess=sess)
        url = "http://m.dcinside.com/del/board"
        payload = { "id": board_id, "no": doc_id, "con_key": con_key }
        res = sess.post(url, headers=header, data=payload, timeout=TIMEOUT)
        if res.text.find("true") < 0:
            raise Exception("Error while removing: " + res.text)
        return True
    url = "http://m.dcinside.com/confirmpw/{}/{}?mode=del".format(board_id, doc_id)
    referer = url
    res = sess.get(url, timeout=TIMEOUT)
    parsed = lxml.html.fromstring(res.text)
    token = parsed.xpath("//input[@name='_token']")[0].get("value", "")
    csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
    con_key = __access("board_Del", url, require_conkey=False, sess=sess)
    payload = {
            "_token": token,
            "board_pw": pw,
            "id": board_id,
            "no": doc_id,
            "mode": "del",
            "con_key": con_key,
            }
    header = XML_HTTP_REQ_HEADERS.copy()
    header["Referer"] = url
    header["Host"] = "m.dcinside.com"
    header["Origin"] = "http://m.dcinside.com"
    header["X-CSRF-TOKEN"] = csrf_token
    url = "http://m.dcinside.com/del/board"
    res = sess.post(url, headers=header, data=payload, timeout=TIMEOUT)
    if res.text.find("true") < 0:
        raise Exception("Error while removing: " + res.text)
    return True

def modify_document(board_id, doc_id, title="", contents="", name="", pw="", sess=DEFAULT_SESS):
    if not pw:
        url = "http://m.dcinside.com/write/{}/modify/{}".format(board_id, doc_id)
        res = sess.get(url)
        return __write_or_modify_document(board_id, title, contents, name, pw, sess, intermediate=res.text, intermediate_referer=url, doc_id=doc_id)
    url = "http://m.dcinside.com/confirmpw/{}/{}?mode=modify".format(board_id, doc_id)
    referer = url
    res = sess.get(url, timeout=TIMEOUT)
    parsed = lxml.html.fromstring(res.text)
    token = parsed.xpath("//input[@name='_token']")[0].get("value", "")
    csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
    con_key = __access("Modifypw", url, require_conkey=False, sess=sess)
    payload = {
            "_token": token,
            "board_pw": pw,
            "id": board_id,
            "no": doc_id,
            "mode": "modify",
            "con_key": con_key,
            }
    header = XML_HTTP_REQ_HEADERS.copy()
    header["Referer"] = referer
    header["Host"] = "m.dcinside.com"
    header["Origin"] = "http://m.dcinside.com"
    header["X-CSRF-TOKEN"] = csrf_token
    url = "http://m.dcinside.com/ajax/pwcheck-board"
    res = sess.post(url, headers=header, data=payload, timeout=TIMEOUT)
    if not res.text.strip():
        Exception("Error while modifing: maybe the password is incorrect")
    payload = {
            "board_pw": pw,
            "id": board_id,
            "no": doc_id,
            "_token": csrf_token
            }
    header = POST_HEADERS.copy()
    header["Referer"] = referer
    url = "http://m.dcinside.com/write/{}/modify/{}".format(board_id, doc_id)
    res = sess.post(url, headers=header, data=payload, timeout=TIMEOUT)
    return __write_or_modify_document(board_id, title, contents, name, pw, sess, intermediate=res.text, intermediate_referer=url, doc_id=doc_id)

def write_document(board_id, title="", contents="", name="", pw="", sess=DEFAULT_SESS):
    return __write_or_modify_document(board_id, title, contents, name, pw, sess)

def __write_or_modify_document(board_id, title="", contents="", name="", pw="", sess=DEFAULT_SESS, intermediate=None, intermediate_referer=None, doc_id=None):
    if not intermediate:
        url = "http://m.dcinside.com/write/{}".format(board_id)
        res = sess.get(url, timeout=TIMEOUT)
        parsed = lxml.html.fromstring(res.text)
    else:
        parsed = lxml.html.fromstring(intermediate)
        url = intermediate_referer
    rand_code = parsed.xpath("//input[@name='code']")
    rand_code = rand_code[0].get("value") if len(rand_code) else None
    user_id = parsed.xpath("//input[@name='user_id']")[0].get("value") if not name else None
    mobile_key = parsed.xpath("//input[@id='mobile_key']")[0].get("value")
    hide_robot = parsed.xpath("//input[@class='hide-robot']")[0].get("name")
    csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
    con_key = __access("dc_check2", url, require_conkey=False, sess=sess)
    header = XML_HTTP_REQ_HEADERS.copy()
    header["Referer"] = url
    header["Host"] = "m.dcinside.com"
    header["Origin"] = "http://m.dcinside.com"
    header["X-CSRF-TOKEN"] = csrf_token
    url = "http://m.dcinside.com/ajax/w_filter"
    payload = {
            "subject": title,
            "memo": contents,
            "id": board_id,
            }
    if rand_code:
        payload["code"] = rand_code
    res = json.loads(sess.post(url, headers=header, data=payload, timeout=TIMEOUT).text)
    if not res["result"]:
        raise Exception("Erorr while write document: " + str(res))
    url = "http://upload.dcinside.com/write_new.php"
    header["Host"] = "upload.dcinside.com"
    payload = {
            "subject": title,
            "memo": contents,
            hide_robot: "1",
            "GEY3JWF": hide_robot,
            "id": board_id,
            "contentOrder": "order_memo",
            "mode": "write",
            "Block_key": con_key,
            "bgm":"",
            "iData":"",
            "yData":"",
            "tmp":"",
            "mobile_key": mobile_key,
        }
    if rand_code:
        payload["code"] = rand_code
    if name:
        payload["name"] = name
        payload["password"] = pw
    else:
        payload["user_id"] = user_id
    if intermediate:
        payload["mode"] = "modify"
        payload["delcheck"] = ""
        payload["t_ch2"] = ""
        payload["no"] = doc_id
    res = sess.post(url, headers=header, data=payload, timeout=TIMEOUT).text
    doc_id = res[res.rfind("/")+1:-2]
    if doc_id.isdigit():
        return doc_id
    else:
        raise Exception(str(res))

def __access(token_verify, target_url, require_conkey=True, sess=DEFAULT_SESS):
    if require_conkey:
        res = sess.get(target_url, timeout=TIMEOUT)
        parsed = lxml.html.fromstring(res.text)
        con_key = parsed.xpath("//input[@id='con_key']")[0].get("value")
        payload = { "token_verify": token_verify, "con_key": con_key }
    else:
        payload = { "token_verify": token_verify, }
    url = "http://m.dcinside.com/ajax/access"
    res = sess.post(url, headers=XML_HTTP_REQ_HEADERS, data=payload, timeout=TIMEOUT)
    return json.loads(res.text)["Block_key"]

if __name__ == "__main__":
    board_id = "programming"
    '''
    for i in board(board_id, num=1, skip_contents=False):
        print(write_comment(board_id, i["id"], "아님", name="점진적자살", pw="1234"))
        print(write_comment(board_id, i["id"], "맞음", name="점진적자살", pw="1234"))
    '''
    #login("bot123", "1q2w3e4r!")
    #print(remove_document(board_id, "386"))
    print(write_document(board_id, "1234", "12345", name="123", pw="12345"))
    #sess = login(id, pw)
    #print(len(all_user_dccon(sess)))
    #write_comment(board_id, "939720", contents="123", dccon_id="", dccon_src="", parent_comment_id="", name="123", pw="1234")
    #for i in board(board_id, num=3, skip_contents=True):
    #doc_id    print(write_comment(board_id, i["id"], "아님", name="점진적자살", pw="1234"))
