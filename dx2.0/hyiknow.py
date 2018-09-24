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

class hyinfo:
    def _init__(self,code,date,dic):
        self.code = code
        self.date = date
        g_tool.reconn('hy')
        items = ''
        tabs  = ''
        cond  = ''
        paras = []
        attrs = []
        for tab in dic.keys():
            for it in dic[tab]:
                item = '%s.%s'%(tab,it)
                if not hasattr(self,it):
                    setattr(self,it,None)
                    attra.append(it)
                items = items+item+','
                tabs = tabs+tab+','
                cond = cond+tab+'.code=%s and '+tab+'.date=%s and '
                paras.append(code)
                paras.append(date)
        if len(tabs)!=0 and len(items)!=0 and len(cond)!=0:
            tabs = tabs[:-1]
            items = items[:-1]
            cond = cond[:-5]
            sql = 'select %s from %s where %s'%(items,tabs,cond)
            data = g_tool.exesqlone(sql,tuple(paras))
            if len(data)!=0 and data[0]:
                for i in range(len(data)):
                    setattr(self,attrs[i],data[i])

class hyrow:
    def __init__(self,open,high,low,close,volwy):
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volwy = volwy
        
class hydata:
    def __init__(self,code,length=None):
        self._dic = {}
        data = None
        if length:
            data = g_tool.exesqlbatch('select date,open,high,low,close,volwy from hy.iknow_data where code=%s order by date desc limit '+str(length),(code,))
        else:
            data = g_tool.exesqlbatch('select date,open,high,low,close,volwy from hy.iknow_data where code=%s order by date desc',(code,))
        for row in data:
            self._dic[row[0]] = hyrow(row[1],row[2],row[3],row[4],row[5])

    def dateline(self,rev=True):
        dl = self._dic.keys()
        dl.sort(reverse=rev)
        return dl

    def get(self,date):
        return self._dic[date]
        
    def length(self):
        return len(self._dic.keys())

    def getsum(self,para):
        dl = self.dateline()
        all = 0.0
        for i in range(para):
            all = all + self._dic[dl[i]].close
        return all

