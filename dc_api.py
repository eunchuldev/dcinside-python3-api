import asyncio
import json
import lxml.html
from datetime import datetime, timedelta
import itertools
import aiohttp
import filetype

DOCS_PER_PAGE = 200

GET_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 Mobile Safari/537.36"
     }
XML_HTTP_REQ_HEADERS = {
    "Accept": "*/*",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 Mobile Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

POST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.0; SM-G892A Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/67.0.3396.87 Mobile Safari/537.36",
    }

GALLERY_POSTS_COOKIES = {
    "__gat_mobile_search": 1,
    "list_count": DOCS_PER_PAGE,
    }

import re
def unquote(encoded):
    return re.sub(r'\\u([a-fA-F0-9]{4}|[a-fA-F0-9]{2})', lambda m: chr(int(m.group(1), 16)), encoded)
def quote(decoded):
    arr = []
    for c in decoded:
        t = hex(ord(c))[2:].upper() 
        if len(t) >= 4:
            arr.append("%u" + t)
        else:
            arr.append("%" + t)
    return "".join(arr)
def peek(iterable):
    try:
        first = next(iterable)
    except StopIteration:
        return None
    return first, itertools.chain((first,), iterable)

class DocumentIndex:
    __slots__ = ["id", "subject", "title", "board_id", "has_image", "author", "time", "view_count", "comment_count", "voteup_count", "document", "comments"]
    def __init__(self, id, board_id, title, has_image, author, time, view_count, comment_count, voteup_count, document, comments, subject):
        self.id = id
        self.board_id = board_id
        self.title = title
        self.has_image = has_image
        self.author = author
        self.time = time
        self.view_count = view_count
        self.comment_count = comment_count
        self.voteup_count = voteup_count
        self.document = document
        self.comments = comments
        self.subject = subject
    def __str__(self):
        return f"{self.subject or ''}\t|{self.id}\t|{self.time.isoformat()}\t|{self.author}\t|{self.title}({self.comment_count}) +{self.voteup_count}"

class Document:
    __slots__ = ["id", "board_id", "title", "author", "author_id", "contents", "images", "html", "view_count", "voteup_count", "votedown_count", "logined_voteup_count", "time", "subject", "comments"]
    def __init__(self, id, board_id, title, author, author_id, contents, images, html, view_count, voteup_count, votedown_count, logined_voteup_count, time, comments, subject=None):
        self.id = id
        self.board_id = board_id
        self.title = title
        self.author = author
        self.author_id = author_id
        self.contents = contents
        self.images = images
        self.html = html
        self.view_count = view_count
        self.voteup_count = voteup_count
        self.votedown_count = votedown_count
        self.logined_voteup_count = logined_voteup_count
        self.comments = comments
        self.time = time
        self.subject = None
    def __str__(self):
        return f"{self.subject or ''}\t|{self.id}\t|{self.time.isoformat()}\t|{self.author}\t|{self.title}({self.comment_count}) +{self.voteup_count} -{self.votedown_count}\n{self.contents}"

class Comment:
    __slots__ = ["id", "parent_id", "author", "author_id", "contents", "dccon", "voice", "time"]
    def __init__(self, id, parent_id, author, author_id, contents, dccon, voice, time):
        self.id = id
        self.parent_id = parent_id
        self.author = author
        self.author_id = author_id
        self.contents = contents
        self.dccon = dccon
        self.voice = voice
        self.time = time
    def __str__(self):
        return f"ㄴ {self.author}: {self.contents or ''}{self.dccon or ''}{self.voice or ''} | {self.time}"

class Image:
    __slots__ = ["src", "document_id", "board_id", "session"]
    def __init__(self, src, document_id, board_id, session):
        self.src = src
        self.document_id = document_id
        self.board_id = board_id
        self.session = session
    async def load(self):
        headers = GET_HEADERS.copy()
        headers["Referer"] = "https://m.dcinside.com/board/{}/{}".format(self.board_id, self.document_id)
        async with self.session.get(self.src, cookies=GALLERY_POSTS_COOKIES, headers=headers) as res:
            return await res.read()
    async def download(self, path):
        headers = GET_HEADERS.copy()
        headers["Referer"] = "https://m.dcinside.com/board/{}/{}".format(self.board_id, self.document_id)
        async with self.session.get(self.src, cookies=GALLERY_POSTS_COOKIES, headers=headers) as res:
            bytes = await res.read()
            ext = filetype.guess(bytes).extension
            with open(path + '.' + ext, 'wb') as f:
                f.write(bytes)



