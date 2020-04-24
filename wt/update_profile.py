import pymysql as mysql
from linebot import LineBotApi
# 什麼樹？  正式
Channel_access_token = 'oSELynYvrTO0WDVirb0rOwTudAvVsNY2FDgrwIKox8FkuPpj/imERNQq06fwlD4BA3IJicppTNjoRe7/Tk53pHYDF7FKIX7l3pCLJs3knbN8bJ7GZZSZ7I3upI5caINzCDAXMuiaVX5llrdf6+YtQgdB04t89/1O/w1cDnyilFU='

line_bot_api = LineBotApi(Channel_access_token)
db = mysql.connect('127.0.0.1', 'wt', 'wt', 'wt', autocommit=True)

sql1 = 'select user_id from wt_user' 
sql2 = 'update wt_user set display_name=%s, picture_url=%s where user_id=%s'

try:
    with db.cursor() as cursor:
        data = cursor.execute(sql1)
        users = cursor.fetchall()
        users = [x[0] for x in users]
        for u in users:
            print(u)
            try:
                p = line_bot_api.get_profile(u)
                data = cursor.execute(sql2, (p.display_name, p.picture_url, p.user_id))
                if data == 1:
                    print(f'{p.display_name} updated')
                else:
                    print(f'update {u} return {data}!')
            except Exception as e1:
                print(e1)
                print(f'{u} passed due to exception!')
                
except Exception as e:
    print(e)

db.close()
