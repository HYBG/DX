#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import urllib2
import socket
import MySQLdb
from bs4 import BeautifulSoup
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME')
sys.path.append(os.path.join(g_home,'lib'))
from ikutil import ikutil
from iktool import iktool

g_iu = ikutil()
g_tool = iktool()


if __name__ == "__main__":
    g_tool.conn('hy')
    tags = g_tool.exesqlbatch('select code,name,tag from hy.iknow_tags where tagtype=%s',('industry',))
    sqls = []
    for row in tags:
        sqls.append(('insert into iknow.ik_name(code,name,industry) values(%s,%s,%s)',(row[0],row[1],row[2])))

    g_tool.task(sqls)
    '''
    watches = g_tool.exesqlbatch('select code,active,name,industry from hy.iknow_watch',None)
    sqls = []
    for row in watches:
        sqls.append(('insert into hyik.ik_watch(code,active,name,industry) values(%s,%s,%s,%s)',(row[0],row[1],row[2],row[3])))
    g_tool.task(sqls)
    
    ofn = os.path.join(g_home,'codes.csv')
    f = open(ofn,'w')
    data = g_tool.exesqlbatch('select distinct code,name from hy.iknow_tags order by code desc',None)
    for row in data:
        f.write('%s\n'%(row[0]))
    f.close()'''
    

