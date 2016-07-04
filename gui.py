# -*- coding: utf-8 -*-
import sys
import os
import time
import json
import operator
from PySide import QtGui, QtCore
import cnoa
import dbus

class ActivityLabel(QtGui.QLabel):
    clicked = QtCore.Signal(object)
    def __init__(self):
        super(ActivityLabel, self).__init__()
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self)

class TextInputWidget(QtGui.QTextEdit):
    commited = QtCore.Signal(str)
    def __init__(self):
        QtGui.QTextEdit.__init__(self)
    def keyPressEvent(self, event):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers & QtCore.Qt.ControlModifier and \
            (event.key() == QtCore.Qt.Key_Enter or \
            event.key() == QtCore.Qt.Key_Return):
            #print "send it"
            self.commited.emit(self.toPlainText())
            self.clear()

        return QtGui.QTextEdit.keyPressEvent(self, event)
class LeftWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.initUI()

    def initUI(self):
        self.setMaximumWidth(100)
        self.setMinimumWidth(100)
        
        self.middle_box = QtGui.QStackedLayout()
        self.setLayout(self.middle_box)

        self.recentchat_list = QtGui.QListWidget()
        self.user_list = QtGui.QListWidget()
        self.group_list = QtGui.QListWidget()

        self.recentchat_list.setStyleSheet("QListWidget{border: none;background-color: transparent;}")
        self.user_list.setStyleSheet("QListWidget{border: none;background-color: transparent;}")
        self.group_list.setStyleSheet("QListWidget{border: none;background-color: transparent;}")
        self.recentchat_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.user_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.group_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        #self.recentchat_list.setMaximumWidth(80)
        #self.recentchat_list.setMinimumWidth(50)
        
        #self.user_list.setMaximumWidth(100)
        #self.user_list.setMinimumWidth(100)
        
        #self.group_list.setMaximumWidth(100)
        #self.group_list.setMinimumWidth(100)

        #self.user_list.itemClicked.connect(self.slot_switch_content_widget)
        #self.recentchat_list.itemClicked.connect(self.switch_recentchat_widget)
        
        self.middle_box.addWidget(self.recentchat_list)
        self.middle_box.addWidget(self.user_list)
        self.middle_box.addWidget(self.group_list)

    def update_chat_list(self, recent_list):
        for rec in recent_list:
            self.recentchat_list.addItem(QtGui.QListWidgetItem(
                QtGui.QIcon("icons/user-icon.png"), rec['name']))


    def update_user_list(self, user_list):
        for usr in user_list:
            self.user_list.addItem(QtGui.QListWidgetItem(
                QtGui.QIcon("icons/user-icon.png"), usr['text']))
    
    def update_group_list(self, group_list):
        for grp in group_list:
            self.group_list.addItem(grp['name'])
    
    def change_widget(self, idx):
        self.middle_box.setCurrentIndex(idx)