class API:
    def __init__(self):
        self.session = aiohttp.ClientSession(headers=GET_HEADERS, cookies={"_ga": "GA1.2.693521455.1588839880"})
    async def close(self):
        await self.session.close()
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args, **kwargs):
        await self.close()
    async def watch(self, board_id):
        pass
    async def board(self, board_id, num=-1, start_page=1, document_id_upper_limit=None, document_id_lower_limit=None, is_minor=False):
        page = start_page
        while num:
            url = "https://m.dcinside.com/board/{}?page={}".format(board_id, page)
            async with self.session.get(url) as res:
                text = await res.text()
                parsed = lxml.html.fromstring(text)
            doc_headers = (i[0] for i in parsed.xpath("//ul[contains(@class, 'gall-detail-lst')]/li") if not i.get("class", "").startswith("ad"))
            for doc in doc_headers:
                document_id = doc[0].get("href").split("/")[-1].split("?")[0]
                if document_id_upper_limit and int(document_id_upper_limit) <= int(document_id): continue
                if document_id_lower_limit and int(document_id_lower_limit) >= int(document_id): return
                if len(doc[0][1]) == 5:
                    subject = doc[0][1][0].text
                    author = doc[0][1][1].text
                    time= self.__parse_time(doc[0][1][2].text)
                    view_count= int(doc[0][1][3].text.split()[-1])
                    voteup_count= int(doc[0][1][4][0].text.split()[-1])
                else:
                    subject = None
                    author = doc[0][1][0].text
                    time= self.__parse_time(doc[0][1][1].text)
                    view_count= int(doc[0][1][2].text.split()[-1])
                    voteup_count= int(doc[0][1][3].text_content().split()[-1])
                title = doc[0][0][1].text
                indexdata = DocumentIndex(
                    id= document_id,
                    board_id=board_id,
                    title= title,
                    has_image= doc[0][0][0].get("class").endswith("img"),
                    author= author,
                    view_count= view_count,
                    voteup_count= voteup_count,
                    comment_count= int(doc[1][0].text),
                    document= lambda: self.document(board_id, document_id),
                    comments= lambda: self.comments(board_id, document_id),
                    time= time,
                    subject=subject
                    )
                yield(indexdata)
                num-=1
                if num==0: 
                    break
            if not doc_headers: 
                break
            else: 
                page+=1
    async def document(self, board_id, document_id):
        url = "https://m.dcinside.com/board/{}/{}".format(board_id, document_id)
        async with self.session.get(url) as res:
            text = await res.text()
            parsed = lxml.html.fromstring(await res.text())
        doc_content_container = parsed.xpath("//div[@class='thum-txtin']")
        doc_head_containers = parsed.xpath("//div[@class='gallview-tit-box ']")
        if not len(doc_head_containers):
            return None
        doc_head_container = doc_head_containers[0]
        if len(doc_content_container):
            title = " ".join(doc_head_container[0].text.strip().split())
            author = doc_head_container[1][0][0].text.strip()
            author_id = None if len(doc_head_container[1]) <= 1 else doc_head_container[1][1][0].get("href").split("/")[-1]
            time = doc_head_container[1][0][1].text.strip()
            doc_content = parsed.xpath("//div[@class='thum-txtin']")[0]
            for adv in doc_content.xpath("div[@class='adv-groupin']"):
                adv.getparent().remove(adv)
            for adv in doc_content.xpath("//img"):
                if adv.get("src", "").startswith("https://nstatic") and not adv.get("data-original"):
                    adv.getparent().remove(adv)
            return Document(
                    id = document_id,
                    board_id = board_id,
                    title= title,
                    author= author,
                    author_id =author_id,
                    contents= '\n'.join(i.strip() for i in doc_content.itertext() if i.strip() and not i.strip().startswith("이미지 광고")),
                    images= [Image(
                        src=i.get("data-original", i.get("src")), 
                        board_id=board_id, 
                        document_id=document_id, 
                        session=self.session)
                        for i in doc_content.xpath("//img") 
                            if i.get("data-original") or (not i.get("src","").startswith("https://nstatic") and
                                not i.get("src", "").startswith("https://img.iacstatic.co.kr") and i.get("src"))],
                    html= lxml.html.tostring(doc_content, encoding=str),
                    view_count= int(parsed.xpath("//ul[@class='ginfo2']")[1][0].text.strip().split()[1]),
                    voteup_count= int(parsed.xpath("//span[@id='recomm_btn']")[0].text.strip()),
                    votedown_count= int(parsed.xpath("//span[@id='nonrecomm_btn']")[0].text.strip()),
                    logined_voteup_count= int(parsed.xpath("//span[@id='recomm_btn_member']")[0].text.strip()),
                    comments= lambda: self.comments(board_id, document_id),
                    time= self.__parse_time(time)
                    )
        else:
            # fail due to unusual tags in mobile version
            # at now, just skip it
            return None
        ''' !TODO: use an alternative(PC) protocol to fetch document
        else:
            url = "https://gall.dcinside.com/{}?no={}".format(board_id, document_id)
            res = sess.get(url, timeout=TIMEOUT, headers=ALTERNATIVE_GET_HEADERS)
            parsed = lxml.html.fromstring(res.text)
            doc_content = parsed.xpath("//div[@class='thum-txtin']")[0]
            return '\n'.join(i.strip() for i in doc_content.itertext() if i.strip() and not i.strip().startswith("이미지 광고")), [i.get("src") for i in doc_content.xpath("//img") if not i.get("src","").startswith("https://nstatic")], comments(board_id, document_id, sess=sess)
        '''
    async def comments(self, board_id, document_id, num=-1, start_page=1):
        url = "https://m.dcinside.com/ajax/response-comment"
        for page in range(start_page, 999999):
            payload = {"id": board_id, "no": document_id, "cpage": page, "managerskill":"", "del_scope": "1", "csort": ""}
            async with self.session.post(url, headers=XML_HTTP_REQ_HEADERS, data=payload) as res:
                parsed = lxml.html.fromstring(await res.text())
            if not len(parsed[1].xpath("li")): break
            #for li in reversed(parsed[1].xpath("li")):
            for li in parsed[1].xpath("li"):
                if not len(li[0]): continue
                yield Comment(
                    id= li.get("no"),
                    parent_id= li.get("m_no"),
                    author= li[0].text + ("{}".format(li[0][0].text) if li[0][0].text else ""),
                    author_id= li[0][1].get("data-info", None) if len(li[0]) > 1 else None,
                    contents= '\n'.join(i.strip() for i in li[1].itertext()),
                    dccon= li[1][0].get("data-original", li[1][0].get("src", None)) if len(li[1]) and li[1][0].tag=="img" else None,
                    voice= li[1][0].get("src", None) if len(li[1]) and li[1][0].tag=="iframe" else None,
                    time= self.__parse_time(li[2].text))
                num -= 1
                if num == 0:
                    return
            page_num_els = parsed.xpath("span[@class='pgnum']")
            if page_num_els:
                p = page_num_els[0].itertext()
                next(p)
                if page == next(p)[1:]: 
                    break
            else: 
                break 
    async def write_comment(self, board_id, document_id, contents="", dccon_id="", dccon_src="", parent_comment_id="", name="", password="", is_minor=False):
        url = "https://m.dcinside.com/board/{}/{}".format(board_id, document_id)
        async with self.session.get(url) as res:
            parsed = lxml.html.fromstring(await res.text())
        hide_robot = parsed.xpath("//input[@class='hide-robot']")[0].get("name")
        csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
        title = parsed.xpath("//span[@class='tit']")[0].text.strip()
        board_name = parsed.xpath("//a[@class='gall-tit-lnk']")[0].text.strip()
        con_key = await self.__access("com_submit", url, require_conkey=False, csrf_token=csrf_token)
        header = XML_HTTP_REQ_HEADERS.copy()
        header["Referer"] = url
        header["Host"] = "m.dcinside.com"
        header["Origin"] = "https://m.dcinside.com"
        header["X-CSRF-TOKEN"] = csrf_token
        cookies = {
            "m_dcinside_" + board_id: board_id,
            "m_dcinside_lately": quote(board_id + "|" + board_name + ","),
            "_ga": "GA1.2.693521455.1588839880",
            }
        url = "https://m.dcinside.com/ajax/comment-write"
        payload = {
                "comment_memo": contents,
                "comment_nick": name,
                "comment_pw": password,
                "mode": "com_write",
                "comment_no": parent_comment_id,
                "id": board_id,
                "no": document_id,
                "best_chk": "",
                "subject": title,
                "board_id": "0",
                "reple_id":"",
                "cpage": "1",
                "con_key": con_key,
                hide_robot: "1",
                }
        if dccon_id: payload["detail_idx"] = dccon_id
        if dccon_src: payload["comment_memo"] = "<img src='{}' class='written_dccon' alt='1'>".format(dccon_src)
        #async with self.session.post(url, headers=header, data=payload, cookies=cookies) as res:
        async with self.session.post(url, headers=header, data=payload, cookies=cookies) as res:
            parsed = await res.text()
        try:
            parsed = json.loads(parsed)
        except Exception as e:
            raise Exception("Error while writing comment: " + unquote(str(parsed)))
        if "data" not in parsed:
            raise Exception("Error while writing comment: " + unquote(str(parsed)))
        return str(parsed["data"])
    async def modify_document(self, board_id, document_id, title="", contents="", name="", password="", is_minor=False):
        if not password:
            url = "https://m.dcinside.com/write/{}/modify/{}".format(board_id, document_id)
            async with self.session.get(url) as res:
                return await self.__write_or_modify_document(board_id, title, contents, name, password, intermediate=await res.text(), intermediate_referer=url, document_id=document_id, is_minor=is_minor)
        url = "https://m.dcinside.com/confirmpw/{}/{}?mode=modify".format(board_id, document_id)
        referer = url
        async with self.session.get(url) as res:
            parsed = lxml.html.fromstring(await res.text())
        token = parsed.xpath("//input[@name='_token']")[0].get("value", "")
        csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
        con_key = await self.__access("Modifypw", url, require_conkey=False, csrf_token=csrf_token)
        payload = {
                "_token": token,
                "board_pw": password,
                "id": board_id,
                "no": document_id,
                "mode": "modify",
                "con_key": con_key,
                }
        header = XML_HTTP_REQ_HEADERS.copy()
        header["Referer"] = referer
        header["Host"] = "m.dcinside.com"
        header["Origin"] = "https://m.dcinside.com"
        header["X-CSRF-TOKEN"] = csrf_token
        url = "https://m.dcinside.com/ajax/pwcheck-board"
        async with self.session.post(url, headers=header, data=payload) as res:
            res = await res.text()
            if not res.strip():
                Exception("Error while modifing: maybe the password is incorrect")
        payload = {
                "board_pw": password,
                "id": board_id,
                "no": document_id,
                "_token": csrf_token
                }
        header = POST_HEADERS.copy()
        header["Referer"] = referer
        url = "https://m.dcinside.com/write/{}/modify/{}".format(board_id, document_id)
        async with self.session.post(url, headers=header, data=payload) as res:
            return await self.__write_or_modify_document(board_id, title, contents, name, password, intermediate=await res.text(), intermediate_referer=url, document_id=document_id)
    async def remove_document(self, board_id, document_id, password="", is_minor=False):
        if not password:
            url = "https://m.dcinside.com/board/{}/{}".format(board_id, document_id)
            async with self.session.get(url) as res:
                parsed = lxml.html.fromstring(await res.text())
            csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
            header = XML_HTTP_REQ_HEADERS.copy()
            header["Referer"] = url
            header["X-CSRF-TOKEN"] = csrf_token
            con_key = await self.__access("board_Del", url, require_conkey=False, csrf_token=csrf_token)
            url = "https://m.dcinside.com/del/board"
            payload = { "id": board_id, "no": document_id, "con_key": con_key }
            async with self.session.post(url, headers=header, data=payload) as res:
                res = await res.text()
            if res.find("true") < 0:
                raise Exception("Error while removing: " + unquote(str(res)))
            return True
        url = "https://m.dcinside.com/confirmpw/{}/{}?mode=del".format(board_id, document_id)
        referer = url
        async with self.session.get(url) as res:
            parsed = lxml.html.fromstring(await res.text())
        token = parsed.xpath("//input[@name='_token']")[0].get("value", "")
        csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
        board_name = parsed.xpath("//a[@class='gall-tit-lnk']")[0].text.strip()
        con_key = await self.__access("board_Del", url, require_conkey=False, csrf_token=csrf_token)
        payload = {
                "_token": token,
                "board_pw": password,
                "id": board_id,
                "no": document_id,
                "mode": "del",
                "con_key": con_key,
                }
        header = XML_HTTP_REQ_HEADERS.copy()
        header["Referer"] = url
        header["X-CSRF-TOKEN"] = csrf_token
        cookies = {
            "m_dcinside_" + board_id: board_id,
            "m_dcinside_lately": quote(board_id + "|" + board_name + ","),
            "_ga": "GA1.2.693521455.1588839880",
            }
        url = "https://m.dcinside.com/del/board"
        async with self.session.post(url, headers=header, data=payload, cookies=cookies) as res:
            res = await res.text()
        if res.find("true") < 0:
            raise Exception("Error while removing: " + unquote(str(res)))
        return True
    async def write_document(self, board_id, title="", contents="", name="", password="", is_minor=False):
        return await self.__write_or_modify_document(board_id, title, contents, name, password, is_minor=is_minor)
    async def __write_or_modify_document(self, board_id, title="", contents="", name="", password="", intermediate=None, intermediate_referer=None, document_id=None, is_minor=False):
        if not intermediate:
            url = "https://m.dcinside.com/write/{}".format(board_id)
            async with self.session.get(url) as res:
                parsed = lxml.html.fromstring(await res.text())
        else:
            parsed = lxml.html.fromstring(intermediate)
            url = intermediate_referer
        first_url = url
        rand_code = parsed.xpath("//input[@name='code']")
        rand_code = rand_code[0].get("value") if len(rand_code) else None
        user_id = parsed.xpath("//input[@name='user_id']")[0].get("value") if not name else None
        mobile_key = parsed.xpath("//input[@id='mobile_key']")[0].get("value")
        hide_robot = parsed.xpath("//input[@class='hide-robot']")[0].get("name")
        csrf_token = parsed.xpath("//meta[@name='csrf-token']")[0].get("content")
        con_key = await self.__access("dc_check2", url, require_conkey=False, csrf_token=csrf_token)
        board_name = parsed.xpath("//a[@class='gall-tit-lnk']")[0].text.strip()
        header = XML_HTTP_REQ_HEADERS.copy()
        header["Referer"] = url
        header["X-CSRF-TOKEN"] = csrf_token
        url = "https://m.dcinside.com/ajax/w_filter"
        payload = {
                "subject": title,
                "memo": contents,
                "mode": "write",
                "id": board_id,
                }
        if rand_code:
            payload["code"] = rand_code
        async with self.session.post(url, headers=header, data=payload) as res:
            res = await res.text()
            res = json.loads(res)
        if not res["result"]:
            raise Exception("Erorr while write document: " + str(res))
        header = POST_HEADERS.copy()
        url = "https://mupload.dcinside.com/write_new.php"
        header["Host"] = "mupload.dcinside.com"
        header["Referer"] = first_url
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
                "imgSize": "850",
                "is_minor": "1" if is_minor else "",
                "mobile_key": mobile_key,
                "GEY3JWF": hide_robot,
            }
        if rand_code:
            payload["code"] = rand_code
        if name:
            payload["name"] = name
            payload["password"] = password
        else:
            payload["user_id"] = user_id
        if intermediate:
            payload["mode"] = "modify"
            payload["delcheck"] = ""
            payload["t_ch2"] = ""
            payload["no"] = document_id
        cookies = {
            "m_dcinside_" + board_id: board_id,
            "m_dcinside_lately": quote(board_id + "|" + board_name + ","),
            "_ga": "GA1.2.693521455.1588839880",
            }
        async with self.session.post(url, headers=header, data=payload, cookies=cookies) as res:
            res = await res.text()

    async def __access(self, token_verify, target_url, require_conkey=True, csrf_token=None):
        if require_conkey:
            async with self.session.get(target_url) as res:
                parsed = lxml.html.fromstring(await res.text())
            con_key = parsed.xpath("//input[@id='con_key']")[0].get("value")
            payload = { "token_verify": token_verify, "con_key": con_key }
        else:
            payload = { "token_verify": token_verify, }
        url = "https://m.dcinside.com/ajax/access"
        headers = XML_HTTP_REQ_HEADERS.copy()
        headers["Referer"] = target_url
        headers["X-CSRF-TOKEN"] = csrf_token
        async with self.session.post(url, headers=headers, data=payload) as res:
            return (await res.json())["Block_key"]
    def __parse_time(self, time): 
        today = datetime.now() 
        if len(time) <= 5: 
            if time.find(":") > 0:
                return datetime.strptime(time, "%H:%M").replace(year=today.year, month=today.month, day=today.day)
            else:
                return datetime.strptime(time, "%m.%d").replace(year=today.year, hour=23, minute=59, second=59)
        elif len(time) <= 11:
            if time.find(":") > 0:
                return datetime.strptime(time, "%m.%d %H:%M").replace(year=today.year)
            else:
                return datetime.strptime(time, "%y.%m.%d").replace(year=today.year, hour=23, minute=59, second=59)
        elif len(time) <= 16:
            if time.count(".") >= 2:
                return datetime.strptime(time, "%Y.%m.%d %H:%M")
            else:
                return datetime.strptime(time, "%m.%d %H:%M:%S").replace(year=today.year)
        else:
            if "." in time:
                return datetime.strptime(time, "%Y.%m.%d %H:%M:%S")
            else:
                return datetime.strptime(time, "%Y-%m-%d %H:%M:%S")

