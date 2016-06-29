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

class CNOA():

    user_agent = 'Mozilla/5.0 (Windows; U; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) AdobeAIR/18.0'
    headers = {'User-Agent': user_agent}

    login_data = {'username': '',
        'password': '',
        'serverurl': ''
        }
    personal_info = {
            'username':'',
            'uid': ''
            }

    
    def __init__(self, notify):
        self.session = requests.Session()
        
        FORMAT = '%(asctime)s %(message)s'
    
        logging.basicConfig(filename='cnoa.log', format=FORMAT)
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        
        self.contacts_list = []
        self.group_list = []
        self.grp_memberlist = []
        self.msg_list = []
        self.server_url = ""
        self.notify = notify
        
        self.load_config()    
        
        self.daemon = daemon_thread(self)

    def __del__(self):
        self.daemon.stop()

    def load_config(self):
        f = codecs.open("config.json")
        config_data = f.read()
        f.close()
        user_data = json.loads(config_data)
        #print "%r" % user_data['user_name'].encode('utf-8')
        self.login_data['username'] = user_data['user_name'].encode('utf-8')
        self.login_data['password'] = user_data['user_password']
        self.login_data['serverurl'] = user_data['server_address']
    
        if not os.path.exists(os.getcwd() + "/log"):
            os.makedirs(os.getcwd() + "/log")
        if not os.path.exists(os.getcwd() + "/files"):
            os.makedirs(os.getcwd() + "/files")
        if not os.path.exists(os.getcwd() + "/img"):
            os.makedirs(os.getcwd() + "/img")

    def login(self):
        login_url = "/api/messagerv2/index.php?action=login&task=login"
        r = self.session.get(self.login_data['serverurl'] + "/i/", \
                headers=self.headers, stream=True)
        self.server_url = r.text
        print "Real Server IP : %s" % (self.server_url)
        r = self.session.post(self.server_url + login_url, \
                data=self.login_data, headers=self.headers, stream=True)
        ret = json.loads(r.text)
        print ret['msg']
        self.personal_info['username'] = ret['username']
        self.personal_info['uid'] = ret['uid']
        
        self.daemon.start()
        
        return ret['success']
    
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
    
    def get_contacts_list(self):
        return self.contacts_list

    def is_contact(self, uid):
        for it in self.contacts_list:
            if uid == int(it['uid']):
                return True
        return False
        
    def find_name_by_id(self, id_no):
        #print contacts_list
        if type(id_no) is str:
            id_no = int(id_no)
        for it in self.contacts_list:
            if id_no == int(it['uid']):
                return it['text']
        return None
    
    def find_id_by_name(self, name):
        #print contacts_list
        for it in self.contacts_list:
            if name == it['text']:
                return it['uid']
        return None


    def is_group(self, gid):
        for grp in self.group_list:
            if int(grp['gid']) == gid:
                return True
        return False
    
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
    def send_msg(self, msg_id, msg, msg_type):
        sendmsg_url = "/api/messagerv2/index.php?action=chat&task=send"

        msg_data = {"id": msg_id,
                "type": msg_type,
                "content": msg,
                "fontsize": "14px"}
        request = self.session.post(self.server_url + sendmsg_url, \
                data=msg_data, headers=self.headers)
        msg_data["posttime"] = time.strftime("%Y-%m-%d %H:%M:%S")
        msg_data["fuid"] = msg_data["id"]
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
            recent_list.append(chat_id)
        print recent_list
        return recent_list
    
    def save_message(self, msg):
        if msg['type'] == "person":
            uid = ""
            if msg.has_key("fname"):
                uid = msg['fuid']
            elif msg.has_key("id"):
                uid = msg['id']
            f = open("log/user-" + str(uid) + ".json", "a+")
            f.write(json.dumps(msg))
            f.write("\n")
            f.close()
        elif msg['type'] == "group":
            f = open("log/group-" + str(msg['gid']) + ".json", "a+")
            f.write(json.dumps(msg))
            f.write("\n")
            f.close()

    def send_file(self, uid, file_path):
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

        request = self.session.get(self.server_url + get_grouplist_url,\
                headers=self.headers)
        group_json = json.loads(request.text)
        for grp in group_json['data']:
            self.group_list.append(grp)
            print "gid: %s name: %s" % (grp['gid'], grp['name'])
    
    def get_group_list(self):
        return self.group_list

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
            logging.info(data)
            if data.has_key("ol"):
                online_status =  data["ol"]
                #print online_status
                for p in online_status:
                    for i in self.cnoa.contacts_list:
                        if p[0] == i["uid"]:
                            i["iconCls"] = "icon-tree-im-online"
                
            elif data.has_key("hh"):
                msg = data.get("hh")
                for it in msg:
                    if it['type'] == "person":
                        print "%s" % it
                        #print type(it['content'])
                         
                        if type(it['content']) is dict:
                            # recv files
                            file_json = it['content']
                            print file_json
                            r = self.cnoa.session.get(self.cnoa.server_url + "/api/messagerv2/?action=file&task=dlload&id=" + str(file_json['id']), headers=self.cnoa.headers, allow_redirects=False)
                            file_url = r.headers['location']
                            file_url = file_url[5:len(file_url)]
                            print file_url
                            
                            r = self.cnoa.session.get(self.cnoa.server_url + file_url, headers=self.cnoa.headers)
                            self.cnoa.save_file(file_json['name'], r.content)

                            datas = {
                                    "fileid": file_json["id"],
                                    "historyid": it['id']
                                    }
                            r = self.cnoa.session.get(self.cnoa.server_url + "/api/messagerv2/?action=file&task=downcomplete", headers=self.cnoa.headers, data=datas)
                            print r
                            
                            self.cnoa.notify.write_notify(
                                    self.cnoa.find_name_by_id(it['fuid']), 
                                    file_json['name'])
                        elif re.findall(r"(\[\^img\^\]).(src\=\".*\")(>)", it['content']):
                            pic_content =  re.findall(r"(\[\^img\^\]).(src\=\".*\")(>)", it['content'])
                            #pass
                            pic_content = pic_content[0]
                            print len(pic_content), pic_content 
                            # recv pictures
                            file_url = re.findall(r"(file\/\w*\/\w*\/\w*\/\w*\/)", pic_content[1])
                            file_name = re.findall(r"(\d*_\d*\.[a-zA-Z]*)", pic_content[1])
                            # remove ">
                            #file_url = file_url[0][0:len(file_url) - 3]
                            file_url = file_url[0] 
                            file_name = file_name[0]
                            print file_url, file_name
                            # get file and save it to local
                            r = self.cnoa.session.get(self.cnoa.server_url + "/" + file_url + file_name, headers=self.cnoa.headers, stream=True)
                            self.cnoa.save_picture(file_name, r.content)
                            
                            self.cnoa.notify.write_notify(
                                    self.cnoa.find_name_by_id(it['fuid']), 
                                    it['content'])
                            
                        elif type(it['content']) is unicode:
                            #print it['content']
                            
                            self.cnoa.notify.write_notify(
                                    self.cnoa.find_name_by_id(it['fuid']), 
                                    it['content'])
                            
                        self.cnoa.msg_list.append(it)
                        self.cnoa.save_message(it)
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
                            r = self.cnoa.session.get(self.cnoa.server_url + "/" + file_url, headers=self.cnoa.headers, stream=True)
                            self.cnoa.save_picture(file_name[0], r.content)

                        self.cnoa.msg_list.append(it)
                        self.cnoa.save_message(it)
            elif data.has_key("xx"):
                xx = data.get("xx")
                #print xx
                pass
            time.sleep(2)