class hyiknow:
    def __init__(self):
        self.__codes = {}
        g_tool.conn('hy')
        self._reload()
        self._mindate = '2005-01-05'
        self._logger = g_iu.createlogger('hyiknow',os.path.join(os.path.join(g_home,'log'),'hyiknow.log'),logging.INFO)
        self._upcodes = []

    def __del__(self):
        pass

    def _reload(self):
        g_tool.reconn('hy')
        data = g_tool.exesqlbatch('select distinct code from hy.iknow_tags order by code', None)
        for row in data:
            ldd = g_tool.exesqlone('select date from hy.iknow_data where code=%s order by date desc limit 1',(row[0],))
            lda = g_tool.exesqlone('select date from hy.iknow_attr where code=%s order by date desc limit 1',(row[0],))
            d = '1982-09-04'
            a = '1982-09-04'
            if len(ldd)>0 and ldd[0]:
                d=ldd[0]
            if len(lda)>0 and lda[0]:
                a = lda[0]
            self.__codes[row[0]]=(d,a)

    def _codes(self):
        codes = self.__codes.keys()
        codes.sort()
        return codes
        
    def _kinfo(self,code,data):
        self._logger.debug('hyiknow _kinfo start code[%s] length[%d]'%(code,data.length()))
        ld = self.__codes[code][1]
        dic = {}
        dl = data.dateline()
        for i in range(len(dl)-1):
            if dl[i]<=ld:
                break
            day = datetime.datetime.strptime(dl[i],'%Y-%m-%d')
            weekday = day.isoweekday()
            hyrow = data.get(dl[i])
            hyrowprev = data.get(dl[i+1])
            hb = 0
            if hyrow.high>hyrowprev.high:
                hb = 1
            lb = 0
            if hyrow.low<hyrowprev.low:
                lb = 1
            k = 0
            if hyrow.close>hyrow.open:
                k = 1
            csrc = 0.5
            if hyrow.high!=hyrow.low:
                csrc = round((hyrow.close-hyrow.low)/(hyrow.high-hyrow.low),4)
            zdf = round((hyrow.close-hyrowprev.close)/hyrowprev.close,4)
            fv = self._fv(hb,lb,k)
            dic[dl[i]] = (weekday,hb,lb,k,csrc,zdf,fv)
        self._logger.debug('hyiknow _kinfo done code[%s] length[%d]'%(code,len(dic)))
        return dic
        
    def _kd(self,code,data):
        self._logger.debug('hyiknow _kd start code[%s] length[%d]'%(code,data.length()))
        kdp = 9
        lastday = self.__codes[code][1]
        lk = 50.0
        ld = 50.0
        dic = {}
        dl = data.dateline(False)
        for i in range(kdp,len(dl)):
            close = data.get(dl[i]).close
            high = data.get(dl[i]).high
            low = data.get(dl[i]).low
            for j in range(1,kdp):
                if data.get(dl[i-j]).high>high:
                    high = data.get(dl[i-j]).high
                if data.get(dl[i-j]).low<low:
                    low = data.get(dl[i-j]).low
            k = 50.0
            d = 50.0
            if high != low:
                rsv = 100*((close-low)/(high-low))
                k = (2.0*lk+rsv)/3.0
                d = (2.0*ld+k)/3.0
            lk = k
            ld = d
            k = round(k,2)
            d = round(d,2)
            if dl[i]>lastday:
                dic[dl[i]]=(k,d)
        self._logger.debug('hyiknow _kd done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _boll(self,code,data):
        self._logger.debug('hyiknow _boll start code[%s] length[%d]'%(code,data.length()))
        ld = self.__codes[code][1]
        bollp = 20
        dic = {}
        dl = data.dateline(False)
        for i in range(bollp,len(dl)):
            if i >= bollp:
                if dl[i] <= ld:
                    continue
                sum = 0.0
                for j in range(bollp):
                    sum = sum + data.get(dl[i-j]).close
                mid = round(sum/float(bollp),2)
                all = 0.0
                for j in range(bollp):
                    all = all + (data.get(dl[i-j]).close-mid)**2
                std = round((all/float(bollp))**0.5,2)
                dic[dl[i]] = (mid,std)
        self._logger.debug('hyiknow _boll done code[%s] length[%d]'%(code,len(dic)))
        return dic
        
    def _macd(self,code,data):
        self._logger.debug('hyiknow _macd start code[%s] length[%d]'%(code,data.length()))
        ld = self.__codes[code][1]
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        dic = {}
        dl = data.dateline(False)
        for i in range(len(dl)):
            if i == 0:
                emaf = data.get(dl[i]).close
                emas = data.get(dl[i]).close
                dea = 0
            else:
                close = data.get(dl[i]).close
                emaf = 2*close/(macdparan1+1)+(macdparan1-1)*emaf/(macdparan1+1)
                emas = 2*close/(macdparan2+1)+(macdparan2-1)*emas/(macdparan2+1)
                diff = round(emaf-emas,4)
                dea  = round(2*diff/(macdparan3+1)+(macdparan3-1)*dea/(macdparan3+1),4)
                macd = round(2*(diff-dea),4)
                if dl[i]>ld:
                    dic[dl[i]] = (round(emaf,4),round(emas,4),diff,dea,macd)
        self._logger.debug('hyiknow _macd done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _ma(self,code,data):
        self._logger.debug('hyiknow _ma start code[%s] length[%d]'%(code,data.length()))
        ld = self.__codes[code][1]
        dic = {}
        dl = data.dateline(False)
        for i in range(60,len(dl)):
            mas = [5,10,30,60]
            line = []
            for map in mas:
                sum = 0.0
                for j in range(map):
                    sum = sum + data.get(dl[i-j]).close
                line.append(round(sum/float(map),2))
                sum = 0.0
            dic[dl[i]] = tuple(line)
        self._logger.debug('hyiknow _ma done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _vol(self,code,data):
        self._logger.debug('hyiknow _vol start code[%s] length[%d]'%(code,data.length()))
        ld = self.__codes[code][1]
        dic = {}
        dl = data.dateline(False)
        for i in range(20,len(dl)):
            mas = [3,5,10,20]
            line = []
            for map in mas:
                sum = 0.0
                for j in range(map):
                    sum = sum + data.get(dl[i-j]).volwy
                line.append(round(sum,2))
                sum = 0.0
            dic[dl[i]] = tuple(line)
        self._logger.debug('hyiknow _vol done code[%s] length[%d]'%(code,len(dic)))
        return dic
        
    def _blanks(self,code):
        blanks = []
        if self.__codes[code][0]!=self.__codes[code][1]:
            dts = g_tool.exesqlbatch('select date from hy.iknow_data where code=%s and date>%s and date<=%s order by date',(code,self.__codes[code][1],self.__codes[code][0]))
            for dt in dts:
                blanks.append(dt[0])
        if len(blanks)>0:
            self._logger.info('hyiknow deal with [%s] from [%s] to [%s]'%(code,blanks[0],blanks[-1]))
        else:
            self._logger.info('hyiknow deal with [%s] nothing'%code)
        return blanks

    def attr(self,all=False):
        self._logger.info('hyiknow attr task start....')
        self._reload()
        codes = self._upcodes
        if all:
            codes = self._codes()
        total = float(len(codes))
        handled = 0
        for code in codes:
            handled = handled+1
            blanks = self._blanks(code)
            if len(blanks)>0:
                sqls = []
                data = hydata(code)
                kinfo = self._kinfo(code,data)
                kd = self._kd(code,data)
                boll = self._boll(code,data)
                macd = self._macd(code,data)
                ma = self._ma(code,data)
                vol = self._vol(code,data)
                for dt in blanks:
                    if kinfo.has_key(dt) and kd.has_key(dt) and boll.has_key(dt) and macd.has_key(dt) and ma.has_key(dt) and vol.has_key(dt):
                        sqls.append(('insert into hy.iknow_attr(code,date,weekday,hb,lb,kline,csrc,zdf,sfv,k,d,mid,std,emaf,emas,diff,dea,macd,ma5,ma10,ma30,ma60,vol3,vol5,vol10,vol20) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,dt,)+kinfo[dt]+kd[dt]+boll[dt]+macd[dt]+ma[dt]+vol[dt]))
                g_tool.task(sqls)
                self._logger.info('hyiknow attr handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyiknow attr task done....')

    def stone(self):
        self._logger.info('hyiknow stone task start....')
        codes = g_tool.exesqlbatch('select code,name,industry from hy.iknow_watch where active=1',None)
        total = float(len(codes))
        handled = 0
        sqls = [('update hy.iknow_stone set active=active+1',None)]
        for code in codes:
            code = code[0]
            handled = handled+1
            data = hydata(code,59)
            dl = data.dateline()
            self._logger.info('hyiknow stone task date[%s-%s]....'%(dl[0],dl[-1]))
            close = data.get(dl[0]).close
            high = data.get(dl[0]).high
            low = data.get(dl[0]).low
            for j in range(1,8):
                if data.get(dl[j]).high>high:
                    high = data.get(dl[j]).high
                if data.get(dl[j]).low<low:
                    low = data.get(dl[j]).low
            vol4 = data.get(dl[0]).volwy+data.get(dl[1]).volwy+data.get(dl[2]).volwy+data.get(dl[3]).volwy
            s4 = data.getsum(4)
            s9 = data.getsum(9)
            s19 = data.getsum(19)
            s29 = data.getsum(29)
            s59 = data.getsum(59)
            sqls.append(('insert into hy.iknow_stone(code,date,high8,low8,vol4,s4,s9,s19,s29,s59) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,dl[0],high,low,vol4,s4,s9,s19,s29,s59)))
            self._logger.info('hyiknow stone handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
        g_tool.task(sqls)
        self._logger.info('hyiknow stone task done sqls[%d]....'%len(sqls))

    def dl(self):
        self._upcodes = []
        try:
            self._logger.info('hyiknow dl task start....')
            now = datetime.datetime.now()
            self._reload()
            clis = self._codes()
            sqls = []
            defaultstart = '2016-01-01'
            for code in clis:
                try:
                    start = defaultstart
                    if self.__codes.has_key(code):
                        start = self.__codes[code][0]
                    mat = g_tool.dl_upfrom163(code,start)
                    for row in mat:
                        sqls.append(('insert into hy.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                        self._upcodes.append(row[0])
                except Exception,e:
                    self._logger.info('code[%s],date[%04d-%02d-%02d] update failed[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
            self._logger.info('hyiknow handle dl executed sqls[%d]....'%(len(sqls)))
            sqls = []
            for code in clis:
                try:
                    shouldadd = g_tool.exesqlbatch('select date from hs.hs_daily_data where code=%s and date not in (select date from hy.iknow_data where code=%s)',(code,code))
                    for adt in shouldadd:
                        self._logger.info('hyiknow handle dl code[%s] date[%s]....'%(code,adt[0]))
                        row = g_tool.exesqlone('select code,date,open,high,low,close,volh,volwy from hs.hs_daily_data where code=%s and date=%s',(code,adt[0]))
                        sqls.append(('insert into hy.iknow_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                        self._upcodes.append(row[0])
                except Exception,e:
                    self._logger.info('code[%s],date[%04d-%02d-%02d] local update exception[%s]'%(code,now.year,now.month,now.day,e))
            g_tool.task(sqls)
            self._logger.info('hyiknow handle dl check executed sqls[%d]....'%(len(sqls)))
        except Exception,e:
            self._logger.info('hyiknow dl exception[%s]....'%e)
        self._logger.info('hyiknow dl task done....')
        
    def _fv(self,hb,lb,kline):
        fv = 0
        if hb==1 and lb==0 and kline==1:
            fv = 1
        elif hb==1 and lb==0 and kline==0:
            fv = 2
        elif hb==0 and lb==1 and kline==1:
            fv = 3
        elif hb==0 and lb==1 and kline==0:
            fv = 4
        elif hb==1 and lb==1 and kline==1:
            fv = 5
        elif hb==1 and lb==1 and kline==0:
            fv = 6
        elif hb==0 and lb==0 and kline==1:
            fv = 7
        elif hb==0 and lb==0 and kline==0:
            fv = 8
        return fv

    def feature(self,all=False):
        self._logger.info('hyiknow feature task start....')
        codes = self._upcodes
        if all:
            codes = self._codes()
        total = float(len(codes))
        handled = 0
        for code in codes:
            sqls = []
            handled = handled+1
            data = g_tool.exesqlbatch('select date,hb,lb,kline from hy.iknow_attr where code=%s order by date desc',(code,))
            if len(data)<200:
                continue
            if data[199][0]<'2005-01-01':
                continue
            ld = g_tool.exesqlone('select date from hy.iknow_feature where code=%s order by date desc limit 1',(code,))
            start = '2005-01-01'
            if len(ld)>0 and ld[0]:
                start = ld[0]
            mat = []
            for i in range(len(data)-4):
                if data[i][0]<=start:
                    break
                next = self._fv(data[i][1],data[i][2],data[i][3])
                fv = '%d%d%d%d'%(self._fv(data[i+4][1],data[i+4][2],data[i+4][3]),self._fv(data[i+3][1],data[i+3][2],data[i+3][3]),self._fv(data[i+2][1],data[i+2][2],data[i+2][3]),self._fv(data[i+1][1],data[i+1][2],data[i+1][3]))
                ffv = '%d%d%d%d'%(self._fv(data[i+3][1],data[i+3][2],data[i+3][3]),self._fv(data[i+2][1],data[i+2][2],data[i+2][3]),self._fv(data[i+1][1],data[i+1][2],data[i+1][3]),self._fv(data[i][1],data[i][2],data[i][3]))
                ohlc = g_tool.exesqlbatch('select open,high,low,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code,data[i][0]))
                if len(ohlc)==2:
                    openr = round((ohlc[0][0]-ohlc[1][3])/ohlc[1][3],4)
                    highr = round((ohlc[0][1]-ohlc[1][3])/ohlc[1][3],4)
                    lowr = round((ohlc[0][2]-ohlc[1][3])/ohlc[1][3],4)
                    closer = round((ohlc[0][3]-ohlc[1][3])/ohlc[1][3],4)
                    vol = g_tool.exesqlone('select hy.iknow_data.volwy,hy.iknow_attr.vol5 from hy.iknow_data,hy.iknow_attr where hy.iknow_data.code=%s and hy.iknow_data.date=%s and hy.iknow_attr.code=%s and hy.iknow_attr.date=%s',(code,data[i][0],code,data[i][0]))
                    if len(vol)!=0 and vol[0]:
                        vr = round((vol[0]/(vol[1]/5.0)),2)
                        sqls.append(('insert into hy.iknow_feature(code,date,fv,vr,openr,highr,lowr,closer,ffv,next) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,data[i][0],fv,vr,openr,highr,lowr,closer,ffv,next)))
            g_tool.task(sqls)
            self._logger.info('hyiknow feature handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyiknow feature task done....')

    def _guass(self,lis):
        ev = sum(lis)/float(len(lis))
        all = 0.0
        for it in lis:
            all = all + (it-ev)**2
        ev = round(ev,4)
        std = round((all/float(len(lis)))**0.5,4)
        return (ev,std)

    def _statistics(self,count,data):
        prob = round(100*(float(len(data))/count),2)
        olis = []
        hlis = []
        llis = []
        clis = []
        for row in data:
            if row[1]>=0.11 or row[2]<-0.11:
                continue
            olis.append(row[0])
            hlis.append(row[1])
            llis.append(row[2])
            clis.append(row[3])
        olis.sort()
        hlis.sort()
        llis.sort()
        clis.sort()
        if len(olis)>0:
            ogs = self._guass(olis)
            hgs = self._guass(hlis)
            lgs = self._guass(llis)
            cgs = self._guass(clis)
            return (prob,ogs[0],ogs[1],hgs[0],hgs[1],lgs[0],lgs[1],cgs[0],cgs[1])
        else:
            return (0,0,0,0,0,0,0,0,0)

    def prob(self,first=False):
        self._logger.info('hyiknow prob task start....')
        fvs = g_tool.exesqlbatch('select distinct ffv from hy.iknow_feature',None)
        sqls = []
        for fv in fvs:
            self._logger.info('hyiknow prob deal with fv[%s]....'%fv[0])
            cnt = g_tool.exesqlone('select count(*) from hy.iknow_feature where fv=%s',(fv[0],))
            mat = []
            if cnt[0]!=0:
                for i in range(1,9):
                    data = g_tool.exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=%s',(fv[0],i))
                    mat.append(self._statistics(cnt[0],data))
                now = datetime.datetime.now()
                ut = '%04d-%02d-%02d %02d:%02d:%02d'%(now.year,now.month,now.day,now.hour,now.minute,now.second)
                if first:
                    sqls.append(('insert into hy.iknow_prob(fv,count,prob1,omean1,ostd1,hmean1,hstd1,lmean1,lstd1,cmean1,cstd1,prob2,omean2,ostd2,hmean2,hstd2,lmean2,lstd2,cmean2,cstd2,prob3,omean3,ostd3,hmean3,hstd3,lmean3,lstd3,cmean3,cstd3,prob4,omean4,ostd4,hmean4,hstd4,lmean4,lstd4,cmean4,cstd4,prob5,omean5,ostd5,hmean5,hstd5,lmean5,lstd5,cmean5,cstd5,prob6,omean6,ostd6,hmean6,hstd6,lmean6,lstd6,cmean6,cstd6,prob7,omean7,ostd7,hmean7,hstd7,lmean7,lstd7,cmean7,cstd7,prob8,omean8,ostd8,hmean8,hstd8,lmean8,lstd8,cmean8,cstd8,updatetime) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(fv[0],cnt[0])+mat[0]+mat[1]+mat[2]+mat[3]+mat[4]+mat[5]+mat[6]+mat[7]+(ut,)))
                else:
                    sqls.append(('update hy.iknow_prob set count=%s,prob1=%s,omean1=%s,ostd1=%s,hmean1=%s,hstd1=%s,lmean1=%s,lstd1=%s,cmean1=%s,cstd1=%s,prob2=%s,omean2=%s,ostd2=%s,hmean2=%s,hstd2=%s,lmean2=%s,lstd2=%s,cmean2=%s,cstd2=%s,prob3=%s,omean3=%s,ostd3=%s,hmean3=%s,hstd3=%s,lmean3=%s,lstd3=%s,cmean3=%s,cstd3=%s,prob4=%s,omean4=%s,ostd4=%s,hmean4=%s,hstd4=%s,lmean4=%s,lstd4=%s,cmean4=%s,cstd4=%s,prob5=%s,omean5=%s,ostd5=%s,hmean5=%s,hstd5=%s,lmean5=%s,lstd5=%s,cmean5=%s,cstd5=%s,prob6=%s,omean6=%s,ostd6=%s,hmean6=%s,hstd1=%s,lmean6=%s,lstd6=%s,cmean6=%s,cstd6=%s,prob7=%s,omean7=%s,ostd7=%s,hmean7=%s,hstd7=%s,lmean7=%s,lstd7=%s,cmean7=%s,cstd7=%s,prob8=%s,omean8=%s,ostd8=%s,hmean8=%s,hstd8=%s,lmean8=%s,lstd8=%s,cmean8=%s,cstd8=%s,updatetime=%s where fv=%s',((cnt[0],)+mat[0]+mat[1]+mat[2]+mat[3]+mat[4]+mat[5]+mat[6]+mat[7]+(ut,fv[0]))))
        g_tool.task(sqls)
        self._logger.info('hyiknow prob task done....')

    def _get(self,code,date,dic):
        pass
        
    def mprob(self,all=False):
        self._logger.info('hyiknow mprob task start....')
        codes = self._upcodes
        if all:
            codes = self._codes()
        total = float(len(codes))
        handled = 0
        start = '2018-01-01'
        for code in codes:
            ld = g_tool.exesqlone('select date,p1,p2,p3,p4,p5,p6,p7,p8 from hy.iknow_mprob where code=%s order by date desc limit 1',(code,))
            if len(ld)!=0 and ld[0]:
                start = ld[0]
            else:
                fvs = g_tool.exesqlbatch('select ffv from hy.iknow_feature where code=%s and date>%s',(code,start))
                
        self._logger.info('hyiknow mprob task done....')

    def daily_task(self,name):
        g_tool.reconn('hy')
        self._logger.info('daily_task[%s] start....'%(name))
        self.dl()
        self.attr()
        self.feature()
        self.prob()
        self.stone()
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
    ik.run()
    
    
    