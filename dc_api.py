#!/usr/bin/python3
import requests


GET_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36",
    "Upgrade-Insecure-Requests": "1",
    "Host": "m.dcinside.com",
    "Connection": "keep-alive",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
    }

POST_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Host": "m.dcinside.com",
    "Origin": "http://m.dcinside.com",
    "Referer": "http://m.dcinside.com/write.php?id=alphago&mode=write",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    }

def _post(sess, url, data=None, json=None, **kwargs):
    res = None
    while not res:
        try:
            res = sess.post(url, data=data, json=json, **kwargs)
        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.TooManyRedirects:
            pass
        except Exception as e:
            print(e)
            pass
    return res

def _get(sess, url, **kwargs):
    res = None
    while not res:
        try:
            res = sess.get(url, **kwargs)
        except requests.exceptions.Timeout:
            pass
        except requests.exceptions.TooManyRedirects:
            pass
        except Exception as e:
            print(e)
            pass
    return res

def createSession():
    return requests.session()

def upvote(board, is_miner, doc_no, num=1, sess=None):
    if num>1:
        try:
            import vpn
        except:
            return None
        def f():
            f.n += upvote(board, is_miner, doc_no)
        f.n = 0
        vpn.do(f, num)
        return f.n
    else:
        if sess is None:
            sess = requests.session()
        url = "http://m.dcinside.com/view.php?id=%s&no=%s" % (board, doc_no)
        res = _get(sess, url, headers=GET_HEADERS, timeout=3)
        _, s = raw_parse(res.text, "function join_recommend()", "{")
        _, e = raw_parse(res.text, "$.ajax", "{", s)
        cookie_name, _ = raw_parse(res.text, 'setCookie_hk_hour("', '"', s)
        sess.cookies[cookie_name] = "done"
        data = {}
        while s < e:
            nv, s = raw_parse(res.text, '= "', '"', s)
            if s >= e: break
            nv= nv.split("=")
            data[nv[0] if nv[0][0] != "&" else nv[0][1:]] = nv[1] or "undefined"
        headers = POST_HEADERS.copy()
        headers["Referer"] = url
        headers["Accept-Language"] = "en-US,en;q=0.9"
        url = "http://m.dcinside.com/_recommend_join.php"
        res = _post(sess, url, headers=headers, data=data, timeout=3)
        return ':"1"' in res.text

def iterableBoard(board, is_miner=False, num=-1, start_page=1, sess=None):
    # create session
    if sess is None:
        sess = requests.session()
    url = "http://m.dcinside.com/list.php"
    params = { "id": board, "page": str(start_page) }
    i = 0
    last_doc_no = 0
    doc_in_page = 0
    page = start_page
    header = GET_HEADERS.copy()
    header["Referer"] = url
    while num != 0:
        params["page"] = str(page)
        res = _get(sess, url, headers=header, params=params, timeout=3)
        t, start = raw_parse(res.text, '"list_best">', "<", i)
        t, end = raw_parse(res.text, "</ul", ">", start)
        i = start
        while num != 0 and i < end and i >= start:
            doc_no, i = raw_parse(res.text, 'no=', '&', i)
            if i >= end or i == 0:
                break
            doc_no = int(doc_no)
            if last_doc_no != 0 and doc_no >= last_doc_no:
                continue
            last_doc_no = doc_no
            t, i = raw_parse(res.text, 'ico_pic ', '"', i)
            has_image = (t == "ico_p_y")
            title, i = raw_parse(res.text, 'txt">', '<', i)
            t, i = raw_parse(res.text, 'txt_num">', "<", i)
            comments = t[1:-1] if len(t)>0 else "0"
            name, i = raw_parse(res.text, 'name">', "<", i)
            t, i = raw_parse(res.text, 'class="', '"', i)
            ip = None
            if t == "userip":
                ip, i = raw_parse(res.text, '>', '<', i) 
            date, i = raw_parse(res.text, "<span>", "<", i)
            t, i = raw_parse(res.text, '조회', "<", i)
            views, i = raw_parse(res.text, '>', '<', i)
            t, i = raw_parse(res.text, '추천', "<", i)
            votes, i = raw_parse(res.text, '>', '<', i)
            if "/" in comments: comments = sum((int(z) for z in comments.split("/")))
            if "/" in votes: votes = sum(int(z) for z in votes.split("/"))
            yield {
                "doc_no": doc_no, "title": title, "name": name, "ip": ip, "date": date, "views": int(views), "votes": int(votes), "comments": int(comments),
                }
            num -= 1
        page += 1
        
