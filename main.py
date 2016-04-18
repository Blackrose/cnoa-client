# -*- coding: utf-8 -*-
import urllib
import urllib2
import cookielib
import json
import codecs

"""
{
    "user_name": username,
    "user_password": password,
    "server_address": server_url
}
"""
def load_config():
    f = codecs.open("config.json")
    config_data = f.read()
    f.close()
    user_data = json.loads(config_data)
    #print "%r" % user_data['user_name'].encode('utf-8')
    return user_data

user_data = load_config()

server_url = "http://113.87.195.133:81"
user_agent = 'Mozilla/5.0 (Windows; U; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) AdobeAIR/18.0'

login_url = "/api/messagerv2/index.php?action=login&task=login"

headers = {'User-Agent': user_agent}

values = {'username': user_data['user_name'].encode('utf-8'),
        'password': user_data['user_password'],
        'serverurl': user_data['server_address']
        }
print values

def parser_json(data):
    ddata = json.loads(data)
    print ddata
    #print ddata[0]['text']
    for i in ddata:
        if i['leaf']:
            print i['uid'], i['text'], i['iconCls']
        else:
            print i['selfid'], i['text']

    
    return ddata

def get_list(item_id):
    global server_url
    print "get Contacts list"
    get_contactlist = "/index.php?app=communication&func=im&version=50008&action=index&task=getAllUserListsInDeptTree"
    node_value = {'node': item_id}
    data = urllib.urlencode(node_value)
    request = urllib2.Request(server_url + get_contactlist, data, headers)
    response = opener.open(request)
    user_list = response.read()
    return user_list


bool is_login = False

cookie = cookielib.CookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie))
urllib2.install_opener(opener)

data = urllib.urlencode(values)
req = urllib2.Request(server_url + login_url, data, headers)
response = urllib2.urlopen(req)
html = response.read()
data = json.loads(html)

if data['success']:
    is_login = True
    print "Login Successful!"
    for cook in cookie:
        if cook == "CNOAOASESSIONID":
            print cook
else:
    print "%s" % data['msg']
    is_login = False


get_tasklist = "/api/messagerv2/index.php?action=group&task=getList"
#response = opener.open(server_url + get_list)
#print response.read()


quary_list = ['CNOA_main_struct_list_tree_node_1']

print quary_list

for i in quary_list:
    list_dt = get_list(i)
    list_user = parser_json(list_dt)
    for item in list_user:
        if item['leaf'] == False:
            quary_list.append(item['id'])

if __main__ == 'main':
    print "Init client"
