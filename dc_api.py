#!/usr/bin/python3
import requests
import json
from requests.adapters import HTTPAdapter
import lxml.html
#import logging
#logging.basicConfig(level=logging.DEBUG)
GET_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36",
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
    "X-Requested-With": "XMLHttpRequest"
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

def raw_parse(text, start, end, offset=0):
    s = text.find(start, offset)
    if s == -1: return None, 0
    s += len(start)
    e = text.find(end, s)
    if e == -1: return None, 0
    return text[s:e], e

def gen_session():
    sess = requests.Session()
    sess.mount("http://", HTTPAdapter(max_retries=5))
    sess.headers.update(GET_HEADERS)
    sess.head("http://m.dcinside.com")
    return sess
default_sess = gen_session()

def board(board_id, num=-1, start_page=1, skip_contents=False, sess=default_sess):
    page = start_page
    while num:
        url = "http://m.dcinside.com/board/{}?page={}".format(board_id, page)
        res = sess.get(url)
        parsed = lxml.html.fromstring(res.text)
        doc_headers = (i[0] for i in parsed.xpath("//ul[@class='gall-detail-lst']/li") if not i.get("class", "").startswith("ad"))
        for doc in doc_headers:
            #if a.tag != 'a': continue
            doc_id = doc[0].get("href").split("/")[-1].split("?")[0]
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

def document(board_id, doc_id, sess=default_sess):
    url = "http://m.dcinside.com/board/{}/{}".format(board_id, doc_id)
    res = sess.get(url)
    parsed = lxml.html.fromstring(res.text)
    doc_content = parsed.xpath("//div[@class='thum-txtin']")[0]
    #csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
    return '\n'.join(i.strip() for i in doc_content.itertext() if i.strip() and not i.strip().startswith("이미지 광고")), [i.get("src") for i in doc_content.xpath("//img") if not i.get("src","").startswith("https://nstatic")], comments(board_id, doc_id, sess=sess)

def comments(board_id, doc_id, sess=default_sess, start_page=1):
    url = "http://m.dcinside.com/ajax/response-comment"
    #header["X-CSRF-TOKEN"] = csrf_token
    for page in range(start_page, 999999):
        payload = {"id": board_id, "no": doc_id, "cpage": page, "managerskill":"", "del_scope": "1", "csort": ""}
        res = sess.post(url, headers=XML_HTTP_REQ_HEADERS, data=payload)
        parsed = lxml.html.fromstring(res.text)
        if not len(parsed[1].xpath("li")): break
        for li in parsed[1].xpath("li"):
            if not len(li[0]): continue
            yield({
                "id": li.get("no"),
                "parent_id": li.get("m_no"),
                "author": li[0].text + ("({})".format(li[0][0].text) if li[0][0].text else ""),
                "author_id": li[0][1].text if len(li[0]) > 1 else None,
                "contents": '\n'.join(i.strip() for i in li[1].itertext()),
                "dccon": li[1][0].get("src", None) if len(li[1]) else None,
                "time": li[2].text, })
        page_num_els = parsed.xpath("span[@class='pgnum']")
        if page_num_els:
            p = page_num_els[0].itertext()
            next(p)
            if page == next(p)[1:]: break
        else: break

def all_user_dccon(sess=default_sess):
    #header["X-CSRF-TOKEN"] = csrf_token
    url = "http://m.dcinside.com/dccon/getDccon"
    res = sess.post(url, headers=XML_HTTP_REQ_HEADERS)
    parsed = lxml.html.fromstring(res.text)
    dccon_package_len = len(parsed.xpath("//ul[@class='dccon-top-slide swiper-wrapper']")[0])-1
    print(lxml.html.tostring(parsed.xpath("//ul[@class='dccon-top-slide swiper-wrapper']")[0]))
    print(dccon_package_len)
    dccons = []
    for i in range(dccon_package_len):
        url = "http://m.dcinside.com/dccon/getDccon_tab"
        payload = {"idx": str(i+1)}
        res = sess.post(url, headers=XML_HTTP_REQ_HEADERS, data=payload)
        parsed = lxml.html.fromstring(res.text)
        dccons += [{"id": li[0].get("data-dccon-detail"), "pakage_id": li[0].get("data-dccon-package"), "src": li[0][0][0][0].get("src")} for li in parsed[0][0]]
    return dccons

def login(id, pw, sess=default_sess):
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
    res = sess.post(url, headers=header, data=payload)
    return sess

def write_comment(board_id, doc_id, contents, dccon_id="", parent_comment_id="", name="", pw="", sess=default_sess):
    url = "http://m.dcinside.com/board/{}/{}".format(board_id, doc_id)
    res = sess.get(url)
    parsed = lxml.html.fromstring(res.text)
    csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
    con_key = __access("com_submit", url, require_conkey=False, sess=sess)
    header = XML_HTTP_REQ_HEADERS
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
            }
    if dccon_id: payload["detail_idx"] = dccon_id
    return str(json.loads(sess.post(url, headers=header, data=payload).text)["data"])

def __access(token_verify, target_url, require_conkey=True, sess=default_sess):
    if require_conkey:
        res = sess.get(target_url)
        parsed = lxml.html.fromstring(res.text)
        con_key = parsed.xpath("//input[@id='con_key']")[0].get("value")
        payload = { "token_verify": token_verify, "con_key": con_key }
    else:
        payload = { "token_verify": token_verify, }
    url = "http://m.dcinside.com/ajax/access"
    res = sess.post(url, headers=XML_HTTP_REQ_HEADERS, data=payload)
    return json.loads(res.text)["Block_key"]

if __name__ == "__main__":
    board_id = "programming"
    for i in board(board_id, num=1, skip_contents=False):
        print(write_comment(board_id, i["id"], "아님", name="점진적자살", pw="1234"))
        print(write_comment(board_id, i["id"], "맞음", name="점진적자살", pw="1234"))
    #login("bot123", "1q2w3e4r!")
    #board_id = "alphago"
    #id = "bot123"
    #pw = "1q2w3e4r!"
    #sess = login(id, pw)
    #print(len(all_user_dccon(sess)))
    #print(write_comment(board_id, "376", "<img src='http://dcimg5.dcinside.com/dccon.php?no=62b5df2be09d3ca567b1c5bc12d46b394aa3b1058c6e4d0ca41648b65fe8206ea7f3b92660bc5d5215423e4ed144a30f6db46e312096e3e93e8603794b756245d3bd55f11fce86'>", dccon_id="153097480"))
    #for i in board(board_id, num=3, skip_contents=True):
    #    print(write_comment(board_id, i["id"], "아님", name="점진적자살", pw="1234"))

