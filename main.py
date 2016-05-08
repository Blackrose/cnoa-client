# -*- coding: utf-8 -*-
import json
import codecs
import requests
import time
import logging
import cmd
import thread
import re
import os
#from requests_toolbelt.multipart.encoder import MultipartEncoder

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
        'serverurl': ''
        }

server_url = ""

def load_config():
    global login_data, server_url
    f = codecs.open("config.json")
    config_data = f.read()
    f.close()
    user_data = json.loads(config_data)
    #print "%r" % user_data['user_name'].encode('utf-8')
    login_data['username'] = user_data['user_name'].encode('utf-8')
    login_data['password'] = user_data['user_password']
    login_data['serverurl'] = user_data['server_address']



scan_url = "/api/messagerv2/index.php?action=scan"
login_url = "/api/messagerv2/index.php?action=login&task=login"
get_tasklist = "/api/messagerv2/index.php?action=group&task=getList"

user_agent = 'Mozilla/5.0 (Windows; U; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) AdobeAIR/18.0'
headers = {'User-Agent': user_agent}

def cnoa_login(session):
    global is_login, login_url, headers, login_data, server_url
    r = session.get(login_data['serverurl'] + "/i/", headers=headers, stream=True)
    server_url = r.text
    print "Real Server IP : %s" % (server_url)
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

# --------------------------------
##
# @Synopsis send message to person or group
#
# @Param session : http client session key
# @Param msg_id : id of message to people or group
# @Param msg : message content
# @Param msg_type : "person" pr "group"
#
# @Returns 
# --------------------------------
def send_msg(session, msg_id, msg, msg_type):
    global server_url, headers
    sendmsg_url = "/api/messagerv2/index.php?action=chat&task=send"

    msg_data = {"id": msg_id,
            "type": msg_type,
            "content": msg,
            "fontsize": "14px"}
    request = session.post(server_url + sendmsg_url, data=msg_data, headers=headers)
    print "SendMsg: %s" %request.text

def send_file(session, uid, file_path):
    global server_url, headers
    sendfile_url = "/api/messagerv2/?action=file&task=upload&uid=" + uid
    filename = os.path.basename(file_path)
    """
    m = MultipartEncoder(
                    fields = {'Filename': filename,
                        'FILES': (filename, open(file_path, 'rb'), 'application/octet-stream'),
                        'Upload': 'Submit Query'
                        }
                    )
        
    request = session.post(server_url + sendfile_url, data=m, headers=headers)
    """
    data = {
            "Filename": filename,
            "Upload": "Submit Query"
            }
    files = {'FILES': open(file_path, 'rb')}
    request = session.post(server_url + sendfile_url, data=data, headers=headers, files=files)
    print "SendFiles: %s" % request.text

def check_in(session):
    global server_url, headers
    get_time = "/index.php?app=att&func=person&action=register&task=getRegisterTime"
    add_register_time = "/index.php?app=att&func=person&action=register&task=addChecktime"
                        
    check_in_data = {
            'num': '',
            'classes': '',
            'workType': '',
            'time': '',
            'stime': '',
            'etime': '',
            'recTime': '',
            'explain': '',
            'date': '',
            'nowTime': ''
            }

    r = session.get(server_url + get_time, headers=headers)
    response = json.loads(r.text)
    time_data = response['data']

    for i in time_data:
        print "%s ~ %s : %s" % (i['stime'], i['etime'], i['recTime'])
                                                     
    idx = int(raw_input("please input check-in idx:"))
    check_in_data['num'] = time_data[idx]['num']
    check_in_data['classes'] = time_data[idx]['classes']
    check_in_data['workType'] = time_data[idx]['workType']
    check_in_data['time'] = time_data[idx]['time']
    check_in_data['stime'] = time_data[idx]['stime']
    check_in_data['etime'] = time_data[idx]['etime']
    check_in_data['date'] = time_data[idx]['date']
    check_in_data['nowTime'] = time_data[idx]['nowTime']
    check_in_data['recTime'] = time_data[idx]['nowTime']

    print check_in_data

    r = session.post(server_url + add_register_time, headers=headers, data=check_in_data)
    ret_json = json.loads(r.text)
    if ret_json.has_key("success"):
        print ret_json['msg']
    elif ret_json.has_key("failure"):
        print ret_json['msg']


def get_noticelist(session):
    global server_url, headers
    get_notice_url = "/api/messagerv2/index.php?action=notice&task=getNoticeList"

    request = session.get(server_url + get_notice_url, headers=headers)
    print "GetNoticeList: %s" %request.text
    
query_list = ['CNOA_main_struct_list_tree_node_1']
msg_list = []

