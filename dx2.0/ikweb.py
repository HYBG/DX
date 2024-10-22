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
import web
import json
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

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

class hyhq:
    def __init__(self,code,open,high,low,close,lastclose,volwy,volh,date,time):
        self.code = code
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volwy = volwy
        self.lastclose = lastclose
        self.volh = volh
        self.date = date
        self.time = time

    def zdf(self):
        return round(100*((self.close-self.lastclose)/self.lastclose),2)

class hyprob:
    def __init__(self,prob,openr,highr,lowr,closer):
        self.prob = prob
        self.openr = openr
        self.highr = highr
        self.lowr = lowr
        self.closer = closer

    def standardize(self):
        return [self.prob,self.openr,self.highr,self.lowr,self.closer]

class hynext:
    def __init__(self,code,name,date,fv,hr,lr,mat):
        self.code = code
        self.name = name
        self.date = date
        self.fv = fv
        self.hr = hr
        self.lr = lr
        self.p1 = hyprob(mat[0][0],mat[0][1],mat[0][2],mat[0][3],mat[0][4])
        self.p2 = hyprob(mat[1][0],mat[1][1],mat[1][2],mat[1][3],mat[1][4])
        self.p3 = hyprob(mat[2][0],mat[2][1],mat[2][2],mat[2][3],mat[2][4])
        self.p4 = hyprob(mat[3][0],mat[3][1],mat[3][2],mat[3][3],mat[3][4])
        self.p5 = hyprob(mat[4][0],mat[4][1],mat[4][2],mat[4][3],mat[4][4])
        self.p6 = hyprob(mat[5][0],mat[5][1],mat[5][2],mat[5][3],mat[5][4])
        self.p7 = hyprob(mat[6][0],mat[6][1],mat[6][2],mat[6][3],mat[6][4])
        self.p8 = hyprob(mat[7][0],mat[7][1],mat[7][2],mat[7][3],mat[7][4])

    def standardize(self):
        return {'code':self.code,'name':self.name,'date':self.date,'fv':self.fv,'hr':self.hr,'lr':self.lr,'p1':self.p1.standardize(),'p2':self.p2.standardize(),'p3':self.p3.standardize(),'p4':self.p4.standardize(),'p5':self.p5.standardize(),'p6':self.p6.standardize(),'p7':self.p7.standardize(),'p8':self.p8.standardize()}

