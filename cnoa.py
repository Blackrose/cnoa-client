# -*- coding: utf-8 -*-

import os
import re
import time
import json
import codecs
import logging
import threading
import requests
import operator
from blinker import signal

class CNOA():
    log_updated = signal("log_updated")
    sig_recv_msg = signal("recv_msg")
    user_agent = "Mozilla/5.0 (Windows; U; en-US) " \
            "AppleWebKit/533.19.4 (KHTML, like Gecko) AdobeAIR/18.0"
    headers = {'User-Agent': user_agent}

    login_data = {'username': '',
        'password': '',
        'serverurl': ''
        }
    personal_info = {
            'username':'',
            'uid': ''
            }
     
    
    def __init__(self, notify=None):
        self.session = requests.Session()
        
        FORMAT = '%(asctime)s %(message)s'
    
        logging.basicConfig(filename='cnoa.log', format=FORMAT)
        logging.getLogger().setLevel(logging.DEBUG)
        self.loger = logging.getLogger("requests.packages.urllib3")
        self.loger.setLevel(logging.DEBUG)
        self.loger.propagate = True
        
        self.contacts_list = []
        self.group_list = []
        self.grp_memberlist = []
        self.msg_list = []
        self.server_url = ""
        
        self.load_config()    
        
        self.daemon = daemon_thread(self)

    def __del__(self):
        self.daemon.stop()

    def emit_recv_msg(self, title, content):
        #print title, content
        self.sig_recv_msg.send(self, title=title, content=content)

    def load_config(self):
        f = codecs.open("config.json")
        config_data = f.read()
        f.close()
        user_data = json.loads(config_data)
        #print "%r" % user_data['user_name'].encode('utf-8')
        self.login_data['username'] = user_data['user_name'].encode('utf-8')
        self.login_data['password'] = user_data['user_password']
        self.login_data['serverurl'] = user_data['server_address']
        self.login_data['serverport'] = user_data['server_port']
    
        if not os.path.exists(os.getcwd() + "/log"):
            os.makedirs(os.getcwd() + "/log")
        if not os.path.exists(os.getcwd() + "/files"):
            os.makedirs(os.getcwd() + "/files")
        if not os.path.exists(os.getcwd() + "/img"):
            os.makedirs(os.getcwd() + "/img")

    def login(self):
        login_url = "/api/messagerv2/index.php?action=login&task=login"
        if not self.login_data['serverport']:
            r = self.session.get(self.login_data['serverurl'] + "/i/", \
                    headers=self.headers, stream=True)
            self.server_url = r.text
        else:
            self.server_url = self.login_data['serverurl'] + ':' + self.login_data['serverport']
        print "Real Server IP : %s" % (self.server_url)
        r = self.session.post(self.server_url + login_url, \
                data=self.login_data, headers=self.headers, stream=True)
        ret = json.loads(r.text)
        print ret['msg']
        self.personal_info['username'] = ret['username']
        self.personal_info['uid'] = ret['uid']
        
        self.daemon.start()
        
        return ret['success']
    
    def handler_contacts_online(self, status_list):
        for i in self.contacts_list:
            i["iconCls"] = "icon-tree-im-offline"
        
        for p in status_list:
            for i in self.contacts_list:
                if p[0] == i["uid"]:
                    i["iconCls"] = "icon-tree-im-online"
    
    def handler_recv_file(self, data_json):
        # recv files
        """
        file_json = {
            'from': 'file', 
            'name': 'abc.txt', 
            'fuid': 'sender-id', 
            'tuid': 'receiver-id', 
            'type': 'receive', 
            'id': message-id, 
            'size': file-size}
        """
        file_json = data_json['content']
        #print file_json
        r = self.session.get(self.server_url + 
                "/api/messagerv2/?action=file&task=dlload&id=" + 
                str(file_json['id']), headers=self.headers, allow_redirects=False)
        file_url = r.headers['location']
        file_url = file_url[5:len(file_url)]
        #print file_url
        
        r = self.session.get(self.server_url + file_url, headers=self.headers)
        self.save_file(file_json['name'], r.content)

        # Download complete response to server
        datas = {
                "fileid": file_json["id"],
                "historyid": data_json['id']
                }
        r = self.session.get(self.server_url + "/api/messagerv2/?action=file&task=downcomplete", headers=self.headers, data=datas)
        
        uname = self.find_name_by_id(data_json['fuid'])
        print "[ReceiveMSG] %s: Send file %s(%d bytes)" %(uname, 
                file_json['name'], file_json['size'])
        self.emit_recv_msg(self.find_name_by_id(data_json['fuid']), file_json['name'])

    def handler_recv_msg(self, data_json):
        """
        Receive message, also includes picture and emoji
        file url: [^img^] src="file/common/imsnapshot/year/month/file_name.jpg">
        emoji url: [^img^] src="/resources/images/face_active/file_name.gif">
        """

        msg_body = data_json['content'] = data_json['content'].replace('[^img^]', '<img')

        pic_content =  re.findall(r"(<img src=\"file\/\w*\/\w*\/\w*\/\w*\/.*>)", data_json['content'])
        if len(pic_content):
            pic_content = pic_content[0]
            #print len(pic_content), pic_content 
            # recv pictures
            file_url = re.findall(r"(file\/\w*\/\w*\/\w*\/\w*\/)", pic_content)
            file_name = re.findall(r"(\d*_\d*\.[a-zA-Z]*)", pic_content)

            file_url = file_url[0]
            file_name = file_name[0]
            print file_url, file_name
            # get file and save it to local
            r = self.session.get(self.server_url + "/" + file_url + file_name, 
                    headers=self.headers, stream=True)
            self.save_picture(file_name, r.content)

        emoji_list = re.findall(r"<img src=\"\/resources\/images\/face_active\/[a-z].\.gif\">", msg_body)

        # remove ">
        #file_url = file_url[0][0:len(file_url) - 3]
        
        #print it['fuid'], it['content']
        uname = self.find_name_by_id(data_json['fuid'])
        if data_json['type'] == "person":
            print "[ReceiveMSG] %s: %s" %(uname, data_json['content'])
        elif data_json['type'] == "group":
            grp_name = self.find_name_by_gid(data_json['gid'])
            print "[ReceiveMSG] Group %s(%s) by %s: %s" % (
                    grp_name, data_json['gid'], uname, data_json['content'])
        self.emit_recv_msg(uname, data_json['content'])
 
    def fetch_contacts_list(self):
        query_list = ['CNOA_main_struct_list_tree_node_1']

        for i in query_list:
            list_dt = self.get_list(i)
            list_user = self.parser_json(list_dt)
            for item in list_user:
                if item['leaf'] == False:
                    query_list.append(item['id'])

    def get_list(self, item_id):
        #print "get Contacts list"
        get_contactlist_url = "/index.php?app=communication&func=im&version=50008&action=index&task=getAllUserListsInDeptTree"
        node_data = {'node': item_id}

        request = self.session.post(self.server_url + get_contactlist_url, \
                data=node_data, headers=self.headers)
        user_list = request.text
        return user_list

    def parser_json(self, data):
        ddata = json.loads(data)
        #print ddata
        #print ddata[0]['text']
        for i in ddata:
            if i['leaf']:
                print i['uid'], i['text'], i['iconCls']
                
                # remove <span style='color:#999'></span>
                if i['uid'] == self.personal_info['uid']:
                    i['text'] = self.personal_info['username']
                self.contacts_list.append(i)
            else:
                print i['selfid'], i['text']

        return ddata
    
    def get_chat_history(self, uid, idtype):
        history_url = "/api/messagerv2/index.php?action=chat&task=getHistory"
        form_data = {'type': idtype,
                "uid": uid}

        request = self.session.post(self.server_url + history_url, \
                data=form_data, headers=self.headers)
        history_list = request.text
        return history_list
    
    def get_contacts_list(self):
        return self.contacts_list

    def is_contact(self, uid):
        for it in self.contacts_list:
            if uid == int(it['uid']):
                return True
        return False
     
    def find_name_by_gid(self, gid_no):
        if not (type(gid_no) is int):
            guid = int(gid_no)
        else:
            guid = gid_no
        for it in self.group_list:
            #print "%r, %r" %(uid, it)
            if guid == int(it['gid']):
                return it['name']
        return None
    
   
    def find_name_by_id(self, id_no):
        if not (type(id_no) is int):
            uid = int(id_no)
        else:
            uid = id_no
        for it in self.contacts_list:
            #print "%r, %r" %(uid, it)
            if uid == int(it['uid']):
                return it['text']
        return None
    
    def find_id_by_name(self, name):
        #print contacts_list
        for it in self.contacts_list:
            if name == it['text']:
                return it['uid']
        for grp in self.group_list:
            if grp['name'] == name:
                return grp['gid']
        return None


    def is_group(self, gid):
        for grp in self.group_list:
            if int(grp['gid']) == gid:
                return True
        return False
    
    def is_user(self, uid):
        for user in self.contacts_list:
            if int(user['uid']) == uid:
                return True
        return False

    """
    Return: 0 is none, 1 is user, 2 is group
    """
    def get_type(self, obj):

        for it in self.contacts_list:
            if type(obj) is str or type(obj) is unicode:
                if obj == it['text']:
                    return 1
            elif type(obj) is int:
                if obj == int(it['uid']):
                    return 1
        for grp in self.group_list:
            if type(obj) is str or type(obj) is unicode:
                if grp['name'] == obj:
                    return 2
            elif type(obj) is int:
                if int(grp['gid']) == obj:
                    return 2
        return 0

    def get_noticelist(self):
        get_notice_url = "/api/messagerv2/index.php?action=notice&task=getNoticeList"

        request = self.session.get(self.server_url + get_notice_url, headers=self.headers)
        print "GetNoticeList: %s" %request.text
     
    def check_in(self):
        get_time_url = "/index.php?app=att&func=person&action=register&task=getRegisterTime"
        add_register_time_url = "/index.php?app=att&func=person&action=register&task=addChecktime"
                            
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

        r = self.session.get(self.server_url + get_time_url, headers=self.headers)
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

        r = self.session.post(self.server_url + add_register_time_url, headers=self.headers, data=check_in_data)
        ret_json = json.loads(r.text)
        
        if ret_json.has_key("success"):
            print ret_json['msg']
        elif ret_json.has_key("failure"):
            print ret_json['msg']

    def send_msg(self, msg_id, msg, msg_type):
        """
        send message to person or group
        msg_id : id of message to people or group
        msg : message content
        msg_type : "person" or "group"
        """
        if not msg_id:
            print "The user/group id is needed!"
            return
        elif not self.is_user(int(msg_id)) and msg_type == "person":
            print "The user id doesn't exist!"
            return
        elif not self.is_group(int(msg_id)) and msg_type == "group":
            print "The group id doesn't exist!"
            return
        sendmsg_url = "/api/messagerv2/index.php?action=chat&task=send"

        msg_data = {"id": msg_id,
                "type": msg_type,
                "content": msg,
                "fontsize": "14px"}
        request = self.session.post(self.server_url + sendmsg_url, \
                data=msg_data, headers=self.headers)
        msg_data["posttime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        msg_data["fuid"] = int(self.personal_info['uid'])
        if msg_type == "group":
            msg_data['gid'] = msg_id

        self.save_message(msg_data)
        print "SendMsg: %s" %request.text
    
    def get_recentchat_list(self):

        dir_path = "log/"
        log_files = os.listdir(dir_path)
        file_mtime = []
        
        for fp in log_files:
            file_mtime.append(
                    dict(file_mtime=int(os.stat(dir_path + fp).st_mtime),
                file_path=fp))
        file_mtime.sort(key=operator.itemgetter('file_mtime'), reverse=True)
        print file_mtime
        recent_list = []
        for item in file_mtime:
            chat_id = item['file_path']
            if chat_id[4] == '-':
                chat_id = (chat_id.split('user-'))[1]
                chat_id = (chat_id.split('.json'))[0]
            elif chat_id[5] == '-':
                chat_id = (chat_id.split('group-'))[1]
                chat_id = (chat_id.split('.json'))[0]
            recent_list.append(dict(cid=chat_id, name=self.find_name_by_id(chat_id)))
        print recent_list
        return recent_list
    
    def save_message(self, msg):

        uid = ""
        if msg['type'] == "person":
            if msg.has_key("fname"):
                uid = msg['fuid']
            elif msg.has_key("id"):
                uid = msg['id']
            f = open("log/user-" + str(uid) + ".json", "a+")
            f.write(json.dumps(msg))
            f.write("\n")
            f.close()
        elif msg['type'] == "group":
            uid = str(msg['gid'])
            f = open("log/group-" + str(msg['gid']) + ".json", "a+")
            f.write(json.dumps(msg))
            f.write("\n")
            f.close()
        self.log_updated.send(int(uid))

    def send_file(self, uid, file_path):
        """
        Send file to user
        """
        if not uid or not self.is_user(int(uid)):
            print "The user id doesn't exist!"
            return
        if not os.path.exists(file_path):
            print "The file doesn't exist!"
            return
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
        request = self.session.post(self.server_url + sendfile_url, \
                data=data, headers=self.headers, files=files)
        print "SendFiles: %s" % request.text

    def fetch_group_list(self):
        get_grouplist_url = "/api/messagerv2/index.php?action=group&task=getList"
        del self.group_list[:]
        request = self.session.get(self.server_url + get_grouplist_url,\
                headers=self.headers)
        group_json = json.loads(request.text)
        for grp in group_json['data']:
            self.group_list.append(grp)
            print "gid: %s name: %s" % (grp['gid'], grp['name'])
    
    def get_group_list(self):
        return self.group_list
    
    def create_group(self, name, user_list):
        create_group_url = "/api/messagerv2/index.php?action=group&task=addedit"
        user_list = json.dumps(user_list)
        group_data = {
                'uids': user_list,
                'gid': "0",
                'type': "add",
                'name': name
                }
        print group_data
        request = self.session.post(self.server_url + \
                create_group_url, \
                headers=self.headers, data=group_data)
        ret = json.loads(request.text)
        print ret['msg']
        self.fetch_group_list()
        if ret.has_key('success'):
            return True
        elif ret.has_key('failure'):
            return False
    
    def remove_group(self, gid):
        """
        Remove an group
        gid : str
        """
        remove_group_url = "/api/messagerv2/index.php?action=group&task=remove"
        group_data = {
                'gid': gid
                }
        request = self.session.post(self.server_url + \
                remove_group_url, \
                headers=self.headers, data=group_data)
        ret = json.loads(request.text)
        print ret
        print ret['msg']
        self.fetch_group_list()
        if ret.has_key('success'):
            return True
        elif ret.has_key('failure'):
            return False
    
    def quit_group(self, gid):
        """
        Quit form an group
        gid : str
        """
        remove_group_url = "/api/messagerv2/index.php?action=group&task=quit"
        group_data = {
                'gid': gid
                }
        request = self.session.post(self.server_url + \
                remove_group_url, \
                headers=self.headers, data=group_data)
        ret = json.loads(request.text)
        self.fetch_group_list()
        print ret['msg']
        if ret.has_key('success'):
            return True
        elif ret.has_key('failure'):
            return False

    def get_group_memberlist(self, gid):
        get_group_memberlist_url = "/api/messagerv2/index.php?action=group&task=loadMemberList"
        group_data = {
                'gid': gid
                } 
        request = self.session.post(self.server_url + \
                get_group_memberlist_url, \
                headers=self.headers, data=group_data)
        member_data = json.loads(request.text)
        grp_memberlist = []
        for mb in member_data['data']:
            self.grp_memberlist.append(mb)
            print "gid: %s name: %s uid: %s" % (mb['gid'], mb['name'], mb['uid'])
    
    def save_file(self, file_name, file_content):
        f = open("files/" + file_name, "w+")
        f.write(file_content)
        f.close

    def save_picture(self, file_name, file_content):
        f = open("img/" + file_name, "w+")
        f.write(file_content)
        f.close

class daemon_thread(threading.Thread):
    def __init__(self, cnoa):
        threading.Thread.__init__(self)
        self.cnoa = cnoa

    def run(self):
        #global server_url, headers, msg_list, notify
        scan_url = "/api/messagerv2/index.php?action=scan"
        print self.cnoa.server_url 
        while True:
            r = self.cnoa.session.post(self.cnoa.server_url + scan_url, \
                    headers=self.cnoa.headers, stream=True)
            data = r.text
            try:
                data = json.loads(data)
            except ValueError, e:
                continue
            #print data
            self.cnoa.loger.debug(data)
            if data.has_key("ol"):
                online_status =  data["ol"]
                #print online_status
                self.cnoa.handler_contacts_online(online_status)

            elif data.has_key("hh"):
                msg = data.get("hh")
                for it in msg:
                    if it['type'] == "person":
                        self.cnoa.loger.debug("%r", it)
                        self.cnoa.loger.debug("%s", it['content'])
                         
                        if type(it['content']) is dict:
                            # recv files
                            self.cnoa.handler_recv_file(it)
                        elif re.findall(r"(\[\^img\^\])", it['content']):
                            # Handle file and emoji
                            self.cnoa.handler_recv_msg(it)
                        elif type(it['content']) is unicode:
                            #print it['fuid'], it['content']
                            self.cnoa.handler_recv_msg(it)

                        self.cnoa.msg_list.append(it)
                        self.cnoa.save_message(it)
                    elif it['type'] == "group":
                        self.cnoa.loger.debug(it)
                        
                        self.cnoa.handler_recv_msg(it)
                        self.cnoa.msg_list.append(it)
                        self.cnoa.save_message(it)
            elif data.has_key("xx"):
                xx = data.get("xx")
                #print xx
                pass
            time.sleep(1)