def iterableComments(board, is_miner, doc_no, num=-1, sess=None):
    if sess is None:
        sess = requests.session()
    referer = "http://m.dcinside.com/view.php?id=%s&no=%s" % (board, doc_no)
    url = "http://m.dcinside.com/%s/comment_more_new.php" % ("m" if is_miner else "")
    page = 1
    params = {"id": board, "no": str(doc_no), "com_page": str(page), "write": "write"}
    headers = GET_HEADERS.copy()
    headers["Referer"] = referer
    headers["Accept-Language"] = "en-US,en;q=0.9"
    num_comments, i, count = 999999999,0,0
    
    while num != 0:
        params["com_page"] = str(page)
        res = _get(sess, url, headers=headers, params=params, timeout=3)
        t, i = raw_parse(res.text, 'txt_total">(', ')', i)
        if i==0: break
        num_comments = min(num_comments, int(t))
        i = -1
        while num != 0:
            date, i3 = rraw_parse(res.text, '"date">', '<', i)
            comment_no2, i2 = rraw_parse(res.text, ":del_layer('", "'", i)
            comment_no, i = rraw_parse(res.text, ":comment_del('", "'", i)
            if i==0 and i2==0 and i3==0: break
            if i<=i2<=i3: comment_no, i = None, i3
            elif i<=i3<=i2: comment_no, i = comment_no2, i2
            contents, i = rraw_parse(res.text, '"txt">', '="info">', i)
            ip, i = rraw_parse(res.text, '"ip">', '<', i)
            name, i = rraw_parse(res.text, '>[', ']<', i)
            name = name.replace('<span class="nick_comm flow"></span>', "")
            name = name.replace('<span class="nick_comm fixed"></span>', "")
            name = name.replace('<span class="nick_mnr_comm ic_gc_df"></span>', "")
            yield {
                "name": name.strip(), "comment_no": comment_no, "ip": ip.strip(), "contents": contents[:-66].strip(), "date": date.strip()
                }
            num -= 1
            count += 1
        if count >= num_comments:
            break
        else:
            page += 1

def writeDoc(board, is_miner, title, contents, name=None, password=None, sess=None):
    # create session
    if sess is None:
        sess = requests.Session()
    url = "http://m.dcinside.com/write.php?id=%s&mode=write" % board
    res = _get(sess, url, headers=GET_HEADERS)
    # get secret input
    data = extractKeys(res.text, 'g_write.php"')
    if name: data['name'] = name
    if password: data['password'] = password
    data['subject'] = title
    data['memo'] = contents
    # get new block key
    headers = POST_HEADERS.copy()
    headers["Referer"] = url
    url = "http://m.dcinside.com/_option_write.php"
    
    verify_data = {
        "id": data["id"],
        "w_subject": title,
        "w_memo": contents,
        "w_filter": "",
        "mode": "write_verify",
    }
    new_block_key = _post(sess, url, data=verify_data, headers=headers).json()
    if new_block_key["msg"] != "5":
        print("Error while write doc(block_key)")
        print(result)
        raise Exception(repr(new_block_key))
    data["Block_key"] = new_block_key["data"]
    print(data)
    url = "http://upload.dcinside.com/g_write.php"
    result = _post(sess, url, data=data, headers=headers).text
    doc_no, i = raw_parse(result, "no=", '"')
    if doc_no is None:
        print("Error while writing doc")
        raise Exception(repr(result))
    return doc_no

def modifyDoc(board, is_miner, doc_no, title, contents, name=None, password=None, sess=None):
    # create session
    if sess is None:
        sess = requests.Session()
    url = "http://m.dcinside.com/write.php"
    res = None
    if password:
        data = {"write_pw": password, "no": doc_no, "id": board, "mode": "modify", "page": ""}
        headers = GET_HEADERS.copy()
        headers["Referer"] = "http://m.dcinside.com/password.php?id=%s&no=%s&mode=modify" % (board, doc_no)
        headers["Origin"] = "http://m.dcinside.com"
        headers["Host"] = "m.dcinside.com"
        headers["Accept-Language"] = "en-US,en;q=0.9"
        headers["Cache-Control"] = "max-age=0"
        headers["Connection"] = "keep-alive"
        res = _post(sess, url, data=data, headers=headers)
    else:
        params = {"id": board, "no": doc_no, "mode": "modify", "page": ""}
        headers = GET_HEADERS.copy()
        headers["Referer"] = "http://m.dcinside.com/view.php?id=%s&no=%s&page=" % (board, doc_no)
        headers["Host"] = "m.dcinside.com"
        headers["Origin"] = "http://m.dcinside.com"
        headers["Accept-Language"] = "en-US,en;q=0.9"
        headers["Cache-Control"] = "max-age=0"
        headers["Connection"] = "keep-alive"
        res = _get(sess, url, params=params, headers=headers)
    data = extractKeys(res.text, 'g_write.php"')
    # get secret input
    if "id" not in data:
        print("Error while modify doc(Maybe there's no article with that id)")
        raise Exception(repr(res.text))
    if name: data['name'] = name
    if password: data['password'] = password
    data['subject'] = title
    data['memo'] = contents
    # get new block key
    headers = POST_HEADERS.copy()
    headers["Referer"] = url
    url = "http://m.dcinside.com/_option_write.php"
    verify_data = {
        "id": data["id"],
        "w_subject": title,
        "w_memo": contents,
        "w_filter": "",
        "mode": "write_verify",
    }
    new_block_key = _post(sess, url, data=verify_data, headers=headers).json()
    if new_block_key["msg"] != "5":
        print("Error while modify doc(block_key)")
        print(result)
        raise Exception(repr(new_block_key))
    data["Block_key"] = new_block_key["data"]
    url = "http://upload.dcinside.com/g_write.php"
    result = _post(sess, url, data=data, headers=headers).text
    doc_no, i = raw_parse(result, "no=", '"')
    if doc_no is None:
        print("Error while writing doc")
        raise Exception(repr(result))
    return doc_no