class CommandLineInterface(cmd.Cmd):
    global session, server_url, scan_url, headers
    
    def do_showlist(self, line):
        print contacts_list
        for p in contacts_list:
            print "%s %s - %s" % (p['uid'], p['text'], p['iconCls'])
    
    def help_help(self):
        print "showlist - show current contacts list"

    def do_chatlog(self, line):
        prefix = ""
        dir_path = "log/"
        log_files = os.listdir(dir_path)
        print log_files
        idx = int(raw_input("choose one:"))
        fp = open(dir_path + log_files[idx])
        for line in fp.readlines():
            if line != "":
                data = json.loads(line)
                #print data
                print find_name_by_id(data['fuid']), data['posttime'], data['content']
        #for it in data:
        #    print "[%s] %s\r\n%s\r\n" % (find_name_by_id(it['fuid']), it['posttime'], it['content'])

        """
            for it in msg:
                if it['type'] == "person":
                    print find_name_by_id(it['fuid'])
                    print "MSG [%s] %s\r\n%s\r\n" % (find_name_by_id(it['fuid']), it['posttime'], it['content'])
                    send_msg(session, it['fuid'], it['content'] + " kevin", "person")
                elif it['type'] == "group":
                    print "[%s - %s] %s\r\n%s\r\n" % (it['gid'], find_name_by_id(it['fuid']), it['posttime'], it['content'])
                    send_msg(session, it['gid'], it['content'] + " kevin", "group")
        """
    def do_msglist(self, line):
        global msg_list
        print msg_list
        i = 0
        for it in msg_list:
            if it['type'] == "person":
                print "{MSG No%d} [%s] %s\r\n%s\r\n" % (i, find_name_by_id(it['fuid']), it['posttime'], it['content'])
            elif it['type'] == "group":
                print "{MSG No%d} [%s - %s] %s\r\n%s\r\n" % (i, it['gid'], find_name_by_id(it['fuid']), it['posttime'], it['content'])
            i += 1
    def do_sendfile(self, line):
        global session
        
        file_path = raw_input("Please input file path:")

        send_file(session, line, file_path)
    def do_checkin(self, line):
        check_in(session)

    def do_reply(self, line):
        global msg_list
        msg_id = int(line)
        print msg_list[msg_id]
        
        msg = raw_input("Please input message:")

        if msg_list[msg_id]['type'] == "person":
            send_msg(session, msg_list[msg_id]['fuid'], msg, "person")
        elif msg_list[msg_id]['type'] == "group":
            send_msg(session, msg_list[msg_id]['gid'], msg, "group")

    def do_sendmsg(self, line):
        global msg_list
        msg_id = int(line)
        
        msg = raw_input("Please input message :")

        send_msg(session, msg_id, msg, "person")
        #send_msg(session, msg_list[msg_id]['gid'], msg, "group")



    def do_EOF(self, line):
        return True

def save_file(file_name, file_content):
    f = open("files/" + file_name, "w+")
    f.write(file_content)
    f.close

def save_picture(file_name, file_content):
    f = open("img/" + file_name, "w+")
    f.write(file_content)
    f.close

def save_message(msg):
    if msg['type'] == "person":
        f = open("log/user-" + msg['fuid'] + ".json", "a+")
        f.write(json.dumps(msg))
        f.write("\n")
        f.close()
    elif msg['type'] == "group":
        f = open("log/group-" + msg['gid'] + ".json", "a+")
        f.write(json.dumps(msg))
        f.write("\n")
        f.close()

def daemon_thread(threadName, session):
    global server_url, scan_url, headers, msg_list
    
    while True:
        r = session.post(server_url + scan_url, headers=headers, stream=True)
        data = r.text
        if data == "":
            continue
        data = json.loads(data)
        #print data
        if data.has_key("ol"):
            online_status =  data["ol"]
            #print online_status
            for p in online_status:
                for i in contacts_list:
                    if p[0] == i["uid"]:
                        i["iconCls"] = "icon-tree-im-online"
            
        elif data.has_key("hh"):
            msg = data.get("hh")
            for it in msg:
                if it['type'] == "person":
                    print "%s" % it
                     
                    if type(it['content']) is dict:
                        # recv files
                        file_json = it['content']
                        print file_json
                        r = session.get(server_url + "/api/messagerv2/?action=file&task=dlload&id=" + str(file_json['id']), headers=headers, allow_redirects=False)
                        file_url = r.headers['location']
                        file_url = file_url[5:len(file_url)]
                        print file_url
                        r = session.get(server_url + file_url, headers=headers)
                        save_file(file_json['name'], r.content)

                        datas = {
                                "fileid": file_json["id"],
                                "historyid": it['id']
                                }
                        r = session.get(server_url + "/api/messagerv2/?action=file&task=downcomplete", headers=headers, data=datas)
                        print r
                    elif type(it['content']) is str:
                        print it['content']
                    else:
                        pass
                        """
                        # recv pictures
                        file_url = re.findall(r"file\/common\/imsnapshot\/\S*", it['content'])
                        file_name = re.findall(r"(\d*_\d*\.[a-zA-Z]*)", file_url[0])
                        # remove ">
                        file_url = file_url[0][0:len(file_url) - 3]
                        print file_url, file_name
                        # get file and save it to local
                        r = session.get(server_url + "/" + file_url, headers=headers, stream=True)
                        save_picture(file_name[0], r.content)
                        """
                    
                    msg_list.append(it)
                    save_message(it)
                    #send_msg(session, it['fuid'], it['content'] + " kevin", "person")
                elif it['type'] == "group":
                    print it
                    #print "[%s - %s] %s\r\n%s\r\n" % (it['gid'], find_name_by_id(it['fuid']), it['posttime'], it['content'])
                    
                    file_url = re.findall(r"file\/common\/imsnapshot\/\S*", it['content'])
                    if file_url:
                        file_name = re.findall(r"(\d*_\d*\.[a-zA-Z]*)", file_url[0])
                        # remove ">
                        file_url = file_url[0][0:len(file_url) - 3]
                        print file_url, file_name
                    
                        # get file and save it to local
                        r = session.get(server_url + "/" + file_url, headers=headers, stream=True)
                        save_picture(file_name[0], r.content)

                    msg_list.append(it)
                    save_message(it)
                    #send_msg(session, it['gid'], it['content'] + " kevin", "group")
        elif data.has_key("xx"):
            xx = data.get("xx")
            #print xx
            pass
        time.sleep(2)



if __name__ == '__main__':
    global query_list, session
    
    load_config()
    """
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    """
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
    
    try:
        thread.start_new_thread(daemon_thread, ("daemon", session))
    except:
        print "Thread start failed!"
    
    CommandLineInterface().cmdloop()
    
