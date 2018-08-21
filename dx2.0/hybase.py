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

class hyiknow:
    def __init__(self):
        self.__codes = {}
        g_tool.conn('hy')
        self._reload()
        self._mindate = '2005-01-05'
        self._logger = g_iu.createlogger('hybase',os.path.join(os.path.join(g_home,'log'),'hybase.log'),logging.INFO)

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('hy')
        data = g_tool.exesqlbatch('select code from hy.iknow_name order by code', None)
        for row in data:
            ld = g_tool.exesqlone('select date from hy.iknow_data where code=%s order by date desc limit 1',(row[0],))
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
            self._logger.info('hy dl task start....')
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
                        sqls.append(('insert into hy.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                except Exception,e:
                    self._logger.info('code[%s],date[%04d-%02d-%02d] update failed[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
            self._logger.info('hy handle dl executed sqls[%d]....'%(len(sqls)))
            sqls = []
            for code in clis:
                try:
                    shouldadd = g_tool.exesqlbatch('select date from hs.hs_daily_data where code=%s and date not in (select date from hy.iknow_data where code=%s)',(code,code))
                    for adt in shouldadd:
                        self._logger.info('hy handle dl code[%s] date[%s]....'%(code,adt[0]))
                        row = g_tool.exesqlone('select code,date,open,high,low,close,volh,volwy from hs.hs_daily_data where code=%s and date=%s',(code,adt[0]))
                        sqls.append(('insert into hy.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                except Exception,e:
                    self._logger.info('code[%s],date[%04d-%02d-%02d] local update exception[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
            self._logger.info('hy handle dl check executed sqls[%d]....'%(len(sqls)))
        except Exception,e:
            self._logger.info('hy dl exception[%s]....'%e)
        self._logger.info('hy dl task done....')

    def kinfo(self):
        self._reload()
        clis = self._codes()
        total = float(len(clis))
        handled = 0
        self._logger.info('hy kinfo task start....')
        for code in clis:
            sqls = []
            handled = handled+1
            ld = g_tool.exesqlone('select date from hy.iknow_kinfo where code=%s order by date desc limit 1',(code,))
            start = '1982-09-04'
            if len(ld)!=0:
                start = ld[0]
            self._logger.debug('hy kinfo task code[%s] start[%s]'%(code,start))
            data = g_tool.exesqlbatch('select date,open,high,low,close from hy.iknow_data where code=%s and date>=%s',(code,start))
            for i in range(1,len(data)):
                date = data[i][0]
                hb = 0
                if data[i][2]>data[i-1][2]:
                    hb = 1
                lb = 0
                if data[i][3]<data[i-1][3]:
                    lb = 1
                k = 1
                if data[i][4]<data[i][1]:
                    k = 0
                elif data[i][4]>data[i][1]:
                    k = 2
                csrc = 0.5
                if data[i][2]!=data[i][3]:
                    csrc = (data[i][4]-data[i][3])/(data[i][2]-data[i][3])
                pattern = 0
                if hb==1 and lb==0 and k==1:
                    pattern = 1
                elif hb==1 and lb==0 and k==0:
                    pattern = 2
                elif hb==0 and lb==1 and k==1:
                    pattern = 3
                elif hb==0 and lb==1 and k==0:
                    pattern = 4
                elif hb==1 and lb==1 and k==1:
                    pattern = 5
                elif hb==1 and lb==1 and k==0:
                    pattern = 6
                elif hb==0 and lb==0 and k==1:
                    pattern = 7
                elif hb==0 and lb==0 and k==0:
                    pattern = 8
                sqls.append(('insert into hy.iknow_kinfo(code,date,hb,lb,k,csrc,pattern) values(%s,%s,%s,%s,%s,%s,%s)',(code,date,hb,lb,k,'%0.4f'%csrc,pattern)))
            self._logger.info('hy kinfo handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            g_tool.task(sqls)
        self._logger.info('hy kinfo task done executed sqls[%d]....'%len(sqls))

    def poles(self):
        clis = self._codes()
        total = float(len(clis))
        handled = 0
        self._logger.info('hy poles task start....')
        for code in clis:
            sqls = []
            handled = handled+1
            ld = g_tool.exesqlone('select date from hy.iknow_poles where code=%s order by date desc limit 1',(code,))
            start = '1982-09-04'
            if len(ld)!=0:
                start = ld[0]
            data = g_tool.exesqlbatch('select date,open,high,low,close from hy.iknow_data where code=%s and date>=%s',(code,start))
            for i in range(1,len(data)-1):
                date = data[i][0]
                hp = 0
                if (data[i][2]>data[i-1][2]) and (data[i][2]>data[i+1][2]):
                    hp = 1
                lp = 0
                if (data[i][3]<data[i-1][3]) and (data[i][3]<data[i+1][3]):
                    lp = 1
                sqls.append(('insert into hy.iknow_poles(code,date,hp,lp) values(%s,%s,%s,%s)',(code,date,hp,lp)))
            self._logger.info('hy poles handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            g_tool.task(sqls)
        self._logger.info('hy poles task done executed sqls[%d]....'%len(sqls))

    def bollkd(self):
        clis = self._codes()
        sqls = []
        total = float(len(clis))
        handled = 0
        kdp = 9
        bollp = 20
        self._logger.info('hy bollkd task start....')
        for code in clis:
            handled = handled+1
            data = g_tool.exesqlbatch('select date,open,high,low,close from hy.iknow_data where code=%s',(code,))
            lk = 50.0
            ld = 50.0
            if len(data)<20:
                continue
            mat = []
            for i in range(kdp,len(data)):
                close = data[i][4]
                high = data[i][2]
                low = data[i][3]
                for j in range(1,kdp):
                    if data[i-j][2]>high:
                        high = data[i-j][2]
                    if data[i-j][3]<low:
                        low = data[i-j][3]
                k = 50.0
                d = 50.0
                if high != low:
                    rsv = 100*((close-low)/(high-low))
                    k = (2.0*lk+rsv)/3.0
                    d = (2.0*ld+k)/3.0
                lk = k
                ld = d
                if i >= bollp:
                    k = round(k,2)
                    d = round(d,2)
                    sum = 0.0
                    for j in range(bollp):
                        sum = sum + data[i-j][4]
                    mid = round(sum/float(bollp),2)
                    all = 0.0
                    for j in range(bollp):
                        all = all + (data[i-j][4]-mid)**2
                    std = round((all/float(bollp))**0.5,2)
                    mat.append((code,data[i][0],k,d,mid,std))
            ld = g_tool.exesqlone('select date from hy.iknow_bollkd where code=%s order by date desc limit 1',(code,))
            start = '1982-09-04'
            if len(ld)!=0:
                start = ld[0]
            for row in mat:
                if row[1]>start:
                    sqls.append(('insert into hy.iknow_bollkd(code,date,k,d,mid,std) values(%s,%s,%s,%s,%s,%s)',row))
            self._logger.info('hy bollkd handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            g_tool.task(sqls)
            self._logger.info('hy bollkd task executed sqls[%d]....'%len(sqls))
            sqls = []
        #g_tool.task(sqls)
        #self._logger.info('hy bollkd task done executed sqls[%d]....'%len(sqls))

    def macd(self):
        clis = self._codes()
        sqls = []
        total = float(len(clis))
        handled = 0
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        self._logger.info('hy macd task start....')
        for code in clis:
            handled = handled+1
            data = g_tool.exesqlbatch('select date,close from hy.iknow_data where code=%s',(code,))
            mat = []
            for i in range(len(data)):
                if i == 0:
                    emaf = data[i][1]
                    emas = data[i][1]
                    dea = 0
                else:
                    close = data[i][1]
                    emaf = 2*close/(macdparan1+1)+(macdparan1-1)*emaf/(macdparan1+1)
                    emas = 2*close/(macdparan2+1)+(macdparan2-1)*emas/(macdparan2+1)
                    diff = emaf-emas
                    dea  = 2*diff/(macdparan3+1)+(macdparan3-1)*dea/(macdparan3+1)
                    macd = 2*(diff-dea)
                    mat.append((code,data[i][0],'%0.4f'%(diff),'%0.4f'%(dea),'%0.4f'%(macd)))
            ld = g_tool.exesqlone('select date from hy.iknow_macd where code=%s order by date desc limit 1',(code,))
            start = '1982-09-04'
            if len(ld)!=0:
                start = ld[0]
            for row in mat:
                if row[1]>start:
                    sqls.append(('insert into hy.iknow_macd(code,date,diff,dea,macd) values(%s,%s,%s,%s,%s)',row))
            self._logger.info('hy macd handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            g_tool.task(sqls)
            self._logger.info('hy macd task executed sqls[%d]....'%len(sqls))
            sqls = []
        self._logger.info('hy macd task done....')
            
    def ma(self):
        clis = self._codes()
        total = float(len(clis))
        handled = 0
        self._logger.info('hy ma task start....')
        for code in clis:
            sqls = []
            handled = handled+1
            data = g_tool.exesqlbatch('select date,close from hy.iknow_data where code=%s',(code,))
            if len(data)<60:
                continue
            if data[59][0]<'2005-01-01':
                continue
            mat = []
            for i in range(60,len(data)):
                mas = [5,10,20,30,60]
                line = [code,data[i][0]]
                for map in mas:
                    sum = 0.0
                    for j in range(map):
                        sum = sum + data[i-j][1]
                    line.append(round(sum/float(map),2))
                    sum = 0.0
                mat.append(line)
            ld = g_tool.exesqlone('select date from hy.iknow_ma where code=%s order by date desc limit 1',(code,))
            start = '1982-09-04'
            if len(ld)!=0 and ld[0]:
                start = ld[0]
            for row in mat:
                if row[1]>start:
                    sqls.append(('insert into hy.iknow_ma(code,date,ma5,ma10,ma20,ma30,ma60) values(%s,%s,%s,%s,%s,%s,%s)',tuple(row)))
            self._logger.info('hy ma handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
            g_tool.task(sqls)
            self._logger.info('hy ma task executed sqls[%d]....'%len(sqls))
        self._logger.info('hy ma task done....')

    def feature(self):
        clis = self._codes()
        total = float(len(clis))
        handled = 0
        self._logger.info('hy feature task start....')
        for code in clis:
            sqls = []
            handled = handled+1
            data = g_tool.exesqlbatch('select date,pattern from hy.iknow_kinfo where code=%s order by date desc',(code,))
            if len(data)<60:
                continue
            if data[59][0]<'2005-01-01':
                continue
            ld = g_tool.exesqlone('select date from hy.iknow_feature where code=%s order by date desc limit 1',(code,))
            start = '1982-09-04'
            if len(ld)>0 and ld[0]:
                start = ld[0]
            mat = []
            for i in range(len(data)-4):
                if data[i][0]<=start:
                    break
                next = data[i][1]
                fv = '%d%d%d%d'%(data[i+1][1],data[i+2][1],data[i+3][1],data[i+4][1])
                ohlc = g_tool.exesqlone('select open,high,low,close from hy.iknow_data where code=%s and date=%s',(code,data[i][0]))
                if len(ohlc)>0 and ohlc[0]:
                    sqls.append(('insert into hy.iknow_feature(code,date,fv,next,open,high,low,close) values(%s,%s,%s,%s,%s,%s,%s,%s)',(code,data[i][0],fv,next,ohlc[0],ohlc[1],ohlc[2],ohlc[3])))
            g_tool.task(sqls)
            self._logger.info('hy feature handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hy feature task done....')
        
    def button(self):
        urllib2.urlopen('http://0.0.0.0:1982/iknow?name=do_feature')
        urllib2.urlopen('http://0.0.0.0:1982/iknow?name=do_trend')

    def daily_task(self,name):
        g_tool.reconn('hy')
        self._logger.info('daily_task[%s] start....'%(name))
        g_tool.task([('update hy.iknow_conf set value=%s where name=%s',('busy','status'))])
        self.dl()
        self.kinfo()
        self.poles()
        self.bollkd()
        self.macd()
        self.ma()
        self.feature()
        self.button()
        g_tool.task([('update hy.iknow_conf set value=%s where name=%s',('idle','status'))])
        self._logger.info('daily_task[%s] end successfully....'%(name))

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
            time.sleep(4)

if __name__ == "__main__":
    ik = hyiknow()
    #ik.feature()
    ik.run()

    
    
    