def removeDoc(board, is_miner, doc_no, password=None, sess=None):
    # create session
    if sess is None:
        sess = requests.Session()
    headers = POST_HEADERS.copy()
    data = {"no": doc_no, "id": board, "page": "", "mode": "board_del"}
    if password:
        url = "http://m.dcinside.com/_access_token.php"
        headers["Referer"] = "http://m.dcinside.com/password.php?id=%s&no=%s&mode=board_del2&flag=" % (board, doc_no)
        result = _post(sess, url, data={"token_verify": "nonuser_del"}, headers=headers).json()
        if result["msg"] != "5":
            print("Error while write doc(block_key)")
            print(result)
            raise Exception(repr(result))
        data["mode"] = "board_del2"
        data["write_pw"] = password
        data["con_key"] = result["data"]
    else:
        url = "http://m.dcinside.com/view.php?id=%s&no=%s" % (board, doc_no)
        res = _get(sess, url, headers=GET_HEADERS)
        user_no = raw_parse(res.text, '"user_no" value="', '"')[0]
        headers["Referer"] = url
        data["mode"] = "board_del"
        data["user_no"] = user_no
    url = "http://m.dcinside.com/_option_write.php"
    result = _post(sess, url, data=data, headers=headers).json()
    if (type(result)==int and result != 1) or (type(result)==dict and result["msg"] != "1"):
        print("Error while remove doc: ", result)
        raise Exception(repr(result))
    return sess


def writeComment(board, is_miner, doc_no, contents, name=None, password=None, sess=None):
    # create session
    if sess is None:
        sess = requests.Session()
    url = "http://m.dcinside.com/view.php?id=%s&no=%s" % (board, doc_no)
    res = _get(sess, url, headers=GET_HEADERS, timeout=3)
    data = extractKeys(res.text, '"comment_write"')
    if name: data["comment_nick"] = name
    if password: data["comment_pw"] = password
    data["comment_memo"] = contents
    headers = POST_HEADERS.copy()
    headers["Referer"] = url
    url = "http://m.dcinside.com/_access_token.php"
    block_key = _post(sess, url, headers=headers, data={"token_verify": "com_submit"}, timeout=3).json()
    if block_key["msg"] != "5":
        print("Error while write comment(block key)")
        raise Exception(repr(block_key))
    url = "http://m.dcinside.com/_option_write.php"
    data["con_key"] = block_key["data"]
    result = _post(sess, url, headers=headers, data=data, timeout=3)
    result = result.json()
    if (type(result)==int and result != 1) or (type(result)==dict and result["msg"] != "1"):
        print("Error while write comment", result)
        raise Exception(repr(result))
    return doc_no

