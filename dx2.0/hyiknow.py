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

IK_STATUS_BREAK_UP = 1
IK_STATUS_BREAK_DN = 2
IK_STATUS_DEVIATION_UP = 3
IK_STATUS_DEVIATION_DN = 4
IK_STATUS_REBOUND_UP = 5 
IK_STATUS_REBOUND_DN = 6
IK_STATUS_STAND_UP = 7
IK_STATUS_STAND_DN = 8
IK_STATUS_OPEN_UP = 9
IK_STATUS_OPEN_DN = 10
IK_STATUS_ADJUST_UP = 11
IK_STATUS_ADJUST_DN = 12
IK_STATUS_MA5_UP = 51
IK_STATUS_MA5_DN = 52
IK_STATUS_MA10_UP = 53
IK_STATUS_MA10_DN = 54
IK_STATUS_MA20_UP = 55
IK_STATUS_MA20_DN = 56
IK_STATUS_MA30_UP = 57
IK_STATUS_MA30_DN = 58
IK_STATUS_MA60_UP = 59
IK_STATUS_MA60_DN = 60

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
        data = g_tool.exesqlbatch('select code from hy.iknow_name order by code', None)
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
            dic[dl[i]] = (hb,lb,k,csrc,zdf,fv)
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
                        sqls.append(('insert into hy.iknow_attr(code,date,hb,lb,kline,csrc,zdf,sfv,k,d,mid,std,emaf,emas,diff,dea,macd,ma5,ma10,ma30,ma60,vol3,vol5,vol10,vol20) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,dt,)+kinfo[dt]+kd[dt]+boll[dt]+macd[dt]+ma[dt]+vol[dt]))
                g_tool.task(sqls)
                self._logger.info('hyiknow attr handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyiknow attr task done....')

    def stone(self):
        self._logger.info('hyiknow stone task start....')
        codes = g_tool.exesqlbatch('select code,name,industry from hy.iknow_watch where active=1',None)
        total = float(len(codes))
        handled = 0
        sqls = [('update hy.iknow_stone set active=0',None)]
        for code in codes:
            code = code[0]
            handled = handled+1
            data = hydata(code,59)
            dl = data.dateline()
            close = data.get(dl[0]).close
            high = data.get(dl[0]).high
            low = data.get(dl[0]).low
            for j in range(1,8):
                if data.get(dl[j]).high>high:
                    high = data.get(dl[j]).high
                if data.get(dl[j]).low<low:
                    low = data.get(dl[j]).low
            s4 = data.getsum(4)
            s9 = data.getsum(9)
            s19 = data.getsum(19)
            s29 = data.getsum(29)
            s59 = data.getsum(59)
            sqls.append(('insert into hy.iknow_stone(code,date,high8,low8,s4,s9,s19,s29,s59) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,dl[0],high,low,s4,s9,s19,s29,s59)))
            self._logger.info('hyiknow stone handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code))
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
                    sqls.append(('insert into hy.iknow_feature(code,date,fv,openr,highr,lowr,closer,ffv,next) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,data[i][0],fv,openr,highr,lowr,closer,ffv,next)))
            g_tool.task(sqls)
            self._logger.info('hyiknow feature handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyiknow feature task done....')

    def _broken(self,redm,grem,macds,code,date,volwy):
        dic = {}
        if macds[0]>=redm and (macds[1]<0 or macds[2]<0):
            dic[(code,date,IK_STATUS_BREAK_UP)] = volwy
        elif macds[0]<=grem and (macds[1]>0 or macds[2]>0):
            dic[(code,date,IK_STATUS_BREAK_DN)] = volwy
        return dic
            
    def _deviation(self,redm,grem,macds,code,date,volwy):
        dic = {}
        if macds[0]<0 and macds[1]<grem and macds[0]>macds[1]:
            lb = g_tool.exesqlone('select lb from hy.iknow_attr where code=%s and date=%s', (code,date))
            if len(lb)>0 and lb[0] and lb[0]==1:
                dic[(code,date,IK_STATUS_DEVIATION_UP)] = volwy
        elif macds[0]>0 and macds[1]>redm and macds[0]<macds[1]:
            hb = g_tool.exesqlone('select hb from hy.iknow_attr where code=%s and date=%s', (code,date))
            if len(hb)>0 and hb[0] and hb[0]==1:
                dic[(code,date,IK_STATUS_DEVIATION_DN)] = volwy
        return dic

    def _rebound(self,macds,code,date,volwy):
        dic = {}
        if macds[0]<0 and macds[0]>macds[1]:
            lb = g_tool.exesqlone('select lb from hy.iknow_attr where code=%s and date=%s', (code,date))
            if len(lb)>0 and lb[0] and lb[0]==1:
                kd = g_tool.exesqlone('select k,d from hy.iknow_attr where code=%s and date=%s',(code,date))
                if len(kd)>0 and kd[0]>kd[1]:
                    dic[(code,date,IK_STATUS_REBOUND_UP)] = volwy
        elif macds[0]>0 and macds[0]<macds[1]:
            hb = g_tool.exesqlone('select lb from hy.iknow_attr where code=%s and date=%s', (code,date))
            if len(hb)>0 and hb[0] and hb[0]==1:
                kd = g_tool.exesqlone('select k,d from hy.iknow_attr where code=%s and date=%s',(code,date))
                if kd[0]<kd[1]:
                    dic[(code,date,IK_STATUS_REBOUND_DN)] = volwy
        return dic
                    
    def _stand(self,closes,mids,k,d,code,date,volwy):
        dic = {}
        if closes[0]>mids[0] and closes[1]<mids[1] and k>d:
            dic[(code,date,IK_STATUS_STAND_UP)] = volwy
        elif closes[0]<mids[0] and closes[1]>mids[1] and k<d:
            dic[(code,date,IK_STATUS_STAND_DN)] = volwy
        return dic
    
    def _open(self,stdm,closes,mids,stds,code,date,volwy):
        dic = {}
        if stds[0]>stdm and stds[1]<stdm:
            if closes[0]>mids[0]+2*stds[0] and closes[1]<mids[1]+2*stds[1]:
                dic[(code,date,IK_STATUS_OPEN_UP)] = volwy
            elif closes[0]<mids[0]-2*stds[0] and closes[1]>mids[1]-2*stds[1]:
                dic[(code,date,IK_STATUS_OPEN_DN)] = volwy
        return dic
    
    def _adjust(self,stdm,code,date,volwy):
        dic = {}
        pds = g_tool.exesqlbatch('select date,high,low,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 20',(code,date))
        std = g_tool.exesqlone('select std,mid from hy.iknow_attr where code=%s and date=%s',(code,date))
        if date==pds[0][0] and len(std)>0 and std[0] and std[0]>stdm and len(pds)==20:
            if pds[0][2]<std[1] and pds[0][3]>std[1]:
                for i in range(1,19):
                    dt = pds[i][0]
                    high = pds[i][1]
                    close = pds[i][3]
                    if high>pds[i+1][1] and high>pds[i-1][1]:
                        up = g_tool.exesqlone('select mid+2*std from hy.iknow_attr where code=%s and date=%s',(code,dt))
                        if len(up)>0 and up[0] and high>up[0]:
                            dic[(code,date,IK_STATUS_ADJUST_UP)] = volwy
                            break
                    else:
                        mid = g_tool.exesqlone('select mid from hy.iknow_attr where code=%s and date=%s',(code,dt))
                        if len(mid)>0 and mid[0] and close<mid[0]:
                            break
            elif pds[0][1]>std[1] and pds[0][3]<std[1]:
                for i in range(1,19):
                    dt = pds[i][0]
                    low = pds[i][2]
                    close = pds[i][3]
                    if low<pds[i+1][2] and low>pds[i-1][3]:
                        dn = g_tool.exesqlone('select mid-2*std from hy.iknow_attr where code=%s and date=%s',(code,dt))
                        if len(dn)>0 and dn[0] and low<dn[0]:
                            dic[(code,date,IK_STATUS_ADJUST_DN)] = volwy
                            break
                    else:
                        mid = g_tool.exesqlone('select mid from hy.iknow_attr where code=%s and date=%s',(code,dt))
                        if len(mid)>0 and mid[0] and close>mid[0]:
                            break
        return dic
                
    def _status(self,date):
        self._logger.info('hyiknow _status task[%s] start....'%date)
        codes = g_tool.exesqlbatch('select code,volwy from hy.iknow_data where date=%s',(date,))
        total = float(len(codes))
        handled = 0
        dic = {}
        for code in codes:
            handled = handled + 1
            redm = g_tool.exesqlbatch('select macd from hy.iknow_attr where code=%s and date<=%s and macd>0 order by macd',(code[0],date))
            grem = g_tool.exesqlbatch('select macd from hy.iknow_attr where code=%s and date<=%s and macd<0 order by macd',(code[0],date))
            ms = g_tool.exesqlbatch('select date,macd from hy.iknow_attr where code=%s and date<=%s order by date desc limit 3',(code[0],date))
            if len(redm)>0 and redm[0] and len(grem)>0 and grem[0]:
                redm = redm[len(redm)/2][0]
                grem = grem[len(grem)/2][0]
                if len(ms)==3 and ms[0][0]==date:
                    dic.update(self._broken(redm,grem,(ms[0][1],ms[1][1],ms[2][1]),code[0],date,code[1]))
                if len(ms)>=2 and ms[0][0]==date:
                    dic.update(self._deviation(redm,grem,(ms[0][1],ms[1][1]),code[0],date,code[1]))
            if len(ms)>=2 and ms[0][0]==date:
                dic.update(self._rebound((ms[0][1],ms[1][1]),code[0],date,code[1]))
            pd = g_tool.exesqlbatch('select date,close from hy.iknow_data where code=%s and date<=%s order by date desc limit 2',(code[0],date))
            stdm = g_tool.exesqlbatch('select std from hy.iknow_attr where code=%s and date<=%s order by std',(code[0],date))
            if len(stdm)>0 and stdm[0]:
                stdm = stdm[len(stdm)/2][0]
                if len(pd)==2 and pd[0][0]==date:
                    mid = g_tool.exesqlone('select mid,std,k,d from hy.iknow_attr where code=%s and date=%s',(code[0],pd[0][0]))
                    midp = g_tool.exesqlone('select mid,std from hy.iknow_attr where code=%s and date=%s',(code[0],pd[1][0]))
                    if len(mid)>0 and mid[0] and len(midp)>0 and midp[0]:
                        dic.update(self._stand((pd[0][1],pd[1][1]),(mid[0],midp[0]),mid[2],mid[3],code[0],date,code[1]))
                        dic.update(self._open(stdm,(pd[0][1],pd[1][1]),(mid[0],midp[0]),(mid[1],midp[1]),code[0],date,code[1]))
                dic.update(self._adjust(stdm,code[0],date,code[1]))
            self._logger.info('hyiknow _status handle progress[%0.2f%%] date[%s] code[%s]....'%(100*(handled/total),date,code[0]))
        self._logger.info('hyiknow _status task[%s] done prepared sqls[%d]....'%(date,len(dic)))
        return dic

    def _ma_up_dn(self,date):
        self._logger.info('iknow _ma_up_dn[%s] task start....'%date)
        dic = {}
        insqls = [('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close>=hy.iknow_attr.ma5',(date,date),IK_STATUS_MA5_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close<hy.iknow_attr.ma5',(date,date),IK_STATUS_MA5_DN),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close>=hy.iknow_attr.ma10',(date,date),IK_STATUS_MA10_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close<hy.iknow_attr.ma10',(date,date),IK_STATUS_MA10_DN),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close>=hy.iknow_attr.mid',(date,date),IK_STATUS_MA20_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close<hy.iknow_attr.mid',(date,date),IK_STATUS_MA20_DN),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close>=hy.iknow_attr.ma30',(date,date),IK_STATUS_MA30_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close<hy.iknow_attr.ma30',(date,date),IK_STATUS_MA30_DN),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close>=hy.iknow_attr.ma60',(date,date),IK_STATUS_MA60_UP),('select hy.iknow_data.code,hy.iknow_data.volwy from hy.iknow_data,hy.iknow_attr where hy.iknow_data.date=%s and hy.iknow_attr.date=%s and hy.iknow_data.code=hy.iknow_attr.code and hy.iknow_data.close<hy.iknow_attr.ma30',(date,date),IK_STATUS_MA60_DN),]
        for sql in insqls:
            output = g_tool.exesqlbatch(sql[0],sql[1])
            for row in output:
                dic[(row[0],date,sql[2])] = row[1]
        self._logger.info('iknow _ma_up_dn[%s] task done prepared sqls[%d]....'%(date,len(dic)))
        return dic
        
    def _transsqls(self,dic):
        sqls = []
        for key in dic.keys():
            sqls.append(('insert into hy.iknow_status(code,date,status,volwy) values(%s,%s,%s,%s)',(key[0],key[1],key[2],dic[key])))
        return sqls
        
    def status(self):
        self._logger.info('hyiknow status task start....')
        start = '2018-01-01'
        dts = g_tool.exesqlbatch('select distinct date from hy.iknow_data where date>%s and date not in (select distinct date from hy.iknow_status) order by date desc',(start,))
        for dt in dts:
            self._logger.info('hyiknow status task deal with date[%s] start'%dt[0])
            dic = {}
            dic.update(self._status(dt[0]))
            dic.update(self._ma_up_dn(dt[0]))
            sqls = self._transsqls(dic)
            g_tool.task(sqls)
            self._logger.info('hyiknow status task deal with date[%s] done sqls[%d]'%(dt[0],len(sqls)))
        self._logger.info('hyiknow status task done....')
        
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
        
    def classify(self):
        self._logger.info('hyiknow classify task start....')
        start = '2018-07-01'
        dts = g_tool.exesqlbatch('select distinct date from hy.iknow_data where date>%s and date not in (select distinct date from hy.iknow_classify) order by date desc',(start,))
        tags = g_tool.exesqlbatch('select distinct tag,tagtype from hy.iknow_tags',None)
        for dt in dts:
            self._logger.info('hyiknow classify task deal with date[%s] start'%dt[0])
            sqls = []
            for tg in tags:
                tag = tg[0]
                typ = tg[1]
                cnt = g_tool.exesqlone('select count(*) from hy.iknow_tags where tag=%s',(tag,))
                hbs = g_tool.exesqlone('select count(*) from hy.iknow_attr where date=%s and hb=1 and code in (select code from hy.iknow_tags where tag=%s)',(dt[0],tag))
                lbs = g_tool.exesqlone('select count(*) from hy.iknow_attr where date=%s and lb=1 and code in (select code from hy.iknow_tags where tag=%s)',(dt[0],tag))
                csrc = g_tool.exesqlone('select avg(csrc) from hy.iknow_attr where date=%s and code in (select code from hy.iknow_tags where tag=%s)',(dt[0],tag))
                zdf = g_tool.exesqlone('select avg(zdf) from hy.iknow_attr where date=%s and code in (select code from hy.iknow_tags where tag=%s)',(dt[0],tag))
                if cnt[0]!=0:
                    hbr = round(float(hbs[0])/float(cnt[0]),4)
                    lbr = round(float(lbs[0])/float(cnt[0]),4)
                    csrc = round(csrc[0],4)
                    zdf = round(zdf[0],4)
                    sqls.append(('insert into hy.iknow_classify(name,date,type,count,hbr,lbr,csrc,zdfev) values(%s,%s,%s,%s,%s,%s,%s,%s)',(tag,dt[0],typ,cnt[0],hbr,lbr,csrc,zdf)))
            g_tool.task(sqls)
            self._logger.info('hyiknow classify task deal with date[%s] done sqls[%d]'%(dt[0],len(sqls)))
        self._logger.info('hyiknow classify task done....')

    def daily_task(self,name):
        g_tool.reconn('hy')
        self._logger.info('daily_task[%s] start....'%(name))
        self.dl()
        self.attr()
        self.feature()
        self.status()
        self.prob()
        self.stone()
        self.classify()
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
    
    
    