import unittest

class Test(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        pass
    async def asyncSetUp(self):
        self.api = API()
    async def asyncTearDown(self):
        await self.api.close()
    async def test_async_with(self):
        async with API() as api:
            doc = api.board(board_id='aoegame', num=1).__anext__()
            self.assertNotEqual(doc, None)
    async def test_read_minor_board_one(self):
        async for doc in self.api.board(board_id='aoegame', num=1):
            for attr in doc.__slots__:
                if attr == 'subject': continue
                val = getattr(doc, attr)
                self.assertNotEqual(val, None, attr)
                self.assertNotEqual(val, '', attr)
            self.assertGreater(doc.time, datetime.now() - timedelta(hours=1))
            self.assertLess(doc.time, datetime.now() + timedelta(hours=1))
    async def test_read_minor_board_many(self):
        count = 0
        async for doc in self.api.board(board_id='aoegame', num=201):
            for attr in doc.__slots__:
                if attr == 'subject': continue
                val = getattr(doc, attr)
                self.assertNotEqual(val, None, attr)
                self.assertNotEqual(val, '', attr)
            count += 1
            self.assertGreater(doc.time, datetime.now() - timedelta(hours=1))
            self.assertLess(doc.time, datetime.now() + timedelta(hours=1))
        self.assertAlmostEqual(count, 201)
    async def test_read_minor_recent_comments(self):
        async for doc in self.api.board(board_id='aoegame'):
            comments = [comm async for comm in doc.comments()]
            if not comments: continue
            for comm in comments:
                for attr in comm.__slots__:
                    if attr in ['contents', 'dccon', 'voice', 'author_id']: continue
                    val = getattr(comm, attr)
                    self.assertNotEqual(val, None, attr)
                    self.assertNotEqual(val, '', attr)
                self.assertNotEqual(comm.contents or comm.dccon or comm.voice, None)
                self.assertGreater(comm.time, datetime.now() - timedelta(hours=1))
                self.assertLess(comm.time, datetime.now() + timedelta(hours=1))
            break
    async def test_read_board_one(self):
        async for doc in self.api.board(board_id='programming', num=1):
            for attr in doc.__slots__:
                if attr == 'subject': continue
                val = getattr(doc, attr)
                self.assertNotEqual(val, None, attr)
                self.assertNotEqual(val, '', attr)
            self.assertGreater(doc.time, datetime.now() - timedelta(hours=24))
            self.assertLess(doc.time, datetime.now() + timedelta(hours=1))
    async def test_read_board_many(self):
        count = 0
        async for doc in self.api.board(board_id='programming', num=201):
            for attr in doc.__slots__:
                if attr == 'subject': continue
                val = getattr(doc, attr)
                self.assertNotEqual(val, None, attr)
                self.assertNotEqual(val, '', attr)
            count += 1
            self.assertGreater(doc.time, datetime.now() - timedelta(hours=24))
            self.assertLess(doc.time, datetime.now() + timedelta(hours=1))
        self.assertAlmostEqual(count, 201)
    async def test_read_recent_comments(self):
        async for doc in self.api.board(board_id='aoegame'):
            comments = [comm async for comm in doc.comments()]
            if not comments: continue
            for comm in comments:
                for attr in comm.__slots__:
                    if attr in ['contents', 'dccon', 'voice', 'author_id']: continue
                    val = getattr(comm, attr)
                    self.assertNotEqual(val, None, attr)
                    self.assertNotEqual(val, '', attr)
                self.assertNotEqual(comm.contents or comm.dccon or comm.voice, None)
                self.assertGreater(comm.time, datetime.now() - timedelta(hours=24))
                self.assertLess(comm.time, datetime.now() + timedelta(hours=1))
            break
    async def test_minor_document(self):
        doc = await (await self.api.board(board_id='aoegame', num=1).__anext__()).document()
        self.assertNotEqual(doc, None)
        for attr in doc.__slots__:
            if attr in ['author_id', 'subject']: continue
            val = getattr(doc, attr)
            self.assertNotEqual(val, None, attr)
            self.assertNotEqual(val, '', attr)
        self.assertGreater(doc.time, datetime.now() - timedelta(hours=1))
        self.assertLess(doc.time, datetime.now() + timedelta(hours=1))
    async def test_document(self):
        doc = await (await self.api.board(board_id='programming', num=1).__anext__()).document()
        self.assertNotEqual(doc, None)
        for attr in doc.__slots__:
            if attr in ['author_id', 'subject']: continue
            val = getattr(doc, attr)
            self.assertNotEqual(val, None, attr)
        self.assertGreater(doc.time, datetime.now() - timedelta(hours=1))
        self.assertLess(doc.time, datetime.now() + timedelta(hours=1))
    '''
    async def test_write_mod_del_document_comment(self):
        board_id='programming'
        doc_id = await self.api.write_document(board_id=board_id, title="제목", contents="내용", name="닉네임", password="비밀번호")
        doc = await self.api.document(board_id=board_id, document_id=doc_id)
        self.assertEqual(doc.contents, "내용")
        doc_id = await self.api.modify_document(board_id=board_id, document_id=doc_id, title="수정된 제목", contents="수정된 내용", name="수정된 닉네임", password="비밀번호")
        doc = await self.api.document(board_id=board_id, document_id=doc_id)
        self.assertEqual(doc.contents, "수정된 내용")
        comm_id = await self.api.write_comment(board_id=board_id, document_id=doc_id, contents="댓글", name="닉네임", password="비밀번호")
        doc = await self.api.document(board_id=board_id, document_id=doc_id)
        comm = await doc.comments().__anext__()
        self.assertEqual(comm.contents, "댓글")
        await self.api.remove_document(board_id=board_id, document_id=doc_id, password="비밀번호")
        doc = await self.api.document(board_id=board_id, document_id=doc_id)
        self.assertEqual(doc, None)
    async def test_minor_write_mod_del_document_comment(self):
        board_id='stick'
        doc_id = await self.api.write_document(board_id=board_id, title="제목", contents="내용", name="닉네임", password="비밀번호", is_minor=True)
        doc = await self.api.document(board_id=board_id, document_id=doc_id)
        self.assertEqual(doc.contents, "내용")
        doc_id = await self.api.modify_document(board_id=board_id, document_id=doc_id, title="수정된 제목", contents="수정된 내용", name="수정된 닉네임", password="비밀번호", is_minor=True)
        doc = await self.api.document(board_id=board_id, document_id=doc_id)
        self.assertEqual(doc.contents, "수정된 내용")
        comm_id = await self.api.write_comment(board_id=board_id, document_id=doc_id, contents="댓글", name="닉네임", password="비밀번호")
        doc = await self.api.document(board_id=board_id, document_id=doc_id)
        comm = await doc.comments().__anext__()
        self.assertEqual(comm.contents, "댓글")
        await self.api.remove_document(board_id=board_id, document_id=doc_id, password="비밀번호")
        doc = await self.api.document(board_id=board_id, document_id=doc_id)
        self.assertEqual(doc, None)
    '''

if __name__ == "__main__":
    unittest.main()

