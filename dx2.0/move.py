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
    some = g_tool.exesqlbatch('select code,name from hy.iknow_name',None)
    sqls = []
    for row in some:
        sqls.append(('update hy.iknow_tags set name=%s where code=%s',(row[1],row[0])))
    g_tool.task(sqls)
