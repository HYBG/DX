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

class iknow:
    def __init__(self):
        self.__codes = {}
        g_tool.conn('dx')
        self._reload()

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('dx')
        data = g_tool.exesqlbatch('select code from dx.iknow_name order by code', None)
        for row in data:
            ld = g_tool.exesqlone('select date from dx.iknow_data where code=%s order by date desc limit 1',(row[0],))
            if len(ld)!=0:
                self.__codes[row[0]]=ld[0]
            else:
                self.__codes[row[0]]='1982-09-04'
                
    def _codes(self):
        codes = self.__codes.keys()
        codes.sort()
        return codes

    def dl(self):
        try:
            g_iu.log(logging.INFO,'dx dl task start....')
            now = datetime.datetime.now()
            self._reload()
            clis = self._codes()
            sqls = []
            defaultstart = '2016-01-01'
            for code in clis:
                try:
                    start = defaultstart
                    if self.__codes.has_key(code):
                        start = self.__codes[code]
                    mat = g_tool.dl_upfrom163(code,start)
                    for row in mat:
                        sqls.append(('insert into dx.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                except Exception,e:
                    g_iu.log(logging.INFO,'code[%s],date[%04d-%02d-%02d] update failed[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
            sqls = []
            for code in clis:
                try:
                    shouldadd = g_tool.exesqlbatch('select date from hs.hs_daily_data where code=%s and date not in (select date from dx.iknow_data where code=%s)',(code,code))
                    for adt in shouldadd:
                        g_iu.log(logging.INFO,'dx handle dl code[%s] date[%s]....'%(code,adt[0]))
                        row = g_tool.exesqlone('select code,date,open,high,low,close,volh,volwy from hs.hs_daily_data where code=%s and date=%s',(code,adt[0]))
                        sqls.append(('insert into dx.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                except Exception,e:
                    g_iu.log(logging.INFO,'code[%s],date[%04d-%02d-%02d] local update exception[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
        except Exception,e:
            g_iu.log(logging.INFO,'dx dl exception[%s]....'%e)
        g_iu.log(logging.INFO,'dx dl task done....')
        
    def _stdv(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0
        for item in lis:
            all = all + (item-ev)**2
        std = all**0.5
        stdv = 0.0
        if std!=0:
            stdv = (lis[0]-ev)/std
        return stdv

    def std5(self):
        codes = self._codes()
        g_iu.log(logging.INFO,'dx std5 handle start....')
        total = float(len(codes))
        handled = 1
        for code in codes:
            sqls = []
            ld = g_tool.exesqlone('select date from dx.iknow_std5 where code=%s order by date desc limit 1',(code,))
            end = '2015-01-01'
            if len(ld)!=0:
                end = ld[0]
            data = g_tool.exesqlbatch('select date,open,high,low,close,volh from dx.iknow_data where code=%s order by date desc',(code,))
            if len(data)<=60:
                continue
            for i in range(len(data)-5):
                if data[i][0]<=end:
                    break
                need = data[i:i+5]
                openlis = []
                highlis = []
                lowlis = []
                closelis = []
                volwylis = []
                for item in need:
                    openlis.append(item[1])
                    highlis.append(item[2])
                    lowlis.append(item[3])
                    closelis.append(item[4])
                    volwylis.append(item[5])
                stdopen = self._stdv(openlis)
                stdhigh = self._stdv(highlis)
                stdlow = self._stdv(lowlis)
                stdclose = self._stdv(closelis)
                stdvolwy = self._stdv(volwylis)
                sqls.append(('insert into dx.iknow_std5(code,date,stdopen,stdhigh,stdlow,stdclose,stdvolwy) values(%s,%s,%s,%s,%s,%s,%s)',(code,data[i][0],'%0.4f'%stdopen,'%0.4f'%stdhigh,'%0.4f'%stdlow,'%0.4f'%stdclose,'%0.4f'%stdvolwy)))
            g_tool.task(sqls)
            g_iu.log(logging.INFO,'dx handle std5 progress[%0.2f%%] code[%s] sqls[%d]'%(100*(handled/total),code,len(sqls)))
            handled = handled+1
        g_iu.log(logging.INFO,'dx std5 handle done....')

    def tell(self,end):
        g_iu.log(logging.INFO,'dx handle tell start....')
        ld = g_tool.exesqlone('select date from dx.iknow_tell2 order by date limit 1',None)
        dts = None
        if len(ld)==0:
            ld = g_tool.exesqlone('select date from dx.iknow_std5 order by date desc limit 1',None)
            if len(ld)==0:
                g_iu.log(logging.INFO,'dx handle tell end no need....')
                return
            ld = ld[0]
            dts = g_tool.exesqlbatch('select distinct date from dx.iknow_std5 where date<=%s and date>=%s order by date desc',(ld,end))
        else:
            ld = ld[0]
            dts = g_tool.exesqlbatch('select distinct date from dx.iknow_std5 where date<%s and date>=%s order by date desc',(ld,end))
        g_iu.log(logging.INFO,'dx tell from [%s] to [%s]'%(dts[0][0],dts[-1][0]))
        for dt in dts:
            g_iu.log(logging.INFO,'dx handle tell start date[%s]....'%dt[0])
            self.told(dt[0])
        g_iu.log(logging.INFO,'dx handle tell end....')

    def istold(self,day):
        cnt = g_tool.exesqlone('select count(*) from dx.iknow_tell2 where date=%s',(day,))
        if cnt[0]>0:
            return True
        return False

    def told(self,day):
        g_iu.log(logging.INFO,'dx handle told start[%s]....'%(day))
        stds = g_tool.exesqlbatch('select code,stdopen,stdhigh,stdlow,stdclose,stdvolwy from dx.iknow_std5 where date=%s order by code',(day,))
        total = float(len(stds))
        handled = 1
        thv = 0.05
        sqls = []
        for stdv in stds:
            code = stdv[0]
            vector = (stdv[1],stdv[2],stdv[3],stdv[4],stdv[5])
            hblis = []
            lblis = []
            klis = []
            hplis = []
            lplis = []
            lib = g_tool.exesqlbatch('select code,date,fv,stdopen,stdhigh,stdlow,stdclose,stdvolwy from dx.iknow_library where stdopen>%s and stdopen<%s and stdhigh>%s and stdhigh<%s and stdlow>%s and stdlow<%s and stdclose>%s and stdclose<%s and stdvolwy>%s and stdvolwy<%s and date<%s',(stdv[1]-thv,stdv[1]+thv,stdv[2]-thv,stdv[2]+thv,stdv[3]-thv,stdv[3]+thv,stdv[4]-thv,stdv[4]+thv,stdv[5]-thv,stdv[5]+thv,day))
            for item in lib:
                v = (item[3],item[4],item[5],item[6],item[7])
                d = ((vector[0]-v[0])**2+(vector[1]-v[1])**2+(vector[2]-v[2])**2+(vector[3]-v[3])**2+(vector[4]-v[4])**2)**0.5
                if d<thv:
                    hblis.append(float(item[2][0]))
                    lblis.append(float(item[2][1]))
                    klis.append(float(item[2][2]))
                    hplis.append(float(item[2][3]))
                    lplis.append(float(item[2][4]))
            if len(hblis)>0:
                cnt = len(hblis)
                hbp = '%0.4f'%(sum(hblis)/float(len(hblis)))
                lbp = '%0.4f'%(sum(lblis)/float(len(lblis)))
                kp = '%0.4f'%(sum(klis)/float(len(klis)))
                hpp = '%0.4f'%(sum(hplis)/float(len(hplis)))
                lpp = '%0.4f'%(sum(lplis)/float(len(lplis)))
                sqls.append(('insert into dx.iknow_tell2(code,date,count,hbp,lbp,kp,hpp,lpp) values(%s,%s,%s,%s,%s,%s,%s,%s)',(code,day,cnt,hbp,lbp,kp,hpp,lpp)))
            g_iu.log(logging.INFO,'dx told handle progress[%0.2f%%] code[%s] date[%s] sqls[%d]....'%(100*(handled/total),code,day,len(sqls)))
            handled = handled+1
        g_tool.task(sqls)
        g_iu.log(logging.INFO,'dx handle told end[%s]....'%(day))
        
    def daily_task(self,name):
        g_iu.log(logging.INFO,'daily_task[%s] start....'%(name))
        self.dl()
        self.std5()
        self.told(name)
        g_iu.log(logging.INFO,'daily_task[%s] end successfully....'%(name))

    def _taskname(self):
        dt = datetime.datetime.now()
        if dt.hour < 17:
            dt = dt + datetime.timedelta(days=-1)
        while dt.isoweekday()>5:
            dt = dt + datetime.timedelta(days=-1)
        return '%04d-%02d-%02d'%(dt.year,dt.month,dt.day)

    def run(self):
        pretask = ''
        while 1:
            taskname = self._taskname()
            if taskname != pretask:
                self.daily_task(taskname)
                pretask = taskname
            time.sleep(5)

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-t', '--tell', action='store_true', dest='tell',default=False, help='tell task')
    parser.add_option('-e', '--end', action='store', dest='end',default=None, help='tell task end day')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = iknow()
    if ops.tell and ops.end:
        ik.tell(ops.end)
    else:
        ik.run()

    
    
    