def removeComment(board, is_miner, doc_no, comment_no, password=None, sess=None):
    if sess is None:
        sess = requests.Session()
    data = None
    headers = POST_HEADERS.copy()
    headers["Referer"] = "http://m.dcinside.com/view.php?id=%s&no=%s" % (board, doc_no)
    if password: 
        data = {"id": board, "no": doc_no, "iNo": comment_no, "user_no": "nonmember", "comment_pw": password, "best_chk": "", "con_key": None, "mode": "comment_del"}
        url = "http://m.dcinside.com/_access_token.php"
        block_key = _post(sess, url, headers=headers, data={"token_verify": "nonuser_com_del"}, timeout=3).json()
        if block_key["msg"] != "5":
            print("Error while remove comment(block key)")
            raise Exception(repr(block_key))
        data["con_key"] = block_key["data"]
    else:
        url = "http://m.dcinside.com/view.php?id=%s&no=%s" % (board, doc_no)
        res = _get(sess, url, headers=GET_HEADERS, timeout=3)
        board_id, i = raw_parse(res.text, '"board_id" value="', '"')
        if not board_id:
            raise Exception("Non-password remove comment without login")
        user_no, _ = raw_parse(res.text, '"user_no" value="', '"', i)
        data = {"id": board, "no": doc_no, "iNo": comment_no, "user_no": user_no, "board_id": board_id, "best_chk": "", "mode": "comment_del"}
    url = "http://m.dcinside.com/_option_write.php"
    result = _post(sess, url, headers=headers, data=data, timeout=3)
    result = result.json()
    if (type(result)==int and result != 1) or (type(result)==dict and result["msg"] != "1"):
        print("Error while write comment", result)
        raise Exception(repr(result))
    return comment_no
    

def login(userid, password, sess=None):
    if sess is None:
        sess = requests.Session()
    url = "http://m.dcinside.com/login.php?r_url=m.dcinside.com%2Findex.php"
    headers = GET_HEADERS.copy()
    headers["Referer"] = "http://m.dcinside.com/index.php"
    res = _get(sess, url, headers=headers, timeout=3)
    data = extractKeys(res.text, '"login_process')
    headers = POST_HEADERS.copy()
    headers["Referer"] = url
    url = "http://m.dcinside.com/_access_token.php"
    res = _post(sess, url, headers=headers, data={"token_verify": "login", "con_key": data["con_key"]}, timeout=3)
    data["con_key"] = res.json()["data"]
    url = "https://dcid.dcinside.com/join/mobile_login_ok.php"
    headers["Host"] = "dcid.dcinside.com"
    headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
    headers["Accept-Encoding"] = "gzip, deflate, br"
    headers["Cache-Control"] = "max-age=0"
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    del(headers["X-Requested-With"])
    data["user_id"] = userid
    data["user_pw"] = password
    data["id_chk"] = ""
    if "form_ipin" in data: del(data["form_ipin"])
    res = _post(sess, url, headers=headers, data=data, timeout=3)
    while 0 <= res.text.find("rucode"):
        return login(userid, password)
    return sess
    
def logout(sess):
    url = "http://m.dcinside.com/logout.php?r_url=m.dcinside.com%2Findex.php"
    headers = GET_HEADERS.copy()
    headers["Referer"] = "http://m.dcinside.com/index.php"
    res = _get(sess, url, headers=headers, timeout=3)
    return sess
    
def extractKeys(html, start_form_keyword):
    p = ""
    start, end, i = 0, 0, 0
    result = {}
    (p, start) = raw_parse(html, start_form_keyword, '', i)
    (p, end) = raw_parse(html, '</form>', '', start)
    i = start
    while True:
        (p, i) = raw_parse(html, '<input type="hidde', '"', i)
        if not p or i >= end: break
        (name, i) = raw_parse(html, 'name="', '"', i)
        if not name or i >= end: break
        (value, i_max) = raw_parse(html, '', '>', i)
        (value, i) = raw_parse(html, 'value="', '"', i)
        if i_max > i:
            result[name] = value
        else:
            i = i_max
            result[name] = ""
    i = start
    while True:
        (p, i) = raw_parse(html, "<input type='hidde", "'", i)
        if not p or i >= end: break
        (name, i) = raw_parse(html, "name='", "'", i)
        if not name or i >= end: break
        (value, i_max) = raw_parse(html, '', '>', i)
        (value, i) = raw_parse(html, "value='", "'", i)
        if i_max > i:
            result[name] = value
        else:
            i = i_max
            result[name] = ""
    while True:
        (p, i) = raw_parse(html, '<input type="hidde', '"', i)
        if not p or i >= end: break
        (name, i) = raw_parse(html, 'NAME="', '"', i)
        if not name or i >= end: break
        (value, i_max) = raw_parse(html, '', '>', i)
        (value, i) = raw_parse(html, 'value="', '"', i)
        if i_max > i:
            result[name] = value
        else:
            i = i_max
            result[name] = ""
    return result

def rraw_parse(text, start, end, offset=0):
    s = text.rfind(start, 0, offset)
    if s == -1: return None, 0
    s += len(start)
    e = text.find(end, s)
    if e == -1: return None, 0
    return text[s:e], s - len(start)

def raw_parse(text, start, end, offset=0):
    s = text.find(start, offset)
    if s == -1: return None, 0
    s += len(start)
    e = text.find(end, s)
    if e == -1: return None, 0
    return text[s:e], e