class ikweb:
    def __init__(self,home='/var/data/iknow'):
        self._logger = logging.getLogger('ikweb')
        self._loglevel = logging.INFO
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logd = os.path.join(home,'log')
        logfile = os.path.join(logd,'ikweb.log')
        rh = RotatingFileHandler(logfile, maxBytes=50*1024*1024,backupCount=10)
        rh.setLevel(self._loglevel)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(self._loglevel)
        self._connection = None
        self._cursor = None
        self._conn('hy')

    def __del__(self):
        if not self._cursor:
            self._cursor.close()
        if not self._connection:
            self._connection.close()

    def _conn(self,dbname):
        try:
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('iknow connect db[%s] error[%s]'%(dbname,e))
        return False

    def _reconn(self,dbname):
        try:
            self._cursor.close()
            self._connection.close()
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('iknow reconnect db[%s] error[%s]'%(dbname,e))
        return False

    def _exesqlone(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n==1:
            ret = self._cursor.fetchone()
        return ret

    def _exesqlbatch(self,sql,param):
        n = 0
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n>0:
            ret = self._cursor.fetchall()
        return ret
        
    def _task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    self._logger.info('iknow execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                self._logger.error('iknow execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._connection.rollback()
                return False
        self._connection.commit()
        return True

    def _getname(self,code):
        names = self._exesqlone('select name,tag from hy.iknow_tags where code=%s and tagtype=%s',(code,'industry'))
        return (names[0],names[1])

    def _lastday(self,code):
        ld = ['']
        if code:
            ld = self._exesqlone('select date from hy.iknow_data where code=%s order by date desc limit 1',(code,))
        else:
            ld = self._exesqlone('select date from hy.iknow_data order by date desc limit 1',None)
        return ld[0]
        
    def _preparenext(self,code,date):
        data = self._exesqlone('select hy.iknow_data.high,hy.iknow_data.low,hy.iknow_data.close,hy.iknow_data.volwy,hy.iknow_attr.vol5,hy.iknow_feature.ffv from hy.iknow_data,hy.iknow_attr,hy.iknow_feature where hy.iknow_data.code=%s and hy.iknow_data.date=%s and hy.iknow_attr.code=%s and hy.iknow_attr.date=%s and hy.iknow_feature.code=%s and hy.iknow_feature.date=%s',(code,date,code,date,code,date))
        if len(data)!=0 and data[0]:
            fv = data[5]
            hr = round((data[0]-data[2])/data[2],4)
            lr = round((data[1]-data[2])/data[2],4)
            vr = round(data[3]/(data[4]/5.0),2)
            return (fv,hr,lr,vr)
        return None
        
    def _getmadistribution(self,date,ma,direction):
        sig = '<'
        if direction==1: #up
            sig = '>'
        field = 'ma5'
        if ma == 10:
            field = 'ma10'
        elif ma == 20:
            field = 'ma20'
        elif ma == 30:
            field = 'ma30'
        elif ma == 60:
            field = 'ma60'
        codes = self._exesqlbatch('select iknow_data.code from iknow_attr,iknow_data where iknow_attr.date=%s and iknow_data.date=%s and iknow_data.close'+sig+'iknow_attr.'+field+' and iknow_data.code=iknow_attr.code',(date,date))
        return codes

    def _rtprice(self,codes):
        codeliststr = ''
        for code in codes:
            market = None
            if code[:2]=='60' or code[0]=='5':
                market = 'sh'
            else:
                market = 'sz'
            codeliststr = codeliststr + '%s%s,'%(market,code)
        url = 'http://hq.sinajs.cn/list=%s'%(codeliststr[:-1])
        try:
            data = urllib2.urlopen(url).readlines()
            i = 0
            lis = []
            for line in data:
                try:
                    info = line.split('"')[1].split(',')
                    now = datetime.datetime.now()
                    if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
                        hq = hyhq(codes[i],float(info[1]),float(info[4]),float(info[5]),float(info[3]),float(info[2]),float(info[9])/10000.0,float(info[8])/100,info[30],info[31])
                        lis.append(hq)
                except Exception, e:
                    self._logger.error('get current price codes[%s] exception[%s]'%(codes[i],e))
                i = i+1
            return lis
        except Exception, e:
            self._logger.error('get current price codes[%d] url[%s] exception[%s]'%(len(codes),url,e))
            return None

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

    def _middles(self,all,sets):
        if len(sets)!=0:
            prob = round(100*(float(len(sets))/all),2)
            opens = []
            highs = []
            lows = []
            closes = []
            for row in sets:
                opens.append(row[0])
                highs.append(row[1])
                lows.append(row[2])
                closes.append(row[3])
            opens.sort()
            highs.sort()
            lows.sort()
            closes.sort()
            return (prob,opens[len(opens)/2],highs[len(highs)/2],lows[len(lows)/2],closes[len(closes)/2])
        return (0,0,0,0,0)

    def _next(self,fv,hr,lr,vr,details=True):
        mat = []
        dn = 0.6
        up = 1.4
        vcond = 'vr<=%s'%(dn)
        if vr>=up:
            vcond = 'vr>=%s'%str(up)
        elif vr>=dn:
            vcond = 'vr>%s and vr<%s'%(str(dn),str(up))
        all = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8))',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
        base = 1000000000
        if all[0]!=0:
            base = all[0]
        if details:
            c1 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=1',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(self._middles(all[0],c1))
            c2 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=2',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(self._middles(all[0],c2))
            c3 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=3',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(self._middles(all[0],c3))
            c4 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=4',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(self._middles(all[0],c4))
            c5 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=5',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(self._middles(all[0],c5))
            c6 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=6',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(self._middles(all[0],c6))
            c7 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=7',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(self._middles(all[0],c7))
            c8 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=8',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(self._middles(all[0],c8))
        else:
            c1 = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=1',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(round(100*(float(c1[0])/base),2))
            c2 = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=2',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(round(100*(float(c2[0])/base),2))
            c3 = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=3',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(round(100*(float(c3[0])/base),2))
            c4 = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=4',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(round(100*(float(c4[0])/base),2))
            c5 = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=5',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(round(100*(float(c5[0])/base),2))
            c6 = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=6',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(round(100*(float(c6[0])/base),2))
            c7 = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=7',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(round(100*(float(c7[0])/base),2))
            c8 = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s and '+vcond+' and not ((highr<=%s or lowr<%s) and (next=1 or next=2)) and not ((lowr>=%s or highr>%s) and (next=3 or next=4)) and not ((highr<=%s or lowr>=%s) and (next=5 or next=6)) and not ((highr>%s or lowr<%s) and (next=7 or next=8)) and next=8',(fv,hr,lr,hr,lr,hr,lr,hr,lr))
            mat.append(round(100*(float(c8[0])/base),2))
        return (all[0],mat)

    def q_watch(self,paras):
        date = ''
        if not paras.has_key('date'):
            date = self._lastday(None)
        else:
            date = paras['date']
        codes = self._exesqlbatch('select code from hy.iknow_watch where active=1',None)
        mat = []
        for code in codes:
            code = code[0]
            data = self._exesqlone('select iknow_tags.name,iknow_tags.tag,iknow_data.volwy from hy.iknow_tags,iknow_data where iknow_tags.code=%s and iknow_tags.tagtype=%s and iknow_data.code=%s and iknow_data.date=%s',(code,'industry',code,date))
            if len(data)!=0 and data[0]:
                name = data[0]
                ind = data[1]
                volwy = data[2]
                prep = self._preparenext(code,date)
                if prep:
                    next = self._next(prep[0],prep[1],prep[2],prep[3],False)
                    mat.append((code,name,ind,volwy,prep[0],next[0],next[1]))
        mat.sort(reverse=True,key=lambda x:x[6][0])
        return json.dumps(mat)

    def q_list(self,paras):
        lis = []
        for name in dir(self):
            if name[:2]=='q_':
                lis.append(name)
        return json.dumps(lis)
        
    def q_code(self,paras):
        if not paras.has_key('code'):
            return self.defaultoutput({'output':'code missing'})
        code = paras['code']
        date = ''
        if not paras.has_key('date'):
            date = self._lastday(code)
        else:
            date = paras['date']
        data = self._exesqlone('select iknow_tags.name,iknow_tags.tag,iknow_attr.zdf,iknow_attr.ma5,iknow_attr.ma10,iknow_attr.mid,iknow_attr.ma30,iknow_attr.ma60,iknow_attr.csrc,iknow_attr.k,iknow_attr.d,iknow_attr.macd,iknow_data.close,iknow_data.volwy from hy.iknow_tags,iknow_attr,iknow_data where iknow_tags.code=%s and iknow_tags.tagtype=%s and iknow_attr.code=%s and iknow_attr.date=%s and iknow_data.code=%s and iknow_data.date=%s',(code,'industry',code,date,code,date))
        output = []
        if len(data)!=0 and data[0]:
            name = data[0]
            ind = data[1]
            zdf = data[2]
            ma5 = data[3]
            ma10 = data[4]
            ma20 = data[5]
            ma30 = data[6]
            ma60 = data[7]
            csrc = data[8]
            k = data[9]
            d = data[10]
            macd = data[11]
            close = data[12]
            volwy = data[13]
            prep = self._preparenext(code,date)
            if prep:
                fv = prep[0]
                vr = prep[3]
                next = self._next(fv,prep[1],prep[2],vr)
                mas = []
                mas.append((ma5,'ma5'))
                mas.append((ma10,'ma10'))
                mas.append((ma20,'ma20'))
                mas.append((ma30,'ma30'))
                mas.append((ma60,'ma60'))
                mas.append((close,'close'))
                mas.sort(reverse=True)
                base = [code,name,ind,date,close,zdf,volwy,vr,fv,next[0],100*csrc,k,d,macd]
                output = [base,mas,next[1]]
        return json.dumps(output)

    def q_base(self,paras):
        lim = 40
        if paras.has_key('max'):
            lim = int(paras['max'])
        mat = []
        dts = self._exesqlbatch('select distinct date from hy.iknow_attr order by date desc limit %d'%lim,None)
        for dt in dts:
            allcnt = self._exesqlone('select count(*) from hy.iknow_watch where active=1 and code in (select code from hy.iknow_attr where date=%s)',(dt[0],))
            hbc = self._exesqlone('select count(*) from hy.iknow_data where date=%s and code in (select code from hy.iknow_watch where active=1) and code in (select code from hy.iknow_attr where date=%s and hb=1)',(dt[0],dt[0]))
            lbc = self._exesqlone('select count(*) from hy.iknow_data where date=%s and code in (select code from hy.iknow_watch where active=1) and code in (select code from hy.iknow_attr where date=%s and lb=1)',(dt[0],dt[0]))
            all = self._exesqlone('select sum(volwy) from hy.iknow_data where date=%s and code in (select code from hy.iknow_watch where active=1)',(dt[0],))
            hbs = self._exesqlone('select sum(volwy) from hy.iknow_data where date=%s and code in (select code from hy.iknow_watch where active=1) and code in (select code from hy.iknow_attr where date=%s and hb=1)',(dt[0],dt[0]))
            lbs = self._exesqlone('select sum(volwy) from hy.iknow_data where date=%s and code in (select code from hy.iknow_watch where active=1) and code in (select code from hy.iknow_attr where date=%s and lb=1)',(dt[0],dt[0]))
            src = self._exesqlone('select avg(csrc) from hy.iknow_attr where date=%s and code in (select code from hy.iknow_watch where active=1)',(dt[0],))
            mat.append((dt[0],allcnt[0],round((100*(float(hbc[0])/allcnt[0])),2),round(100*(float(lbc[0])/allcnt[0]),2),all[0],round(100*(float(hbs[0])/all[0]),2),round(100*(float(lbs[0])/all[0]),2),round(100*src[0],2)))
        return json.dumps(mat)

    def _spnext(self,code,date):
        rows = self._exesqlbatch('select hb,lb,kline from hy.iknow_attr where date<=%s and code=%s order by date desc limit 4',(date,code))
        fv = '%d%d%d%d'%(self._fv(rows[3][0],rows[3][1],rows[3][2]),self._fv(rows[2][0],rows[2][1],rows[2][2]),self._fv(rows[1][0],rows[1][1],rows[1][2]),self._fv(rows[0][0],rows[0][1],rows[0][2]))
        hlr = self._exesqlone('select (high-close)/close,(low-close)/close from hy.iknow_data where code=%s and date=%s',(code,date))
        hr = round(hlr[0],4)
        lr = round(hlr[1],4)
        mat = self._next(fv,hr,lr)
        dic = {'code':code,'date':date,'time':'15:00:00','fv':fv,'data':mat}
        return dic

    def q_next(self,paras):
        if not paras.has_key('code'):
            return self.defaultoutput({'output':'code missing'})
        code = paras['code']
        date = ''
        rt = True
        if not paras.has_key('date'):
            date = self._exesqlone('select date from hy.iknow_data order by date desc limit 1',None)
            date = date[0]
        else:
            date = paras['date']
            rt = False
        dic = {}
        if rt:
            hq = self._rtprice([code])
            if hq and hq[0].date>date:
                hl = self._exesqlone('select high,low from hy.iknow_data where code=%s and date=%s',(code,date))
                hb = 0
                if hq[0].high>hl[0]:
                    hb = 1
                lb = 0
                if hq[0].low<hl[1]:
                    lb = 1
                k = 0
                if hq[0].close>hq[0].open:
                    k = 1
                rows = self._exesqlbatch('select hb,lb,kline from hy.iknow_attr where date<=%s and code=%s order by date desc limit 3',(date,code))
                fv = '%d%d%d%d'%(self._fv(rows[2][0],rows[2][1],rows[2][2]),self._fv(rows[1][0],rows[1][1],rows[1][2]),self._fv(rows[0][0],rows[0][1],rows[0][2]),self._fv(hb,lb,k))
                hr = round((hq[0].high-hq[0].close)/hq[0].close,4)
                lr = round((hq[0].low-hq[0].close)/hq[0].close,4)
                mat = self._next(fv,hr,lr)
                dic = {'code':code,'date':hq[0].date,'time':hq[0].time,'fv':fv,'data':mat}
            else:
                dic = self._spnext(code,date)
        else:
            dic = self._spnext(code,date)
        return json.dumps(dic)
        
    def q_fvnext(self,paras):
        if not paras.has_key('fv'):
            return self.defaultoutput({'output':'fv missing'})
        fv = paras['fv']
        mat = []
        all = self._exesqlone('select count(*) from hy.iknow_feature where fv=%s',(fv,))
        c1 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=1',(fv,))
        mat.append(self._middles(all[0],c1))
        c2 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=2',(fv,))
        mat.append(self._middles(all[0],c2))
        c3 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=3',(fv,))
        mat.append(self._middles(all[0],c3))
        c4 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=4',(fv,))
        mat.append(self._middles(all[0],c4))
        c5 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=5',(fv,))
        mat.append(self._middles(all[0],c5))
        c6 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=6',(fv,))
        mat.append(self._middles(all[0],c6))
        c7 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=7',(fv,))
        mat.append(self._middles(all[0],c7))
        c8 = self._exesqlbatch('select openr,highr,lowr,closer from hy.iknow_feature where fv=%s and next=8',(fv,))
        mat.append(self._middles(all[0],c8))
        dic = {'fv':fv,'data':mat}
        return json.dumps(dic)
        
    def q_rt(self,paras):
        data = self._exesqlbatch('select code,datetime,name,industry,zdf,hb,lb,csrc,volwy,vr,k,d,macd,fv,fvcnt,close,closemid,ma5,ma10,ma20,ma30,ma60,prob1,openmid1,highmid1,lowmid1,closemid1,prob2,openmid2,highmid2,lowmid2,closemid2,prob3,openmid3,highmid3,lowmid3,closemid3,prob4,openmid4,highmid4,lowmid4,closemid4,prob5,openmid5,highmid5,lowmid5,closemid5,prob6,openmid6,highmid6,lowmid6,closemid6,prob7,openmid7,highmid7,lowmid7,closemid7,prob8,openmid8,highmid8,lowmid8,closemid8 from hy.iknow_rt where active=1 order by prob1 desc',None)
        mat = []
        hbc = 0
        lbc = 0
        csrc = 0
        for row in data:
            if (row[22]>50):
                mat.append(row)
            if row[5]==1:
                hbc = hbc + 1
            if row[6]==1:
                lbc = lbc + 1
            csrc = csrc + row[7]
        hbr = round(100*(hbc/float(len(data))),2)
        lbr = round(100*(lbc/float(len(data))),2)
        csrc = round(csrc/float(len(data)),2)
        return json.dumps([hbr,lbr,csrc,mat])

    def q_codert(self,paras):
        if not paras.has_key('code'):
            return self.defaultoutput({'output':'code missing'})
        code = paras['code']
        data = self._exesqlone('select code,datetime,name,industry,zdf,hb,lb,csrc,volwy,vr,k,d,macd,fv,fvcnt,close,closemid,ma5,ma10,ma20,ma30,ma60,prob1,openmid1,highmid1,lowmid1,closemid1,prob2,openmid2,highmid2,lowmid2,closemid2,prob3,openmid3,highmid3,lowmid3,closemid3,prob4,openmid4,highmid4,lowmid4,closemid4,prob5,openmid5,highmid5,lowmid5,closemid5,prob6,openmid6,highmid6,lowmid6,closemid6,prob7,openmid7,highmid7,lowmid7,closemid7,prob8,openmid8,highmid8,lowmid8,closemid8 from hy.iknow_rt where active=1 and code=%s',(code,))
        if len(data)!=0 and data[0]:
            base = list(data[:17])
            ma = [(data[15],'close'),(data[17],'ma5'),(data[18],'ma10'),(data[19],'ma20'),(data[20],'ma30'),(data[21],'ma60')]
            ma.sort(reverse=True)
            prob = list(data[22:])
            return json.dumps([base,ma,prob])
        return json.dumps([])

    def q_codefv(self,paras):
        if not paras.has_key('code'):
            return self.defaultoutput({'output':'code missing'})
        code = paras['code']
        length = 'all'
        if paras.has_key('length'):
            length = paras['length']
        sql = ('select sfv from hy.iknow_attr where code=%s',(code,))
        if length!='all':
            sql = ('select sfv from hy.iknow_attr where code=%s order by date desc limit '+length,(code,))
        data = self._exesqlbatch(sql[0],sql[1])
        dist = {1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0}
        for row in data:
            dist[row[0]] = dist[row[0]] + 1
        for k in dist.keys():
            dist[k] = round(dist[k]/float(len(data)),4)
        return json.dumps(dist)

    def defaultoutput(self,paras):
        if paras.has_key('output'):
            return json.dumps(paras['output'])
        return json.dumps(['DONE'])

    def _parse(self,querystr):
        paras = {}
        items = querystr[1:].split('&')
        for it in items:
            nvs = it.split('=')
            paras[nvs[0]] = nvs[1]
        return paras

    def GET(self):
        if len(web.ctx.query)==0:
            return defaultoutput({})
        paras = self._parse(web.ctx.query)
        fun = getattr(self,paras['name'],self.defaultoutput)
        return fun(paras)
        
    def POST(self):
        pass
        
if __name__ == "__main__":
    urls = (
        '/iknow', 'ikweb'
    )
    app = web.application(urls, globals())
    app.run()
        
        
        