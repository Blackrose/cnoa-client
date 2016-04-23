# -*- coding: utf-8 -*-
import json
import codecs
import requests
import time
import logging

"""
config.json
{
    "user_name": username,
    "user_password": password,
    "server_address": server_url
}
"""

login_data = {'username': '',
        'password': '',
        #'serverurl': server_url
        'serverurl': ''
        }


def load_config():
    global login_data
    f = codecs.open("config.json")
    config_data = f.read()
    f.close()
    user_data = json.loads(config_data)
    #print "%r" % user_data['user_name'].encode('utf-8')
    login_data['username'] = user_data['user_name'].encode('utf-8')
    login_data['password'] = user_data['user_password']
    login_data['serverurl'] = user_data['server_address']


#server_url = "http://113.87.195.133:81"
server_url = "http://121.35.112.153:81"

scan_url = "/api/messagerv2/index.php?action=scan"
login_url = "/api/messagerv2/index.php?action=login&task=login"
get_tasklist = "/api/messagerv2/index.php?action=group&task=getList"

user_agent = 'Mozilla/5.0 (Windows; U; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) AdobeAIR/18.0'
headers = {'User-Agent': user_agent}

def cnoa_login(session):
    global is_login, login_url, headers, login_data
    r = session.post(server_url + login_url, data=login_data, headers=headers, stream=True)
    print r.text
    print "Cookies: %s " %r.cookies
    return True

contacts_list = []

def parser_json(data):
    global contacts_list
    ddata = json.loads(data)
    print ddata
    #print ddata[0]['text']
    for i in ddata:
        if i['leaf']:
            print i['uid'], i['text'], i['iconCls']
            contacts_list.append(i)
        else:
            print i['selfid'], i['text']

    return ddata

def find_name_by_id(id_no):
    global contacts_list
    #print contacts_list
    for it in contacts_list:
        if id_no == it['uid']:
            return it['text']
    return None

def get_list(session, item_id):
    global server_url, headers
    print "get Contacts list"
    get_contactlist = "/index.php?app=communication&func=im&version=50008&action=index&task=getAllUserListsInDeptTree"
    node_data = {'node': item_id}

    request = session.post(server_url + get_contactlist, data=node_data, headers=headers)
    user_list = request.text
    return user_list

def send_msg(session, uid, msg, msg_type):
    global server_url, headers
    sendmsg_url = "/api/messagerv2/index.php?action=chat&task=send"

    msg_data = {"id": uid,
            "type": msg_type,
            "content": msg,
            "fontsize": "14px"}
    request = session.post(server_url + sendmsg_url, data=msg_data, headers=headers)
    print "SendMsg: %s" %request.text

def get_noticelist(session):
    global server_url, headers
    get_notice_url = "/api/messagerv2/index.php?action=notice&task=getNoticeList"

    request = session.get(server_url + get_notice_url, headers=headers)
    print "GetNoticeList: %s" %request.text
    
query_list = ['CNOA_main_struct_list_tree_node_1']

if __name__ == '__main__':
    global query_list
    
    load_config()

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True

    session = requests.Session()
    
    if cnoa_login(session):
        print "Login Successful!"  
    else:
        print "Failed"

    print query_list
    for i in query_list:
        list_dt = get_list(session, i)
        list_user = parser_json(list_dt)
        for item in list_user:
            if item['leaf'] == False:
                query_list.append(item['id'])


    while True:
        r = session.post(server_url + scan_url, headers=headers, stream=True)
        data = r.text
        if data:
            #print json.loads(data)
            data = json.loads(data)
            if data.has_key("hh"):
                print "%r" %data
                msg = data.get("hh")
                print "%r" %msg
                for it in msg:

                    if it['type'] == "person":
                        print find_name_by_id(it['fuid'])
                        print "MSG [%s] %s\r\n%s\r\n" % (find_name_by_id(it['fuid']), it['posttime'], it['content'])
                        send_msg(session, it['fuid'], it['content'] + " kevin", "person")
                    elif it['type'] == "group":
                        print "[%s - %s] %s\r\n%s\r\n" % (it['gid'], find_name_by_id(it['fuid']), it['posttime'], it['content'])
            else:
                print data
         
        time.sleep(2)
        get_noticelist(session)

