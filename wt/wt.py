#!/usr/bin/env python
# coding: utf-8

# # 什麼樹？

# In[1]:


from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (
    MessageEvent, PostbackEvent,
    TextMessage, TextSendMessage, ImageMessage, ImageSendMessage,
    TemplateSendMessage, ImagemapSendMessage, LocationSendMessage, FlexSendMessage,
    QuickReply, QuickReplyButton,
    CameraAction, CameraRollAction, MessageAction, URIAction, PostbackAction)
from linebot.models.template import (
    ButtonsTemplate, CarouselTemplate, ConfirmTemplate, ImageCarouselTemplate)
from linebot.models.events import (FollowEvent)
import json
import requests
import re
from bauya import Bauya
from wtit import Wtit
import numpy as np
from sys import argv
from urllib.parse import parse_qs


# In[2]:


import pymysql as mysql
import time

class Wtbase:
    
    db = None
    
    def __init__(self, db_ip, db, db_id, db_pwd):
        if self.db is not None:
            self.db.close()
        self.db = mysql.connect(db_ip, db_id, db_pwd, db, autocommit=True)
    
    def addUser(self, user_id, display_name, picture_url):
        if user_id is None:
            print('[Wtbase:addUser] user_id is None')
            return
        
        d = '' if display_name is None else display_name
        p = 'https://i.imgur.com/g6GRWOx.png' if picture_url is None else picture_url
        sql = 'insert into wt_user (user_id, display_name, picture_url, admin) values (%s, %s, %s, %s)'
        try:
            self.db.ping(reconnect=True)
            with self.db.cursor() as cursor:
                data = cursor.execute(sql, (user_id, d, p, 1))
                if data != 1:
                    print('[Wtbase:addUser]', user_id, 'insert returned', data)
        except Exception as e:
            print('[Wtbase:addUser]', user_id, 'insert exception', e)
    
    def updateUsers(self, users):
        sql = 'update wt_user set display_name=%s, picture_url=%s where user_id=%s'
        try:
            self.db.ping(reconnect=True)
            with self.db.cursor() as cursor:
                for u in users:
                    p = 'https://i.imgur.com/g6GRWOx.png' if u[1] is None else u[1] 
                    data = cursor.execute(sql, (u[0], p, u[2]))
                    if data == 1:
                        print(f'[Wtbase:updateUsers] {u[2]} {u[0]} updated')
        except Exception as e:
            print('[Wtbase:updateUsers]', e)
    
    # kw:m for m_count, j for j_count
    def increase(self, user_id, kw='m'):
        if user_id is None or kw is None or len(kw) != 1 or kw not in 'mj':
            print('[Wtbase:increase] user_id or kw is invalid')
            return
        
        sql = f'update wt_user set {kw}_count={kw}_count+1, {kw}_last=now() where user_id=%s'
        try:
            self.db.ping(reconnect=True)
            with self.db.cursor() as cursor:
                data = cursor.execute(sql, (user_id))
                if data != 1:
                    print('[Wtbase:increase]', user_id, kw, 'update returned', data)
        except Exception as e:
            print('[Wtbase:increase]', user_id, kw, 'update exception', e)
    
    def _checkCriterion(self, user_id, criterion=1):
        if user_id is None:
            print('[Wtbase:_checkCriterion] user_id is None')
        else:
            sql = 'select admin from wt_user where user_id = %s and admin >= %s'
            try:
                self.db.ping(reconnect=True)
                with self.db.cursor() as cursor:
                    data = cursor.execute(sql, (user_id, criterion))
                    return data is 1          
            except Exception as e:
                print('[Wtbase:_checkCriterion]', user_id, 'select exception', e)
        
        return False
    
    def countUsage(self, user_id, criterion=1):
        if self._checkCriterion(user_id, criterion):
            sql1 = 'select count(user_id) from wt_user' # 用戶總數
            sql2 = 'select count(user_id) from wt_user where dt >= %s' # 今日新增用戶數
            #sql3 = 'select sum(j_count) from wt_user' # 使用 AI 總數
            sql3 = 'select count(user_id) from wt_user where j_last >= %s or m_last >= %s' # 今日使用用戶數
            try:
                with self.db.cursor() as cursor:
                    cursor.execute(sql1)
                    user_amt = cursor.fetchone()[0]
                    from time import strftime, localtime, time
                    today = strftime('%Y-%m-%d', localtime(time()))
                    cursor.execute(sql2, (today))
                    user_daily = cursor.fetchone()[0]
                    cursor.execute(sql3, (today, today))
                    usage_amt = cursor.fetchone()[0]
                    return user_amt, user_daily, usage_amt
            except Exception as e:
                print('[Wtbase:countUsage] select exception', e)
        
        return 0, 0, 0
    
    def markModel(self, user_id, model):
        if user_id is None or model is None:
            print('[Wtbase:markModel] user_id or model is None')
            return
        
        sql = 'update wt_user set model = %s where user_id = %s'
        try:
            self.db.ping(reconnect=True)
            with self.db.cursor() as cursor:
                data = cursor.execute(sql, (model, user_id))
                if data != 1:
                    print('[Wtbase:markModel]', user_id, model, 'update returned', data)
        except Exception as e:
            print('[Wtbase:markModel]', user_id, model, 'update exception', e)
        
    def getModel(self, user_id):
        if user_id is None:
            print('[Wtbase:getModel] user_id is None')
            return None
        
        sql = 'select model from wt_user where user_id = %s'
        try:
            self.db.ping(reconnect=True)
            with self.db.cursor() as cursor:
                data = cursor.execute(sql, (user_id))
                if data is 1:
                    return cursor.fetchone()[0]
                print('[Wtbase:getModel]', user_id, 'select returned', data)
        except Exception as e:
            print('[Wtbase:getModel]', user_id, 'select exception', e)
        
        return None
    
    def getUser(self, user_id):
        if user_id is None:
            print('[Wtbase:getUser] user_id is None')
        else:
            sql = 'select user_id, display_name, picture_url, admin, dt, m_count, m_last, j_count, j_last from wt_user where user_id=%s'
            try:
                self.db.ping(reconnect=True)
                with self.db.cursor() as cursor:
                    data = cursor.execute(sql, (user_id))
                    if data is 1:
                        return cursor.fetchone()
                    print('[Wtbase:getUser]', user_id, 'select returned', data)
            except Exception as e:
                print('[Wtbase:getUser]', user_id, 'select exception', e)
            
        return None
    
    def _countUsers(self):
        sql = 'select count(*) from wt_user'
        try:
            self.db.ping(reconnect=True)
            with self.db.cursor() as cursor:
                data = cursor.execute(sql)
                if data is 1 :
                    return (int)(cursor.fetchone()[0])
                print('[Wtbase:_countUsers] select returned', data)
        except Exception as e:
            print('[Wtbase:_countUsers] select exception', e)
        
        return -1
    
    def getUids(self):
        sql = 'select user_id from wt_user'
        try:
            self.db.ping(reconnect=True)
            with self.db.cursor() as cursor:
                data = cursor.execute(sql)
                if data > 0 :
                    uids = cursor.fetchall()
                    uids = [uid[0] for uid in uids] # due to previously returned uids structure is strange
                    return uids
                print('[Wtbase:getUids] select returned', data)
        except Exception as e:
            print('[Wtbase:getUids] select exception', e)
        
        return []
    
    # mode=last, first, most, msg, visit, usage
    def getUsers(self, user_id, mode='last', start=0, amount=10, criterion=1):
        if self._checkCriterion(user_id, criterion):
            amt = self._countUsers()
            if amt <= 0:
                return []
            last = 'select user_id, display_name, picture_url, dt, m_count+j_count from wt_user order by dt desc limit %s, %s'
            first = 'select user_id, display_name, picture_url, dt, j_count from wt_user order by dt asc limit %s, %s'
            most = 'select user_id, display_name, picture_url, dt, j_count from wt_user order by j_count desc limit %s, %s'
            msg = 'select user_id, display_name, picture_url, dt, m_count from wt_user order by m_count desc limit %s, %s'
            visit = 'select user_id, display_name, picture_url, (case when m_last > j_last then m_last else j_last end) as u_last, m_count+j_count as s from wt_user order by u_last desc limit %s, %s'
            usage = 'select user_id, display_name, picture_url, (case when m_last > j_last then m_last else j_last end) as u_last, m_count+j_count as s from wt_user order by s desc limit %s, %s'
            
            sql_dict = {'last': last, 'first': first, 'most': most, 'msg': msg, 'visit': visit, 'usage': usage}
            try:
                with self.db.cursor() as cursor:
                    data = cursor.execute(sql_dict[mode], (start, amount))
                    if data > 0 :
                        rows = cursor.fetchall()
                        ROWS = []
                        for r in rows:
                            R = list(r)
                            R[3] = f'{R[3].year:04d}{R[3].month:02d}{R[3].day:02d}'
                            R.append(amt)
                            ROWS.append(R)
                        return ROWS
                    print(f'[Wtbase:getUsers] {mode}, {start}, {amount} select returned {data}')
            except Exception as e:
                print(f'[Wtbase:getUsers] {mode}, {start}, {amount} select exception {e}')
        
        return []
    
    def reload(self, user_id, db_ip, db, db_id, db_pwd, criterion=2):
        if self._checkCriterion(user_id, criterion):
            if self.db is not None:
                self.db.close()
            self.db = mysql.connect(db_ip, db_id, db_pwd, db, autocommit=True)
            return True
        
        return False