class RightWidget(QtGui.QWidget):
    def __init__(self):
        #super(RightWidget, self).__init__()
        QtGui.QWidget.__init__(self)
        self.initUI()
    
    def initUI(self):
        self.content_wid = QtGui.QStackedLayout()
        self.setLayout(self.content_wid)
        
        # chating widget
        chat_widget = QtGui.QWidget()
        chat_layout = QtGui.QGridLayout()
        self.chat_display = QtGui.QTextEdit()
        self.chat_label = QtGui.QLabel()
        self.chat_label.setFixedHeight(40)
        self.chat_display.setReadOnly(True)
        self.chat_edit = TextInputWidget()
        #chat_layout.setColumnMinimumWidth(0, 200)
        #chat_layout.setRowMinimumHeight(0, 500)
        
        #chat_widget.setStyleSheet("QLabel {background-color: green;}")
        chat_layout.addWidget(self.chat_label, 0, 0)
        chat_layout.addWidget(self.chat_display, 1, 0)
        chat_layout.addWidget(self.chat_edit, 2, 0)
        chat_widget.setLayout(chat_layout)
        #chat_layout.setRowStretch(0, 1)
        chat_layout.setRowStretch(1, 6)
        chat_layout.setRowStretch(2, 2)

        chat_widget.setLayout(chat_layout)
        
        
        # userinfo widget
        userinfo_widget = QtGui.QWidget()
        userinfo_layout = QtGui.QVBoxLayout()
        
        layout1 = QtGui.QHBoxLayout()
        layout2 = QtGui.QHBoxLayout()
        
        self.userinfo_chat_btn = QtGui.QPushButton("Chat with")
        self.userinfo_username_label = QtGui.QLabel("username")
        self.userinfo_username_val = QtGui.QLabel()
        layout1.addWidget(self.userinfo_username_label)
        layout1.addWidget(self.userinfo_username_val)
        self.userinfo_userid_label = QtGui.QLabel("user id")
        self.userinfo_userid_val = QtGui.QLabel()
        layout2.addWidget(self.userinfo_userid_label)
        layout2.addWidget(self.userinfo_userid_val)
        
        self.userinfo_chat_btn.clicked.connect(self.slot_chatto)

        userinfo_layout.addLayout(layout1)
        userinfo_layout.addLayout(layout2)
        userinfo_layout.addWidget(self.userinfo_chat_btn)

        userinfo_widget.setLayout(userinfo_layout)
        
        # blank widget
        blank_widget = QtGui.QWidget()
        blank_layout = QtGui.QVBoxLayout()
        self.blank_container = QtGui.QLabel("CNOA client Develop by Kevin.Chen")
        blank_layout.addWidget(self.blank_container)
        blank_widget.setLayout(blank_layout)

        self.content_wid.addWidget(blank_widget)
        self.content_wid.addWidget(chat_widget)
        self.content_wid.addWidget(userinfo_widget)
    
    def slot_chatto(self):
        self.change_widget(1)
        self.chat_label.setText(self.userinfo_username_val.text())
        self.update_chat_view(int(self.userinfo_userid_val.text()), 1)

    def chating(self, name, cid, ctype):
        self.change_widget(1)
        self.chat_label.setText(name)
        self.update_chat_view(cid, ctype)

    def update_userinfo(self, uid, uname):
        self.userinfo_username_val.setText(uname)
        self.userinfo_userid_val.setText(uid)
        self.update()
    
    def change_widget(self, idx):
        self.content_wid.setCurrentIndex(idx)

    def update_chat_view(self, cid, ctype):
        self.chat_display.clear()
        file_path = "log/"
        if ctype == 1:
            file_path += "user-" + str(cid) + ".json"
        elif ctype == 2:
            file_path += "group-" + str(cid) + ".json"

        if os.path.isfile(file_path):
            print file_path 

            fp = open(file_path)
            for line in fp.readlines():
                if line != "":
                    data = json.loads(line)
                    #print data

                    if data['id'] is None:
                        user_name = "I say: "
                    else:
                        user_name = self.chat_label.text()

                    if type(data['content']) is dict:
                        self.chat_display.insertPlainText(user_name +
                            data['posttime'] + data['content']['name'] + 
                            "\r\n") 
                    else:
                        self.chat_display.insertPlainText(user_name +
                            data['posttime'] + data['content'] + "\r\n") 
            
        self.update()    


