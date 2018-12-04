# dcinside-python3-api
Deadly simple non official dcinside api for python3
```python
# 프로그래밍 갤러리 글 헤더 무한 크롤링(빠름)
for doc in dc_api.board(board_id="programming", skip_contents=True):
    print(doc["id"], doc["title"], doc["author"], doc["date"]) 
# => "131293"
# => "땔감 벗어나는법.tip ㅇㅇ(10.42) 1:41"
# => "왜 이거 안돼냐? ㅇㅇ(192.231) 1:40"
# => ...
```
```python
# 프로그래밍 갤러리 글내용, 이미지, 댓글 포함 무한 크롤링(느림)
for doc in dc_api.board(board_id="programming"):
    print(doc["contents"])  # => "ㅗㅜㅑ\n미친다.."
    print(doc["images"])    # => "[imgsrc1, imgsrc2, ...]"
    for com in doc["comments"]:
        print(com["author"], com["contents"], com["date"])
        # => "ㅇㅇ(10.42) 나 남잔데 이런거 별로 10:20"
```
```python
# 댓글쓰기
dc_api.write_comment(board_id="programming", doc_id="149123", name="ㅇㅇ", pw="1234", contents="ㅇㅈ")
# 로그인 후 글쓰기
dc_api.login(id="SAMPLE_ID", pw="SAMPLE_PW")
dc_api.write_document(board_id="programming", title="흠..좋네", contents="기부니가 좋네")
dc_api.write_comment(board_id="programming", doc_id="149123", contents="설리")
```

# Dependency
python3 requests, lxml 

# Usage
Place dc_api.py in your working directory

or install through pip

```
pip3 install --user dc_api
```

```python
import dc_api

# full API
# for doc in dc_api.board(board_id="programming", num=5, start_page=2, skip_contents=True):

# full attributes of document and comment
for doc in dc_api.board(board_id="programming"):
    print(doc["id"])         # => "835027"
    print(doc["title"])      # => "땔감 벗어나는법.tip"
    print(doc["author"])     # => "ㅇㅇ(10.20)"
    print(doc["has_image"])  # => True
    print(doc["time"])       # => "1:41"
    print(doc["comment_num"])# => 3
    print(doc["voteup_num"]) # => 0
    print(doc["view_num"])   # => 14
    # Belows are None if parameter skip_contents=True
    print(doc["contents"])   # => "자바를 한다" 
    print(doc["imgs"])       # => ["http://static.dcinside.com/1o2i3joie", ...]
    print(doc["comments"])   # => generator
    for com in doc["comments"]:
        print(com["id"])        # => "123123"
        print(com["parent_id"]) # => "123122"
        print(com["time"])      # => "1:55"
        print(com["author"])    # => "ㅇㅇ(192.23)"
        print(com["contents"])  # => "개솔 ㄴㄴ"
        if com["dccon"]: 
            print(com["dccon"]) # => "http://dcimg5.dcinside.com/dccon.php?...."

        
# print document contents, images, and comments
contents, images, comments = dc_api.document(board_id="programming", doc_no="835027")
print(contents, images, comments)
# => "ㅗㅜㅑ\nㅗㅜㅑ.. [imgsrc1, imgsrc2, ..] <generator>"

# write doc
doc_id = dc_api.write_document(board_id="programming",
                               name="점진적자살", pw="1234", 
                               title="제목", contents="내용")
# modify doc
doc_id = dc_api.modify_document(board_id="programming", doc_id=doc_id, 
                          name="얄파고", pw="1234", 
                          title="수정된 제목", contents="수정된 내용")

# delete doc
dc_api.remove_document(board_id="programming", doc_id=doc_id, pw="1234")

# write comment
com_id = write_comment(board_id="programming", doc_no=doc_no, 
                           name="점진적자살", pw="1234", contents="아님")
                          
'''(Under development)
# delete comment
dc_api.removeComment(board_id="programming", is_miner=False, doc_no=doc_no, 
                     comment_no=comment_no, pw="1234")

# upvote
dc_api.upvote(board_id="programming", is_miner=False, doc_no=doc_no)

# upvote many times(it needs openvpn)
dc_api.upvote(board_id="programming", is_miner=False, doc_no=doc_no, num=10)
'''

# login
# if you skip the sess parameter, it will use the default session(and it affects all other API calls that use default session)
sess = dc_api.get_session()
dc_api.login(id="", pw="", sess=sess)

# write doc with logined session
# if you have skiped sess parameter of login API, you should also skip following API's sess parameters
doc_id = dc_api.write_document(sess=sess, board_id="programming", 
                         title="제목", contents="내용")
                         
# modify doc with logined session
doc_id = dc_api.modify_document(sess=sess, board_id="programming", doc_id=doc_id,
                          title="수정된 제목", contents="수정된 내용")

# write comment with logined session
# if you have skiped sess parameter of login API, you should also skip following API's sess parameters
# write comment
com_id = write_comment(sess=sess, board_id="programming", doc_id=doc_id, 
                           name="점진적자살", pw="1234", contents="아님")
                          
'''(Under development)
# delete comment with logined session
dc_api.removeComment(sess=sess, board_id="programming", is_miner=False, 
                     doc_no=doc_no, comment_no=comment_no)
                     
# upvote with logined session
dc_api.upvote(board_id="programming", is_miner=False, doc_no=doc_no, sess=sess)

# logout
dc_api.logout(sess)
'''

```