# In[3]:


# Line Preprocessing
def load_chatbot_config(filename): 
    config = json.load(open(filename,'r'))
    line_bot_api = LineBotApi(config.get("Channel_access_token"))
    handler = WebhookHandler(config.get("Channel_secret"))
    return config, line_bot_api, handler


# In[4]:


# TextMessage Detector
def detect_json_array_to_new_message_array(fn):    
    with open(fn, encoding='utf8') as f:
        jsonArray = json.load(f)
    
    returnArray = []
    for jsonObject in jsonArray:
        message_type = jsonObject.get('type')
        if message_type == 'text':
            returnArray.append(TextSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'imagemap':
            returnArray.append(ImagemapSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'template':
            returnArray.append(TemplateSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'image':
            returnArray.append(ImageSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'sticker':
            returnArray.append(StickerSendMessage.new_from_json_dict(jsonObject))  
        elif message_type == 'audio':
            returnArray.append(AudioSendMessage.new_from_json_dict(jsonObject))  
        elif message_type == 'location':
            returnArray.append(LocationSendMessage.new_from_json_dict(jsonObject))
        elif message_type == 'flex':
            returnArray.append(FlexSendMessage.new_from_json_dict(jsonObject))    

    return returnArray


# In[ ]:


# user_id, display_name, picture_url, dt_string, j_count (or m_count), amt
def create_list(users, mode_str, start, length, callback=None):
    c = []

    for u in users:
        a = f'action=whoami&target={u[0]}'
        if callback:
            a += f'&callback={callback.replace("&", "^")}'
        
        t = {"type": "box", "layout": "baseline", "margin": "lg",
             "contents": [{"type": "icon", "url": u[2],"size": "3xl"},
                          {"type": "text", "text": u[1], "margin": "lg", "size": "md", "gravity": "center",
                           "weight": "bold", "color": "#FF00FF",
                           "action": {"type": "postback", "data": a}},
                          {"type": "text", "text": str(u[4]), "flex": 0, "size": "md", "align": "center",
                           "weight": "bold", "color": "#9D6439"},
                          {"type": "text", "text": u[3], "margin": "md", "flex": 0, "size": "md", "align": "end",
                           "color": "#8EC641"}
                         ]
            }
        c.append(t)
        
    h = f'用戶清冊  [{mode_str}]' if length == 0 else f'用戶清冊  [{mode_str}: {start}~{start+length-1}]'
    
    r = {"type": "flex", "altText": "用戶清冊",
         "contents": {"type": "bubble", "direction": "ltr",
                      "body": {"type": "box", "layout": "vertical",
                               "contents": [{"type": "text", "text": h, "size": "xl",
                                             "align": "start", "weight": "bold", "color": "#000000"},
                                            {"type": "separator", "margin": "xl"}
                                           ]
                              }
                     }
        }
    
    if c:
        r["contents"]["body"]["contents"] += c
    
    return r


# In[ ]:


def create_whoami(user): # id, name, url, admin, dt, m_count, m_last, j_count, j_last
    admin = ['素人', '管理員', '至尊管理員']
    
    r = {"type": "flex", "altText": "這誰？",
         "contents": {"type": "bubble",
                      "direction": "ltr",
                      "header": {"type": "box", "layout": "vertical",
                                 "contents": [{"type": "text", "text": "這誰？", "flex": 4, "size": "xl", "weight": "bold"}]},
                      "hero": {"type": "image", "url": user[2], "size": "xl", "aspectRatio": "1:1", "aspectMode": "fit"},
                      "body": {"type": "box", "layout": "vertical",
                               "contents": [{"type": "box", "layout": "baseline",
                                             "contents": [{"type": "text", "text": "名稱", "color": "#A9A9A9"},
                                                          {"type": "text", "text": user[1], "flex": 3, "size": "md",
                                                           "align": "start", "weight": "bold", "color": "#9D6439"}]},
                                            {"type": "box", "layout": "baseline",
                                             "contents": [{"type": "text", "text": "身份", "color": "#A9A9A9"},
                                                          {"type": "text", "text": admin[user[3]], "flex": 3,
                                                           "weight": "bold","color": "#8EC641"}]},
                                            {"type": "box", "layout": "baseline",
                                             "contents": [{"type": "text", "text": "加入時間", "color": "#A9A9A9"},
                                                          {"type": "text", "text": user[4].strftime('%Y/%m/%d-%H:%M:%S'),
                                                           "flex": 3, "weight": "bold","color": "#FF00FF"}]},
                                            {"type": "box", "layout": "baseline",
                                             "contents": [{"type": "text", "text": "瀏覽量", "color": "#A9A9A9"},
                                                          {"type": "text", "text": str(user[5]), "flex": 3,
                                                           "weight": "bold","color": "#FF00FF"}]},
                                            {"type": "box", "layout": "baseline",
                                             "contents": [{"type": "text", "text": "最近瀏覽", "color": "#A9A9A9"},
                                                          {"type": "text", "text": user[6].strftime('%Y/%m/%d-%H:%M:%S'),
                                                           "flex": 3, "weight": "bold","color": "#FF00FF"}]},
                                            {"type": "box", "layout": "baseline",
                                             "contents": [{"type": "text", "text": "辨識量", "color": "#A9A9A9"},
                                                          {"type": "text", "text": str(user[7]), "flex": 3,
                                                           "weight": "bold","color": "#FF00FF"}]},
                                            {"type": "box", "layout": "baseline",
                                             "contents": [{"type": "text", "text": "最近辨識", "color": "#A9A9A9"},
                                                          {"type": "text", "text": user[8].strftime('%Y/%m/%d-%H:%M:%S'),
                                                           "flex": 3, "weight": "bold","color": "#FF00FF"}]}
                                            
                                           ]}}}
    return r


# In[ ]:


def get_textmessage_reply(path, text, user_id, db, returnkey=False):
    result_arr = []
    prog = re.compile('<<[0-9a-zA-Z_\-]+>>')
    if prog.fullmatch(text) is None: # error handling should be later
        return None
    else:
        t = text[2:-2]
        fn = path + "/" + t + "/reply.json"
        result_arr = detect_json_array_to_new_message_array(fn)
    
    if returnkey:
        return result_arr, t
    
    return result_arr


# In[ ]:


cfg_filename = 'wt.json'
cfg, line_bot_api, handler = load_chatbot_config(cfg_filename)
app = Flask('wt', static_url_path = "/", static_folder = cfg['static_path'])
db = Wtbase(cfg['mysql_ip'], cfg['mysql_db'], cfg['mysql_id'], cfg['mysql_pwd'])
trees = ['AS', 'BJ', 'CC', 'DR', 'FM', 'KE', 'LF', 'MA', 'MI', 'MP', 'PC', 'RR', 'TC', 'TM']
trees_dict = {t:i for i, t in enumerate(trees)}
admin = ['素人', '管理員', '至尊管理員']
    
@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 萬用 TextMessage Replier
@handler.add(MessageEvent, message=TextMessage)
def handle_textmessage(event):
    #print(event.source.user_id)
    result_message_array = get_textmessage_reply(cfg['reply_path'], event.message.text, event.source.user_id, db)
    if result_message_array is not None:
        line_bot_api.reply_message(
            event.reply_token,
            result_message_array
        )

# 告知 handler，如果收到 FollowEvent，則做下面的方法處理
@handler.add(FollowEvent)
def reply_text_and_get_user_profile(event):   
    # 取出消息內 User 的資料並保存
    user_profile = line_bot_api.get_profile(event.source.user_id)
    db.addUser(user_profile.user_id, user_profile.display_name, user_profile.picture_url)
        
    # 將 richmenu 綁定在用戶身上
    line_bot_api.link_rich_menu_to_user(event.source.user_id, cfg['richmenu_id'])
        
    # 消息清單
    reply_message_list = [
        TextSendMessage(text="這是個全按鈕操控的樹木 AI 辨識機器人，不需輸入文字，就從底下控制台的三個按鈕開始，其中"+
                        "《這是什麼樹？》與《拍拍羊蹄甲》可立即進行樹木 AI 辨識，而《什麼樹？幕後》讓你探索這個 AI 辨識機器人"+
                        "的背景與維運機制。如果這是你的第一次，建議先從《什麼樹？控制台》逛逛《什麼樹？幕後》。")
    ]
    
    # 回覆文字消息與圖片消息
    line_bot_api.reply_message(event.reply_token, reply_message_list)

 # 回傳處理
@handler.add(PostbackEvent)
def process_postback_event(event):
    model_dict = {'classify_14tree': '影像辨識:14種樹', 'classify_8leaf': '影像辨識:8種葉',
                  'objdetect_14tree': '物件偵測:14種樹', 'objdetect_8leaf': '物件偵測:8種葉',
                  'classify_bauya': '影像辨識:羊蹄甲3種葉'}
    
    db.increase(event.source.user_id, 'm')
    q = parse_qs(event.postback.data)
    if 'model' in q:
        m = q.get('model')[0]
        
        if m in model_dict:
            cameraQuickRB = QuickReplyButton(action=CameraAction(label="拍照"))
            cameraRollQRB = QuickReplyButton(action=CameraRollAction(label="讀檔"))
            quickReplyList = QuickReply(items = [cameraRollQRB, cameraQuickRB])
            fn = '<<fn_' + m + '>>'
            quickReplyTextSendMessage = get_textmessage_reply(cfg['reply_path'], fn, event.source.user_id, db)
            quickReplyTextSendMessage[0].quick_reply = quickReplyList
            line_bot_api.reply_message(event.reply_token, quickReplyTextSendMessage)
            db.markModel(event.source.user_id, m)
    
    elif 'page' in q:
        page = q.get('page')[0]
        msg, key = get_textmessage_reply(cfg['reply_path'], page, event.source.user_id, db, True)
        msg = msg[0] # get_textmessage_reply() returned list
        
        if 'category' in q:
            cat = q.get('category')[0]
            if cat == 'trees': # page=<<AS>>&category=trees
                items = [QuickReplyButton(action=PostbackAction(label='<<', data='page=<<trees>>'))]
                k = trees_dict[key]
                if k > 0:
                    p = f'page=<<{trees[k-1]}>>&category=trees'
                    items.append(QuickReplyButton(action=PostbackAction(label='<', data=p)))
                if k < len(trees)-1:
                    f = f'page=<<{trees[k+1]}>>&category=trees'
                    items.append(QuickReplyButton(action=PostbackAction(label='>', data=f)))
                msg.quickReply = QuickReply(items=items)
                
            elif cat == 'leaves':
                pass
        
        line_bot_api.reply_message(event.reply_token, msg)
        
    elif 'action' in q:
        a = q.get('action')[0]
        msg = None
        
        if a == 'whoami':
            t = q.get('target')[0] if 'target' in q else event.source.user_id
            u = db.getUser(t)
            msg = FlexSendMessage.new_from_json_dict(create_whoami(u))
            if 'callback' in q:
                cb = (q.get('callback')[0]).replace('^', '&')
                msg.quickReply = QuickReply(items=[QuickReplyButton(action=PostbackAction(label='<', data=cb))])
        elif a == 'show_email':
            msg = TextSendMessage.new_from_json_dict(
                {'type': 'text', 'text': 'Enos Chou, feel free to contact me\ncatchsob@gmail.com'})
        elif a == 'count_usage':
            criterion = 1
            user_amt, user_today, usage_amt = db.countUsage(event.source.user_id, criterion=criterion)
            if user_amt is 0:
                msg = TextSendMessage.new_from_json_dict({"type": "text", "text": f'你還不是 {admin[criterion]}'})
            else:
                msg = TextSendMessage.new_from_json_dict(
                    {'type': 'text',
                     'text': f'用戶總數： {user_amt} 人\n今日新增： {user_today} 人\n今日使用： {usage_amt} 人'})
        elif a == 'list':
            AMOUNT = cfg['show_maxuser']
            alt = {'last':'註', 'visit':'訪', 'usage':'量'}
            criterion = 1
            mode = q.get('mode')[0]
            start = (int)(q.get('start')[0]) # must be cast to int, or it would be str
            users = db.getUsers(event.source.user_id, mode, start, AMOUNT, criterion)
            u_len = len(users)
            msg = FlexSendMessage.new_from_json_dict(create_list(users, alt[mode], start, u_len, event.postback.data))
            items = []
            if u_len > 0:
                if start > 0:
                    x = start - AMOUNT # cehck previus button
                    p = f'action=list&mode={mode}&start={x if x > 0 else 0}'
                    items.append(QuickReplyButton(action=PostbackAction(label='<', data=p)))
                    if x > 0: # check first page button
                        f = f'action=list&mode={mode}&start=0'
                        items.insert(0, QuickReplyButton(action=PostbackAction(label='<<', data=f)))
                if u_len == AMOUNT and (start+u_len < users[-1][-1]): # check next button
                    n = f'action=list&mode={mode}&start={start+u_len}'
                    items.append(QuickReplyButton(action=PostbackAction(label='>', data=n)))
                    nn = f'action=list&mode={mode}&start={AMOUNT*((users[-1][-1]-1)//AMOUNT)}'
                    items.append(QuickReplyButton(action=PostbackAction(label='>>', data=nn)))
                    
            for a in alt:
                if mode != a:
                    rb = QuickReplyButton(action=PostbackAction(label=alt[a], data=f'action=list&mode={a}&start=0'))
                    items.append(rb)
            msg.quickReply = QuickReply(items=items)
        elif a == 'reload':
            criterion = 2
            u = db.getUser(event.source.user_id) # user_id, display_name, picture_url, admin
            if u[3] >= criterion:
                if 'scope' in q:
                    s = q.get('scope')[0]
                    if s == 'db':
                        r = db.reload(event.source.user_id,
                                      cfg['mysql_ip'], cfg['mysql_db'], cfg['mysql_id'], cfg['mysql_pwd'], criterion)
                        desc = ['失敗!', '完成']
                        msg = TextSendMessage.new_from_json_dict({"type": "text", "text": f'DB重連{desc[r]}'})
                    elif s == 'profile':
                        pp = []
                        uids = db.getUids()
                        for uid in uids:
                            try:
                                p = line_bot_api.get_profile(uid) # sometimes failed due to UID not found by A
                                pp.append([p.display_name, p.picture_url, p.user_id])
                            except Exception as e1:
                                print(e1)
                                print(f'{uid} passed due to exception!')
                        db.updateUsers(pp)
                        msg = TextSendMessage.new_from_json_dict({"type": "text", "text": '更新用戶資料完畢'})
                    elif s == 'richmenu':
                        uids = db.getUids()
                        line_bot_api.link_rich_menu_to_users(uids, cfg['richmenu_id'])
                        msg = TextSendMessage.new_from_json_dict({"type": "text", "text": '重置圖文選單完畢'})
                else:
                    msg = get_textmessage_reply(cfg['reply_path'], '<<background>>', event.source.user_id, db)[0]
                    rb1 = QuickReplyButton(action=PostbackAction(label='重連DB', data='action=reload&scope=db'))
                    rb2 = QuickReplyButton(action=PostbackAction(label='更新用戶', data='action=reload&scope=profile'))
                    rb3 = QuickReplyButton(action=PostbackAction(label='重置選單', data='action=reload&scope=richmenu'))
                    msg.quickReply = QuickReply(items=[rb1, rb2, rb3])
            else:
                msg = TextSendMessage.new_from_json_dict({"type": "text", "text": f'你還不是 {admin[criterion]}'})
            
        line_bot_api.reply_message(event.reply_token, msg)
            
# 相片處理
@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event):
    mp = {'bb':['https://i.imgur.com/BB4Js7o.png', 'http://kplant.biodiv.tw/艷紫荊/艷紫荊.htm'],
          'bp':['https://i.imgur.com/kONyfcK.png', 'http://kplant.biodiv.tw/洋紫荊/洋紫荊.htm'],
          'bv':['https://i.imgur.com/bu4IE8I.png', 'http://kplant.biodiv.tw/羊蹄甲/羊蹄甲.htm']}
    
    # 取回用戶上傳的照片
    message_content = line_bot_api.get_message_content(event.message.id)
    b = None
    for chunk in message_content.iter_content():
        x = np.asarray(bytearray(chunk), dtype="uint8")
        b = x if b is None else np.append(b, x)
    
    msg = []
    m = db.getModel(event.source.user_id) #取出用戶設定的 model 型號
    if m == 'classify_bauya':
        _, cs, ms = bau_judge.judge(b) # AI 判定
        db.increase(event.source.user_id, 'j')
        msg.append(TextSendMessage(text=cs+' with '+ms))
        msg.append(ImageSendMessage(original_content_url=mp[cs[-2:]][0], preview_image_url=mp[cs[-2:]][0]))
        #msg.append(TextSendMessage(text=mp[cs[-2:]][1]))
    elif m in ['classify_14tree', 'classify_8leaf']:
        _, cs, ms = wtit_judge.judge(b, model_kw=m)
        db.increase(event.source.user_id, 'j')
        msg.append(TextSendMessage(text=cs+' with '+ms))
    elif m in ['objdetect_14tree', 'objdetect_8leaf']:
        p = cfg['static_path'] + '/output/' + event.message.id + '.jpg'
        wtit_judge.judgeYolo(b, p, model_kw=m)
        db.increase(event.source.user_id, 'j')
        full_p = 'https://' + cfg['server'] + '/output/' + event.message.id + '.jpg'
        msg.append(ImageSendMessage(original_content_url=full_p, preview_image_url=full_p))
    else:
        return # unknow model noted, should not happen, just return
        
    line_bot_api.reply_message(event.reply_token, msg)

bau_judge = Bauya()
wtit_judge = Wtit()


# In[ ]:


if __name__ == "__main__":
    app.run()


# In[ ]:




