# -*- coding: utf-8 -*-
import json
import time
import logging
import cmd
import threading
import os
import sys
import operator
import dbus

from PySide import QtGui, QtCore
import cnoa

"""
config.json
{
    "user_name": username,
    "user_password": password,
    "server_address": server_url
}
"""

notify = None

get_tasklist = "/api/messagerv2/index.php?action=group&task=getList"

contacts_list = []
cnoa_lib = None


msg_list = []

class CommandLineInterface(cmd.Cmd):
    global server_url, scan_url, headers, cnoa_lib
    
    def do_showlist(self, line):
        #print contacts_list
        contacts_list = cnoa_lib.get_contacts_list()
        for p in contacts_list:
            print "%s %s - %s" % (p['uid'], p['text'], p['iconCls'])
    
    def help_help(self):
        print "showlist - show current contacts list"

    def do_grouplist(self, line):
        for grp in cnoa_lib.get_group_list():
            print "gid: %s name: %s" % (grp['gid'], grp['name'])

    def do_memberlist(self, line):
        cnoa_lib.get_group_memberlist(line)
    
    def do_chatlog(self, line):
        prefix = ""
        dir_path = "log/"
        log_files = os.listdir(dir_path)
        file_mtime = []
        
        for fp in log_files:
            file_mtime.append(
                    dict(file_mtime=int(os.stat(dir_path + fp).st_mtime),
                file_path=fp))
        file_mtime.sort(key=operator.itemgetter('file_mtime'), reverse=True)
        print file_mtime
        #print log_files
        idx = int(raw_input("choose one:"))
        fp = open(dir_path + file_mtime[idx]['file_path'])
        for line in fp.readlines():
            if line != "":
                data = json.loads(line)
                #print data
                print cnoa_lib.find_name_by_id(data['fuid']), data['posttime'], data['content']

    def do_msglist(self, line):
        global msg_list
        print msg_list
        i = 0
        for it in msg_list:
            if it['type'] == "person":
                print "{MSG No%d} [%s] %s\r\n%s\r\n" % (i, cnoa_lib.find_name_by_id(it['fuid']), it['posttime'], it['content'])
            elif it['type'] == "group":
                print "{MSG No%d} [%s - %s] %s\r\n%s\r\n" % (i, it['gid'], cnoa_lib.find_name_by_id(it['fuid']), it['posttime'], it['content'])
            i += 1
    def do_sendfile(self, line):
        file_path = raw_input("Please input file path:")

        cnoa_lib.send_file(line, file_path)

    def do_checkin(self, line):
        cnoa_lib.check_in()

    def do_reply(self, line):
        global msg_list
        msg_id = int(line)
        print msg_list[msg_id]
        
        msg = raw_input("Please input message:")

        if msg_list[msg_id]['type'] == "person":
            cnoa_lib.send_msg(msg_list[msg_id]['fuid'], msg, "person")
        elif msg_list[msg_id]['type'] == "group":
            cnoa_lib.send_msg(msg_list[msg_id]['gid'], msg, "group")

    def do_sendmsg(self, line):
        msg_id = int(line)
        
        msg = raw_input("Please input message :")
        cnoa_lib.send_msg(msg_id, msg, "person")

    def do_sendgroup(self, line):
        msg_id = int(line)
        
        msg = raw_input("Please input message :")
        cnoa_lib.send_msg(msg_id, msg, "group")

    def do_EOF(self, line):
        return True

class KNotify:
    knotify = None
    def __init__(self):
        self.knotify = dbus.SessionBus().get_object("org.kde.knotify", "/Notify")
    def write_notify(self, title, text):
        #print title, text
        self.knotify.event("warning", "kde", [], title, 
                text, [], [], 0, 0,
                dbus_interface="org.kde.KNotify")

if __name__ == '__main__':

    notify = KNotify()
    
    cnoa_lib = cnoa.CNOA(notify)
    #cnoa_lib.load_config()

    if not cnoa_lib.login():
        sys.exit()
    
    cnoa_lib.fetch_contacts_list()
    cnoa_lib.fetch_group_list()
    
    CommandLineInterface().cmdloop()
    
