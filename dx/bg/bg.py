#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import MySQLdb
import json
import urllib2
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf8')

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-f', '--file', action='store', dest='file',default=None, help='menu file')
    parser.add_option('-d', '--delete', action='store_true', dest='delete',default=False, help='delete menu')
    
    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)
        
    appid = 'wx2362cb9a0f1baece'
    appsecret = '14507233b4cec807a3449bcd8551febe'
    
    url='https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s'%(appid,appsecret)
    res = urllib2.urlopen(url)
    res = res.read()
    res = json.loads(res)
    at = None
    if res.has_key('access_token'):
        at = res['access_token']
    else:
        print 'get access token error[%d:%s]'%(res['errcode'],res['errmsg'])
        sys.exit(0)
        
    if ops.delete:
        url='https://api.weixin.qq.com/cgi-bin/menu/delete?access_token=%s'%(at)
        res = urllib2.urlopen(url)
        res = res.read()
        res = json.loads(res)
        print 'delete menu[%d:%s]'%(res['errcode'],res['errmsg'])
        sys.exit(0)

    jsondata = None
    if not ops.file:
        #jsondata = '{"button":[{"type":"click","name":"stock","key":"V1001_STOCK"},{"name":"MOM","sub_button":[{"type":"view","name":"trade","url":"http://www.boargame.org.cn/mom/index.php"},{"type":"click","name":"me","key":"V1001_MYINFO"},{"type":"click","name":"about","key":"V1001_ABOUT"}]}]}'
        print 'json file is needed'
        sys.exit(0)
    else:
        f = open(ops.file,'r')
        jsondata = f.read()
        f.close()

    header_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',"Content-Type": "application/json"}
    url='https://api.weixin.qq.com/cgi-bin/menu/create?access_token=%s'%at
    req = urllib2.Request(url=url,data=jsondata,headers=header_dict)
    res = urllib2.urlopen(req)
    res = res.read()
    res = json.loads(res)
    print 'create menu[%d:%s]'%(res['errcode'],res['errmsg'])

