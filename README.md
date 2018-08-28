# dcinside-python3-api
Deadly simple non official dcinside api for python3
```python
for doc in dc_api.board(board="programming"):
    print(doc["title"], doc["name"], doc["date"]) 
# => "땔감 벗어나는법.tip ㅇㅇ 1:41"
# => "왜 이거 안돼냐? ㅇㅇ 1:40"
# => ...
```

# Dependency
It has optional dependency openvpn. It is used when you call upvote function with arguement num>1.

# Usage
place dc_api.py in your working directory
```python
import dc_api

# print five recent documents in programming gallery of dcinside
for doc in dc_api.board(board="programming", is_miner=False):
    print(doc["doc_no"])     # => "835027"
    print(doc["title"])      # => "땔감 벗어나는법.tip"
    print(doc["name"])       # => "ㅇㅇ"
    print(doc["ip"])         # => "10.20"
    print(doc["date"])       # => "1:41"
    print(doc["comments"])   # => 3
    print(doc["votes"])      # => 0
    print(doc["views"])      # => 14

# full API
for doc in dc_api.board(board="programming", is_miner=False, num=5, start_page=2, include_contents=True, include_comments=True):
    print(doc["contents"])  # => "<div ..... </div>"
    print(doc["comments"])  # => <generator ... >
    # => this is generator. see below usage

# print five recent comments of doc in programming gallery of dcinside 
for doc in dc_api.comments(board="programming", is_miner=False, doc_no="835027", num=5):
    print(doc["comment_no"]) # => "110"
    print(doc["name"])       # => "morris"
    print(doc["contents"])   # => "요 4권만 읽으면 건물주 되기 가능??"
    print(doc["ip"])         # => ""
    print(doc["date"])       # => "2018.04.15 02:34:16"

# write doc
doc_no = dc_api.writeDoc(board="programming", is_miner=False, 
                         name="얄파고", password="1234", 
                         title="제목", contents="내용")
# modify doc
doc_no = dc_api.modifyDoc(board="programming", is_miner=False, 
                          name="얄파고", password="1234", 
                          title="수정된 제목", contents="수정된 내용")

# write comment
comment_no = writeComment(board="programming", is_miner=False, 
                          doc_no=doc_no, name="얄파고", password="1234", contents="테스트 댓글")
                          
# delete comment
dc_api.removeComment(board="programming", is_miner=False, 
                     doc_no=doc_no, comment_no=comment_no, password="1234")

# delete doc
dc_api.removeDoc(board="programming", is_miner=False, doc_no=doc_no, password="1234")

# upvote
dc_api.upvote(board="programming", is_miner=False, doc_no=doc_no)

# upvote many times(it needs openvpn)
dc_api.upvote(board="programming", is_miner=False, doc_no=doc_no, num=10)

# login
sess = dc_api.login(userid="", password="")

# write doc with logined session
doc_no = dc_api.writeDoc(sess=sess, board="programming", is_miner=False,                          
                         title="제목", contents="내용")
                         
# modify doc with logined session
doc_no = dc_api.modifyDoc(sess=sess, board="programming", is_miner=False, 
                          title="수정된 제목", contents="수정된 내용")

# write comment with logined session
comment_no = writeComment(sess=sess, board="programming", is_miner=False, 
                          doc_no=doc_no, contents="테스트 댓글")
                          
# delete comment with logined session
dc_api.removeComment(sess=sess, board="programming", is_miner=False, 
                     doc_no=doc_no, comment_no=comment_no)
                     
# upvote with logined session
dc_api.upvote(board="programming", is_miner=False, doc_no=doc_no, sess=sess)

# logout
dc_api.logout(sess)

```