class CNOAWindow(QtGui.QWidget):
    def __init__(self, cnoa_lib):
        super(CNOAWindow, self).__init__()

        self.cnoa = cnoa_lib
        self.initUI()
        
        self.left_wid.update_chat_list(self.cnoa.get_recentchat_list())
        self.left_wid.update_user_list(self.cnoa.get_contacts_list())
        self.left_wid.update_group_list(self.cnoa.get_group_list())


    def initUI(self):
        sidebar_box = QtGui.QVBoxLayout()
        content_box = QtGui.QVBoxLayout()

        sidebar_layout = QtGui.QGridLayout()
       
        userinfo = QtGui.QLabel()
        user_logo = QtGui.QPixmap("icons/user-logo.png")
        userinfo.setPixmap(user_logo)

        # chatlog lable
        self.chatlog_label = ActivityLabel()
        chat_icon = QtGui.QPixmap("icons/chat-icon.png")
        self.chatlog_label.setPixmap(chat_icon)
        #self.chatlog_label.setStyleSheet("QLabel {background-color: green;}")
        
        # switch icon of left panel
        self.chatlog_label.clicked.connect(self.switch_label)
        
        self.chatlog_label.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed))

        # userlist lable
        self.userlist_label = ActivityLabel()
        user_icon = QtGui.QPixmap("icons/user-icon.png")
        self.userlist_label.setPixmap(user_icon)
        self.userlist_label.clicked.connect(self.switch_label)
        
        # grouplist lable
        self.grouplist_label = ActivityLabel()
        group_icon = QtGui.QPixmap("icons/group-icon.png")
        self.grouplist_label.setPixmap(group_icon)
        self.grouplist_label.clicked.connect(self.switch_label)
            

        sidebar_layout.addWidget(userinfo, 0, 0)
        sidebar_layout.setRowStretch(1, 1)
        sidebar_layout.addWidget(self.chatlog_label, 2, 0)
        sidebar_layout.addWidget(self.userlist_label, 3, 0)
        sidebar_layout.addWidget(self.grouplist_label, 4, 0)
        sidebar_layout.setRowStretch(5, 4)
       
        # left area
        self.left_wid = LeftWidget()
        self.left_wid.user_list.itemClicked.connect(self.slot_switch_right_panel)
        self.left_wid.group_list.itemClicked.connect(self.slot_switch_right_panel)
        self.left_wid.recentchat_list.itemClicked.connect(self.slot_chating)
        
        # right area
        self.right_wid = RightWidget()
        self.right_wid.change_widget(0)

        mbox = QtGui.QHBoxLayout()
        mbox.addLayout(sidebar_layout)
        mbox.addWidget(self.left_wid)
        mbox.addWidget(self.right_wid)
        
        self.right_wid.chat_edit.commited.connect(self.slot_sendmsg)

        self.setLayout(mbox)

        self.resize(600, 600)
        self.center()
        self.show()
    
    def slot_sendmsg(self, msg):
        uid = self.cnoa.find_id_by_name(self.right_wid.chat_label.text())
        self.cnoa.send_msg(uid, msg, "person")
    
    def slot_chating(self, item):
        uname = item.text()
        self.right_wid.chating(uname, 
                self.cnoa.find_id_by_name(uname),
                self.cnoa.get_type(uname))

    def slot_switch_right_panel(self, item):
        #self.chat_display.clear()
        #self.content_wid.setCurrentIndex(2)
        
        ret = self.cnoa.get_type(item.text())
        if ret == 1 or ret == 2:
            self.right_wid.change_widget(2)
            self.right_wid.update_userinfo(self.cnoa.find_id_by_name(item.text()), item.text())
        else:
            self.right_wid.change_widget(0)
        
        self.update()

    def switch_label(self, label):
        
        if label is self.chatlog_label:
            self.left_wid.change_widget(0)
        elif label is self.userlist_label:
            self.left_wid.change_widget(1)
        elif label is self.grouplist_label:
            self.left_wid.change_widget(2)
        
        self.update()

    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

class KNotify:
    knotify = None
    def __init__(self):
        self.knotify = dbus.SessionBus().get_object("org.kde.knotify", "/Notify")
    def write_notify(self, title, text):
        #print title, text
        self.knotify.event("warning", "kde", [], title, 
                text, [], [], 0, 0,
                dbus_interface="org.kde.KNotify")

def main():
    app = QtGui.QApplication(sys.argv)
    cnoa_gui = CNOAWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':


    notify = KNotify()
    
    cnoa_lib = cnoa.CNOA(notify)
    #cnoa_lib.load_config()

    if not cnoa_lib.login():
        sys.exit()
    
    cnoa_lib.fetch_contacts_list()
    cnoa_lib.fetch_group_list()
    
    app = QtGui.QApplication(sys.argv)
    cnoa_gui = CNOAWindow(cnoa_lib)
    #cnoa_gui.update_user_list(cnoa_lib.get_contacts_list()) 
    #cnoa_gui.update_group_list(cnoa_lib.get_group_list()) 
    sys.exit(app.exec_())

