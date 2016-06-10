# -*- coding: utf-8 -*-
import sys
from PySide import QtGui, QtCore

class ActivityLabel(QtGui.QLabel):
    clicked = QtCore.Signal(object)
    def __init__(self):
        super(ActivityLabel, self).__init__()
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self)

class TextInputWidget(QtGui.QTextEdit):
    commited = QtCore.Signal()
    def __init__(self):
        QtGui.QTextEdit.__init__(self)
    def keyPressEvent(self, event):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers & QtCore.Qt.ControlModifier and \
            (event.key() == QtCore.Qt.Key_Enter or \
            event.key() == QtCore.Qt.Key_Return):
            print "send it"
            self.commited.emit()

        return QtGui.QTextEdit.keyPressEvent(self, event)

class CNOAWindow(QtGui.QWidget):
    def __init__(self):
        super(CNOAWindow, self).__init__()

        self.initUI()

    def initUI(self):
        sidebar_box = QtGui.QVBoxLayout()
        content_box = QtGui.QVBoxLayout()

        sidebar_layout = QtGui.QGridLayout()
       
        userinfo = QtGui.QLabel()
        user_logo = QtGui.QPixmap("user-logo.png")
        userinfo.setPixmap(user_logo)

        # chatlog lable
        self.chatlog_label = ActivityLabel()
        chat_icon = QtGui.QPixmap("chat-icon.png")
        self.chatlog_label.setPixmap(chat_icon)
        self.chatlog_label.clicked.connect(self.switch_label)

        # userlist lable
        self.userlist_label = ActivityLabel()
        user_icon = QtGui.QPixmap("user-icon.png")
        self.userlist_label.setPixmap(user_icon)
        self.userlist_label.clicked.connect(self.switch_label)
        
        # grouplist lable
        self.grouplist_label = ActivityLabel()
        group_icon = QtGui.QPixmap("group-icon.png")
        self.grouplist_label.setPixmap(group_icon)
        self.grouplist_label.clicked.connect(self.switch_label)
            

        sidebar_layout.addWidget(userinfo, 0, 0)
        sidebar_layout.setRowStretch(1, 1)
        sidebar_layout.addWidget(self.chatlog_label, 2, 0)
        sidebar_layout.addWidget(self.userlist_label, 3, 0)
        sidebar_layout.addWidget(self.grouplist_label, 4, 0)
        sidebar_layout.setRowStretch(5, 4)
       
        # middle area
        self.middle_box = QtGui.QVBoxLayout()
        self.chatlog_list = QtGui.QListWidget()
        self.user_list = QtGui.QListWidget()
        self.group_list = QtGui.QListWidget()

        self.user_list.clicked.connect(self.switch_content_widget)
        
        self.user_list.setVisible(False)
        self.group_list.setVisible(False)

        self.middle_box.addWidget(self.chatlog_list)
        self.middle_box.addWidget(self.user_list)
        self.middle_box.addWidget(self.group_list)

        # content area
        self.content_wid = QtGui.QStackedLayout()

        chat_widget = QtGui.QWidget()
        chat_layout = QtGui.QGridLayout()
        self.chat_display = QtGui.QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_edit = TextInputWidget()
        chat_layout.setColumnMinimumWidth(0, 200)
        chat_layout.setRowMinimumHeight(0, 500)
        chat_layout.addWidget(self.chat_display, 0, 0, 4, 4)
        chat_layout.addWidget(self.chat_edit, 4, 0, 4, 4)
        chat_widget.setLayout(chat_layout)

        userinfo_widget = QtGui.QWidget()
        userinfo_layout = QtGui.QVBoxLayout()
        self.userinfo_container = QtGui.QLabel()
        userinfo_layout.addWidget(self.userinfo_container)
        userinfo_widget.setLayout(userinfo_layout)
        
        blank_widget = QtGui.QWidget()
        blank_layout = QtGui.QVBoxLayout()
        self.blank_container = QtGui.QLabel()
        blank_layout.addWidget(self.blank_container)
        blank_widget.setLayout(blank_layout)

        self.content_wid.addWidget(chat_widget)
        self.content_wid.addWidget(userinfo_widget)
        self.content_wid.addWidget(blank_widget)
        
        #self.content_box.addWidget(self.content_wid)

        mbox = QtGui.QGridLayout()
        mbox.addLayout(sidebar_layout, 0, 0)
        mbox.addLayout(self.middle_box, 0, 1)
        mbox.addLayout(self.content_wid, 0, 2)

        mbox.setColumnStretch(0, 1)
        mbox.setColumnStretch(1, 2)
        #mbox.setColumnStretch(3, 4)
        self.setLayout(mbox)

        self.resize(600, 600)
        self.center()
        self.show()

    def switch_content_widget(self, item):
        print item

    def update_chatlog_list(self, log_list):
        self.chatlog_list.addItem("chat kevinsu")
        self.chatlog_list.addItem("chat linda")
    
    def update_user_list(self, user_list):
        for usr in user_list:
            self.user_list.addItem(QtGui.QListWidget(usr['text']))
    
    def update_group_list(self, group_list):
        for grp in group_list:
            self.group_list.addItem(grp['name'])
    
    def switch_label(self, label):
        if label is self.chatlog_label:
            self.chatlog_list.setVisible(True)
            self.user_list.setVisible(False)
            self.group_list.setVisible(False)
            self.chatlog_label.setStyleSheet("QLabel {background-color: green;}")
            self.userlist_label.setStyleSheet("")
            self.grouplist_label.setStyleSheet("")
        elif label is self.userlist_label:
            self.user_list.setVisible(True)
            self.chatlog_list.setVisible(False)
            self.group_list.setVisible(False)
            self.userlist_label.setStyleSheet("QLabel {background-color: green;}")
            self.chatlog_label.setStyleSheet("")
            self.grouplist_label.setStyleSheet("")
        elif label is self.grouplist_label:
            self.group_list.setVisible(True)
            self.chatlog_list.setVisible(False)
            self.user_list.setVisible(False)
            self.grouplist_label.setStyleSheet("QLabel {background-color: green;}")
            self.chatlog_label.setStyleSheet("")
            self.userlist_label.setStyleSheet("")

        self.update()


    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

def main():
    app = QtGui.QApplication(sys.argv)
    cnoa_gui = CNOAWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
