#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import string
import re
import datetime
import urllib2
from bs4 import BeautifulSoup
from optparse import OptionParser
reload(sys)
sys.setdefaultencoding('utf-8')

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-o', '--off', action='store', dest='off',default=None, help='add off days,split by comma')
    parser.add_option('-c', '--code', action='store', dest='code',default=None, help='add codes,split by comma')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)
        
    home = os.getenv('IKNOW_HOME','/var/data/iknow')
    if ops.off:
        days = ops.off.split(',')
        fn = os.path.join(os.path.join(home,'conf'),'offday.conf')
        f = open(fn,'r')
        lines = f.readlines()
        f.close()
        now = datetime.datetime.now()
        td = '%04d-%02d-%02d'%(now.year,now.month,now.day)
        mat = []
        for row in lines:
            row = row.strip()
            if row>td:
                mat.append(row)
        for d in days:
            if re.match('\d{4}-\d{2}-\d{2}', d) and (d not in mat) and d>td:
                mat.append(d)
        f = open(fn,'w')
        for row in mat:
            f.write('%s\n'%row)
        f.close()
    if ops.code:
        lis = ops.code.split(',')
        codes = []
        for it in lis:
            codes.append(it.strip())
        fn = os.path.join(os.path.join(home,'conf'),'codes.conf')
        f = open(fn,'r')
        lines = f.readlines()
        f.close()
        dic = {}
        for line in lines:
            code = line.strip()
            dic[code] = True
        url = 'http://quote.eastmoney.com/stocklist.html'
        html = urllib2.urlopen(url).read()
        soup = BeautifulSoup(html, 'lxml')
        lis = soup.find_all('li')
        for li in lis:
            try:
                a = li.find_all('a')
                name = a[0].text.strip()
                names = name.split('(')
                name = names[0]
                code = names[1][:-1]
                if code in codes:
                    dic[code]=True
            except Exception,e:
                pass
        fn = os.path.join(os.path.join(home,'conf'),'codes.conf')
        f = open(fn,'w')
        clis = dic.keys()
        clis.sort()
        for code in clis:
            f.write('%s\n'%code)
        f.close()
