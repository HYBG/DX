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
from logging.handlers import RotatingFileHandler

class hydataset:
    def __init__(self):
        self._store = None

    def add(self,obj):
        if type(self._store)==type(None):
            self._store = []
            self._store.append(obj)
        elif type(self._store)==type([]):
            self._store.append(obj)

    def set(self,key,value):
        if type(self._store)==type(None):
            self._store = {}
            self._store[key] = value
        elif type(self._store)==type({}):
            self._store[key] = value
    
    def get(self,key):
        try:
            if type(self._store)==type({}) or type(self._store)==type([]):
                return self._store[key]
        except Exception,e:
            pass
        return None
        
    def keys(self,rev=False):
        if type(self._store)==type({}):
            keys = self._store.keys()
            keys.sort(reverse=rev)
            return keys
        return None

    def length(self):
        if self._store:
            return len(self._store)
        return 0

    def getsum(self,item,keys):
        all = 0.0
        for k in keys:
            all = all + getattr(self._store[k],item,0.0)
        return all

class hyobj:
    def __init__(self):
        pass

class hydata:
    def __init__(self,logger,logon=False):
        self._logger = logger
        self._connection = None
        self._cursor = None
        self._conn('hyik')
        self._logon = logon

    def _conn(self,dbname):
        try:
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('hydata connect db[%s] error[%s]'%(dbname,e))
        return False

    def _reconn(self,dbname):
        try:
            self._cursor.close()
            self._connection.close()
            self._connection = MySQLdb.connect(host='localhost',user='root',passwd='123456',db=dbname,charset='utf8') 
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self._logger.info('hydata reconnect db[%s] error[%s]'%(dbname,e))
        return False

    def exesqlone(self,sql,param,log=None):
        n = 0
        show = self._logon
        if log:
            show = log
        if show:
            self._logger.info('hydata prepare to query one sql[%s],para[%s]'%(sql,str(param)))
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n==1:
            ret = self._cursor.fetchone()
        return ret

    def exesqlbatch(self,sql,param,log=None):
        n = 0
        show = self._logon
        if log:
            show = log
        if show:
            self._logger.info('hydata prepare to query batch sql[%s],para[%s]'%(sql,str(param)))
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        ret = ()
        if n>0:
            ret = self._cursor.fetchall()
        if show:
            self._logger.info('hydata query batch results[%d]'%(len(ret)))
        return ret
        
    def task(self,sqls,log=None):
        show = self._logon
        if log:
            show = log
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if show:
                    self._logger.info('hydata execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                self._logger.error('hydata execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._connection.rollback()
                return False
        self._connection.commit()
        return True

    def loadone(self,code,date,dic):
        items = ''
        tabs  = ''
        cond  = ''
        paras = []
        attrs = []
        for tab in dic.keys():
            tabs = tabs+tab+','
            cond = cond+tab+'.code=%s and '+tab+'.date=%s and '
            for it in dic[tab]:
                item = '%s.%s'%(tab,it)
                if not hasattr(self,it):
                    attrs.append(it)
                items = items+item+','
            paras.append(code)
            paras.append(date)
        if len(tabs)!=0 and len(items)!=0 and len(cond)!=0:
            tabs = tabs[:-1]
            items = items[:-1]
            cond = cond[:-5]
            sql = 'select %s from %s where %s'%(items,tabs,cond)
            self._logger.debug('loadone sql[%s],paras[%s]'%(sql,str(paras)))
            data = self.exesqlone(sql,tuple(paras))
            if len(data)!=0 and data[0]:
                obj = hyobj()
                for i in range(len(data)):
                    setattr(obj,attrs[i],data[i])
                return obj
        return None

    def loadbycode(self,code,table,fields,orderby=None,indexed=False,desc=False,limit=None):
        items = ''
        for it in fields:
            items = items+it+','
        items = items[:-1]
        sql = 'select '+items+' from '+table+' where code=%s'
        if orderby:
            sql = sql + ' order by '+orderby
        if desc:
            sql = sql + ' desc'
        if limit:
            sql = sql + ' limit '+str(limit)
        self._logger.debug('loadbycode sql[%s]'%sql)
        data = self.exesqlbatch(sql,(code,))
        set = hydataset()
        for row in data:
            obj = hyobj()
            for i in range(len(row)):
                setattr(obj,fields[i],row[i])
            if orderby and indexed:
                set.set(getattr(obj,orderby),obj)
            else:
                set.add(obj)
        return set
        
    def loadbycodelast(self,code,date,table,fields,limit):
        items = ''
        for it in fields:
            items = items+it+','
        items = items[:-1]
        sql = 'select '+items+' from '+table+' where code=%s and date<=%s order by date desc'
        if limit:
            sql = sql + ' limit '+str(limit)
        self._logger.debug('loadbycodelast sql[%s]'%sql)
        data = self.exesqlbatch(sql,(code,date))
        set = hydataset()
        for row in data:
            obj = hyobj()
            for i in range(len(row)):
                setattr(obj,fields[i],row[i])
            set.add(obj)
        return set

    def lastday(self,table,code=None,default=None):
        ld = None
        if code:
            ld = self.exesqlone('select date from '+table+' where code=%s order by date desc limit 1',(code,))
        else:
            ld = self.exesqlone('select date from '+table+' order by date desc limit 1',None)
        if ld:
            return ld[0]
        return default

    def lastdays(self,codes,table,default=None):
        dic = {}
        for code in codes:
            dic[code]=self.lastday(table,code,default)
        return dic

    def codes(self):
        lis = []
        data = self.exesqlbatch('select distinct code from hyik.ik_tags order by code', None)
        for row in data:
            lis.append(row[0])
        return lis

    def watches(self):
        set = hydataset()
        data = self.exesqlbatch('select code,name,industry from hyik.ik_watch where active=1 order by code', None)
        for row in data:
            obj = hyobj()
            setattr(obj,'code',row[0])
            setattr(obj,'name',row[1])
            setattr(obj,'industry',row[2])
            set.add(obj)
        return set

    def getstone(self):
        pass

class hyik:
    def __init__(self):
        self._mindate = '2005-01-05'
        self._upcodes = []
        self._stone = {}
        self._logger = logging.getLogger('hyik')
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        rh = RotatingFileHandler('/var/data/iknow/log/hyik.log', maxBytes=100*1024*1024,backupCount=50)
        rh.setLevel(logging.INFO)
        fmter = logging.Formatter(formatstr)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(logging.INFO)
        self._hy = hydata(self._logger,False)

    def __del__(self):
        pass

    def _dl_season(self,month):
        sea = 4
        if month<=3:
            sea=1
        elif month<=6:
            sea=2
        elif month<=9:
            sea=3
        return sea

    def _dl_drawdigit(self,str):
        if str.isdigit():
            return int(str)
        else:
            lis = list(str)
            for i in range(len(lis)):
                if not lis[i].isdigit():
                    lis[i]=''
            return int(''.join(lis))
            
    def _dl_upfrom163(self,code,start):
        td = datetime.datetime.today()
        ey = td.year
        em = td.month
        es = self._dl_season(em)
        ymd= start.split('-')
        sy = int(ymd[0])
        ss = self._dl_season(int(ymd[1]))
        s = [sy,ss]
        e = [ey,es]
        mat = []
        while s<=e:
            url = 'http://quotes.money.163.com/trade/lsjysj_%s.html?year=%s&season=%s'%(code,s[0],s[1])
            self._logger.info('hyik ready to open url[%s]'%url)
            html=urllib2.urlopen(url).read()
            #soup = BeautifulSoup(html, 'html.parser')
            soup = BeautifulSoup(html, 'lxml')
            trs = soup.find_all('tr')
            for tr in trs:
                tds=tr.find_all('td')
                if len(tds)==11:
                    dt = tds[0].text.strip()
                    if re.match('\d{4}-\d{2}-\d{2}', dt) and dt>start:
                        open = float(tds[1].text.strip())
                        high = float(tds[2].text.strip())
                        low = float(tds[3].text.strip())
                        close = float(tds[4].text.strip())
                        vols = self._dl_drawdigit(tds[7].text.strip())
                        vole = self._dl_drawdigit(tds[8].text.strip())
                        v = (code,dt,open,high,low,close,vols,vole)
                        mat.append(v)
            self._logger.info('hyik fetch from url[%s] records[%d] start[%s]'%(url,len(mat),start))
            if s[1]!=4:
                s[1]=s[1]+1
            else:
                s[0]=s[0]+1
                s[1]=1
        return mat

    def _check(self,codes):
        sqls = []
        for code in codes:
            try:
                lds = self._hy.lastdays(codes,'ik_data','1982-09-04')
                shouldadd = self._hy.exesqlbatch('select date from hs.hs_daily_data where code=%s and date not in (select date from hy.iknow_data where code=%s)',(code,code))
                for adt in shouldadd:
                    self._logger.info('hyik _check handle dl code[%s] date[%s]....'%(code,adt[0]))
                    row = self._hy.exesqlone('select code,date,open,high,low,close,volh,volwy from hs.hs_daily_data where code=%s and date=%s',(code,adt[0]))
                    sqls.append(('insert into hyik.ik_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                    self._upcodes.append(row[0])
            except Exception,e:
                self._logger.info('code[%s],date[%04d-%02d-%02d] local update exception[%s]'%(code,now.year,now.month,now.day,e))
        self._hy.task(sqls)
        self._logger.info('hyik _check handle dl check executed sqls[%d]....'%(len(sqls)))

    def dl(self):
        self._upcodes = []
        try:
            self._logger.info('hyik dl task start....')
            now = datetime.datetime.now()
            clis = self._hy.codes()
            sqls = []
            defaultstart = '2016-01-01'
            lds = self._hy.lastdays(clis,'ik_data',defaultstart)
            for code in clis:
                try:
                    start = lds[code]
                    mat = self._dl_upfrom163(code,start)
                    for row in mat:
                        sqls.append(('insert into hyik.ik_data(code,date,open,high,low,close,volh,volwy) values(%s,%s,%s,%s,%s,%s,%s,%s)',(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7])))
                        self._upcodes.append(row[0])
                except Exception,e:
                    self._logger.info('code[%s],date[%04d-%02d-%02d] update failed[%s]'%(code,now.year,now.month,now.day,e))
            self._hy.task(sqls)
            self._logger.info('hyik handle dl executed sqls[%d]....'%(len(sqls)))
            self._check(clis)
        except Exception,e:
            self._logger.info('hyik dl exception[%s]....'%e)
        self._logger.info('hyik dl task done....')

    def _kinfo(self,code,data,ld):
        self._logger.debug('hyik _kinfo start code[%s] length[%d]'%(code,data.length()))
        dic = {}
        dl = data.keys(True)
        for i in range(len(dl)-1):
            if dl[i]<=ld:
                break
            day = datetime.datetime.strptime(dl[i],'%Y-%m-%d')
            weekday = day.isoweekday()
            obj = data.get(dl[i])
            objp = data.get(dl[i+1])
            hb = 0
            if obj.high>objp.high:
                hb = 1
            lb = 0
            if obj.low<objp.low:
                lb = 1
            k = 0
            if obj.close>obj.open:
                k = 1
            csrc = 0.5
            if obj.high!=obj.low:
                csrc = round((obj.close-obj.low)/(obj.high-obj.low),4)
            zdf = round((obj.close-objp.close)/objp.close,4)
            dic[dl[i]] = (weekday,hb,lb,k,csrc,zdf)
        self._logger.debug('hyik _kinfo done code[%s] length[%d]'%(code,len(dic)))
        return dic
        
    def _fvs(self,code,data,ld):
        self._logger.debug('hyik _fvs start code[%s] length[%d]'%(code,data.length()))
        dic = {}
        dl = data.keys(True)
        for i in range(len(dl)-4):
            if dl[i]<=ld:
                break
            fvs = []
            for j in range(4):
                hb = 0
                if data.get(dl[i+j]).high>data.get(dl[i+j+1]).high:
                    hb = 1
                lb = 0
                if data.get(dl[i+j]).low<data.get(dl[i+j+1]).low:
                    lb = 1
                kline = 0
                if data.get(dl[i+j]).close>data.get(dl[i+j]).open:
                    kline = 1
                fvs.append(self._fv(hb,lb,kline))
            fv1 = fvs[0]
            fv2 = int('%d%d'%(fvs[1],fvs[0]))
            fv3 = int('%d%d%d'%(fvs[2],fvs[1],fvs[0]))
            fv4 = int('%d%d%d%d'%(fvs[3],fvs[2],fvs[1],fvs[0]))
            dic[dl[i]] = (fv1,fv2,fv3,fv4)
        self._logger.debug('hyik _fvs done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _kd(self,code,data,ld):
        self._logger.debug('hyik _kd start code[%s] length[%d]'%(code,data.length()))
        kdp = 9
        lastk = 50.0
        lastd = 50.0
        dic = {}
        dl = data.keys()
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
                k = (2.0*lastk+rsv)/3.0
                d = (2.0*lastd+k)/3.0
            lastk = k
            lastd = d
            k = round(k,2)
            d = round(d,2)
            if dl[i]>ld:
                dic[dl[i]]=(k,d)
        self._logger.debug('hyik _kd done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _boll(self,code,data,ld):
        self._logger.debug('hyik _boll start code[%s] length[%d]'%(code,data.length()))
        bollp = 20
        dic = {}
        dl = data.keys()
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
        self._logger.debug('hyik _boll done code[%s] length[%d]'%(code,len(dic)))
        return dic
        
    def _macd(self,code,data,ld):
        self._logger.debug('hyik _macd start code[%s] length[%d]'%(code,data.length()))
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        dic = {}
        dl = data.keys()
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
        self._logger.debug('hyik _macd done code[%s] length[%d]'%(code,len(dic)))
        return dic

    def _ma(self,code,data,ld):
        self._logger.debug('hyik _ma start code[%s] length[%d]'%(code,data.length()))
        dic = {}
        dl = data.keys()
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

    def _vol(self,code,data,ld):
        self._logger.debug('hyiknow _vol start code[%s] length[%d]'%(code,data.length()))
        dic = {}
        dl = data.keys()
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

    def _blanks(self,code,base,fill,default):
        blanks = []
        ld = self._hy.exesqlone('select date from hyik.'+fill+' where code=%s order by date desc limit 1',(code,))
        start = default
        if len(ld)!=0 and ld[0]:
            default = ld[0]
        dates = self._hy.exesqlbatch('select date from hyik.'+base+' where code=%s and date>%s and date not in (select date from hyik.'+fill+' where code=%s)',(code,start,code))
        for dt in dates:
            blanks.append(dt[0])
        if len(blanks)>0:
            self._logger.info('hyik deal with [%s] from [%s] to [%s]'%(code,blanks[0],blanks[-1]))
        else:
            self._logger.info('hyik deal with [%s] nothing'%code)
        return blanks

    def attr(self,all=False):
        self._logger.info('hyik attr task start....')
        codes = self._upcodes
        if all:
            codes = self._hy.codes()
        total = float(len(codes))
        handled = 0
        lds = self._hy.lastdays(codes,'ik_attr','1982-09-04')
        for code in codes:
            handled = handled+1
            blanks = self._blanks(code,'ik_data','ik_attr',lds[code])
            if len(blanks)>0:
                sqls = []
                data = self._hy.loadbycode(code,'ik_data',['code','date','open','high','low','close','volwy'],'date',True,False)
                ld = lds[code]
                kinfo = self._kinfo(code,data,ld)
                kd = self._kd(code,data,ld)
                boll = self._boll(code,data,ld)
                macd = self._macd(code,data,ld)
                ma = self._ma(code,data,ld)
                vol = self._vol(code,data,ld)
                for dt in blanks:
                    if kinfo.has_key(dt) and kd.has_key(dt) and boll.has_key(dt) and macd.has_key(dt) and ma.has_key(dt) and vol.has_key(dt):
                        sqls.append(('insert into hyik.ik_attr(code,date,weekday,hb,lb,kline,csrc,zdf,k,d,mid,std,emaf,emas,diff,dea,macd,ma5,ma10,ma30,ma60,vol3,vol5,vol10,vol20) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,dt,)+kinfo[dt]+kd[dt]+boll[dt]+macd[dt]+ma[dt]+vol[dt]))
                self._hy.task(sqls)
                self._logger.info('hyik attr handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyik attr task done....')

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
        
    def _kdv(self,kb,kdb):
        kdv = 0
        if kb==1 and kdb==1:
            kdv = 1
        elif kb==0 and kdb==1:
            kdv = 2
        elif kb==1 and kdb==0:
            kdv = 3
        elif kb==0 and kdb==0:
            kdv = 4
        return kdv

    def _mdv(self,mb,mdb):
        mdv = 0
        if mb==1 and mdb==1:
            mdv = 1
        elif mb==0 and mdb==1:
            mdv = 2
        elif mb==1 and mdb==0:
            mdv = 3
        elif mb==0 and mdb==0:
            mdv = 4
        return mdv

    def derivative(self,all=False):
        self._logger.info('hyik derivative task start....')
        codes = self._upcodes
        if all:
            codes = self._hy.codes()
        total = float(len(codes))
        handled = 0
        lds = self._hy.lastdays(codes,'ik_deri','1982-09-04')
        for code in codes:
            handled = handled+1
            blanks = self._blanks(code,'ik_attr','ik_deri',lds[code])
            sqls = []
            for dt in blanks:
                data = self._hy.exesqlbatch('select open,high,low,close from hyik.ik_data where code=%s and date<=%s order by date desc limit 2',(code,dt))
                if len(data)==2:
                    hb = 0
                    if data[0][1]>data[1][1]:
                        hb = 1
                    lb = 0
                    if data[0][2]<data[1][2]:
                        lb = 1
                    kline = 0
                    if data[0][3]>data[0][0]:
                        kline = 1
                    fv = self._fv(hb,lb,kline)
                    attr = self._hy.exesqlbatch('select k,d,macd from hyik.ik_attr where code=%s and date<=%s order by date desc limit 2',(code,dt))
                    if len(attr)==2:
                        kb = 0
                        if attr[0][0]>attr[0][1]:
                           kb = 1
                        kdb = 0
                        if abs(attr[0][0]-attr[1][0])>abs(attr[0][1]-attr[1][1]):
                            kdb = 1
                        kdv = self._kdv(kb,kdb)
                        mb = 0
                        if attr[0][2]>0:
                            mb = 1
                        mdb = 0
                        if attr[0][2]-attr[1][2]>0:
                            mdb = 1
                        mdv = self._mdv(mb,mdb)
                        sqls.append(('insert into hyik.ik_deri(code,date,fv,kdv,macdv) values(%s,%s,%s,%s,%s)',(code,dt,fv,kdv,mdv)))
            self._hy.task(sqls)
            self._logger.info('hyik derivative handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyik derivative task done....')
        
    def feature(self,all=False):
        self._logger.info('hyik feature task start....')
        codes = self._upcodes
        if all:
            codes = self._hy.codes()
        total = float(len(codes))
        handled = 0
        for code in codes:
            sqls = []
            handled = handled+1
            data = self._hy.loadbycode(code,'ik_deri',['date','fv','kdv','macdv'],'date',False,True)
            if data.length()<200:
                continue
            if data.get(199).date<'2005-01-01':
                continue
            start = self._hy.lastday('ik_feature',code,'2005-01-01')
            mat = []
            for i in range(data.length()-5):
                date = data.get(i+1).date
                if date<=start:
                    break
                nextdate = data.get(i).date
                nextfv = data.get(i).fv
                fv4 = '%d%d%d%d'%(data.get(i+4).fv,data.get(i+3).fv,data.get(i+2).fv,data.get(i+1).fv)
                kdv3 = '%d%d%d'%(data.get(i+3).kdv,data.get(i+2).kdv,data.get(i+1).kdv)
                macdv3 = '%d%d%d'%(data.get(i+3).macdv,data.get(i+2).macdv,data.get(i+1).macdv)
                ohlc = self._hy.loadbycodelast(code,data.get(i).date,'ik_data',['open','high','low','close'],2)
                if ohlc.length()==2:
                    openr = round((ohlc.get(0).open-ohlc.get(1).close)/ohlc.get(1).close,4)
                    highr = round((ohlc.get(0).high-ohlc.get(1).close)/ohlc.get(1).close,4)
                    lowr = round((ohlc.get(0).low-ohlc.get(1).close)/ohlc.get(1).close,4)
                    closer = round((ohlc.get(0).close-ohlc.get(1).close)/ohlc.get(1).close,4)
                    vol = self._hy.loadone(code,date,{'ik_data':['volwy'],'ik_attr':['vol5']})
                    if vol:
                        vr = round((vol.volwy/(vol.vol5/5.0)),2)
                        nfv4 = '%d%d%d%d'%(data.get(i+3).fv,data.get(i+2).fv,data.get(i+1).fv,data.get(i).fv)
                        nkdv3 = '%d%d%d'%(data.get(i+2).kdv,data.get(i+1).kdv,data.get(i).kdv)
                        nmacdv3 = '%d%d%d'%(data.get(i+2).macdv,data.get(i+1).macdv,data.get(i).macdv)
                        sqls.append(('insert into hyik.ik_feature(code,date,vr,fv4,kdv3,macdv3,nextdate,nextfv,openr,highr,lowr,closer,nextfv4,nextkdv3,nextmacdv3) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,date,vr,fv4,kdv3,macdv3,nextdate,nextfv,openr,highr,lowr,closer,nfv4,nkdv3,nmacdv3)))
            self._hy.task(sqls)
            self._logger.info('hyik feature handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyik feature task done....')

    def stone(self):
        self._logger.info('hyik stone task start....')
        watches = self._hy.watches()
        total = float(watches.length())
        handled = 0
        sqls = [('update hyik.ik_stone set active=active+1',None)]
        for i in range(watches.length()):
            code = watches.get(i).code
            handled = handled+1
            data = self._hy.loadbycode(code,'ik_data',['date','open','high','low','close','volwy'],'date',True,True,59)
            dl = data.keys()
            self._logger.info('hyik stone task date[%s-%s]....'%(dl[0],dl[-1]))
            close = data.get(dl[0]).close
            high = data.get(dl[0]).high
            low = data.get(dl[0]).low
            for j in range(1,8):
                if data.get(dl[j]).high>high:
                    high = data.get(dl[j]).high
                if data.get(dl[j]).low<low:
                    low = data.get(dl[j]).low
            vol4 = data.get(dl[0]).volwy+data.get(dl[1]).volwy+data.get(dl[2]).volwy+data.get(dl[3]).volwy
            s4 = data.getsum('close',dl[:4])
            s9 = data.getsum('close',dl[:9])
            s19 = data.getsum('close',dl[:19])
            s29 = data.getsum('close',dl[:29])
            s59 = data.getsum('close',dl[:59])
            sqls.append(('insert into hyik.ik_stone(code,date,high8,low8,vol4,s4,s9,s19,s29,s59) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,dl[0],high,low,vol4,s4,s9,s19,s29,s59)))
            self._logger.info('hyik stone handle progress[%0.2f%%] code[%s]....'%(100*(handled/total),code))
        self._hy.task(sqls)
        self._logger.info('hyik stone task done sqls[%d]....'%len(sqls))

    def daily(self):
        self._logger.info('hyik daily task start....')
        ld = self._hy.lastday('ik_daily')
        start = '2005-01-01'
        sqls = []
        if ld:
            start = ld
        dts = self._hy.exesqlbatch('select distinct date from hyik.ik_attr where date>%s order by date',(start,),True)
        for dt in dts:
            self._logger.info('hyik daily task deal with date[%s]'%dt[0])
            all = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and code in (select code from hyik.ik_watch)',(dt[0],))
            c1 = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and fv=1 and code in (select code from hyik.ik_watch)',(dt[0],))
            c2 = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and fv=2 and code in (select code from hyik.ik_watch)',(dt[0],))
            c3 = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and fv=3 and code in (select code from hyik.ik_watch)',(dt[0],))
            c4 = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and fv=4 and code in (select code from hyik.ik_watch)',(dt[0],))
            c5 = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and fv=5 and code in (select code from hyik.ik_watch)',(dt[0],))
            c6 = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and fv=6 and code in (select code from hyik.ik_watch)',(dt[0],))
            c7 = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and fv=7 and code in (select code from hyik.ik_watch)',(dt[0],))
            c8 = self._hy.exesqlone('select count(*) from hyik.ik_deri where date=%s and fv=8 and code in (select code from hyik.ik_watch)',(dt[0],))
            if len(all)!=0 and all[0]:
                k1r = round(100*(float(c1[0])/float(all[0])),2)
                k2r = round(100*(float(c2[0])/float(all[0])),2)
                k3r = round(100*(float(c3[0])/float(all[0])),2)
                k4r = round(100*(float(c4[0])/float(all[0])),2)
                k5r = round(100*(float(c5[0])/float(all[0])),2)
                k6r = round(100*(float(c6[0])/float(all[0])),2)
                k7r = round(100*(float(c7[0])/float(all[0])),2)
                k8r = round(100*(float(c8[0])/float(all[0])),2)
                sqls.append(('insert into hyik.ik_daily(date,k1r,k2r,k3r,k4r,k5r,k6r,k7r,k8r) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(dt[0],k1r,k2r,k3r,k4r,k5r,k6r,k7r,k8r)))
        self._hy.task(sqls)
        self._logger.info('hyik daily task done sqls[%d]....'%len(sqls))

    def future(self,nextn):
        self._logger.info('hyik future task start....')
        codes = self._hy.codes()
        total = float(len(codes))
        handled = 0
        for code in codes:
            ld = self._hy.exesqlone('select date from hyik.ik_future where code=%s and nextn=%s order by date desc limit 1',(code,nextn))
            handled = handled+1
            start = '2005-01-01'
            if len(ld)!=0 and ld[0]:
                start = ld[0]
            data = self._hy.loadbycode(code,'ik_data',['date','open','high','low','close'],'date',False,False)
            sqls = []
            for i in range(data.length()-nextn):
                if data.get(i).date<=start:
                    continue
                close = data.get(i).close
                high = 0.0
                low = 1000000.0
                for j in range(1,nextn+1):
                    if data.get(i+j).high>high:
                        high = data.get(i+j).high
                    if data.get(i+j).low<low:
                        low = data.get(i+j).low
                end= data.get(i+nextn).close
                highr = round(100*((high-close)/close),2)
                lowr = round(100*((low-close)/close),2)
                csrc = round(100*((end-low)/(high-low)),2)
                sqls.append(('insert into hyik.ik_future(code,date,nextn,highr,lowr,csrc) values(%s,%s,%s,%s,%s,%s)',(code,data.get(i).date,nextn,highr,lowr,csrc)))
            self._hy.task(sqls)
            self._logger.info('hyik future handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyik future task done....')

    def _simdays(self,date,dv,cnt):
        set = self._hy.exesqlbatch('select date,k1r,k2r,k3r,k4r,k5r,k6r,k7r,k8r from hyik.ik_daily where date<%s order by date desc',(date,))
        mat = []
        for row in set:
            d = abs(row[1]-dv[0])+abs(row[2]-dv[1])+abs(row[3]-dv[2])+abs(row[4]-dv[3])+abs(row[5]-dv[4])+abs(row[6]-dv[5])+abs(row[7]-dv[6])+abs(row[8]-dv[7])
            mat.append((d,row[0]))
        mat.sort()
        mat = mat[:cnt]
        lis = []
        for row in mat:
            lis.append(row[1])
        return lis

    def _prob(self,item,val,hr,lr,vr,dlis):
        self._logger.info('hyik _prob handle item[%s] val[%s] start....'%(str(item),str(val)))
        plis = []
        dcond = '('
        for d in dlis:
            dcond = dcond+d+','
        dcond = dcond[:-1]+')'
        vcond = 'vr<=0.6'
        if vr>=1.4:
            vcond = 'vr>=1.4'
        elif vr>=0.6:
            vcond = 'vr>0.6 and vr<1.4'
        fcond = item+'=%s'
        all = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        if all[0]==0:
            return (0,(0,0,0,0,0,0,0,0))
        c1 = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=1 and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c1[0])/all[0]),2))
        c2 = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=2 and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c2[0])/all[0]),2))
        c3 = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=3 and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c3[0])/all[0]),2))
        c4 = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=4 and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c4[0])/all[0]),2))
        c5 = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=5 and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c5[0])/all[0]),2))
        c6 = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=6 and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c6[0])/all[0]),2))
        c7 = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=7 and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c7[0])/all[0]),2))
        c8 = self._hy.exesqlone('select count(*) from hyik.ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=8 and date in '+dcond,(val,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c8[0])/all[0]),2))
        self._logger.info('hyik _prob handle item[%s] val[%s] done....'%(str(item),str(val)))
        return (all[0],tuple(plis))

    def prob(self,start=None):
        self._logger.info('hyik prob task start....')
        codes = self._upcodes
        if all:
            codes = self._hy.codes()
        total = float(len(codes))
        handled = 0
        if not start:
            start = '2018-09-01'
        for code in codes:
            handled = handled+1
            ld = self._hy.exesqlone('select date from hyik.ik_prob where code=%s order by date desc limit 1',(code,))
            if len(ld)!=0 and ld[0]:
                start = ld[0]
            fvs = self._hy.exesqlbatch('select fv1,fv2,fv3,fv4,date from hyik.ik_attr where code=%s and date>%s and date not in (select date from hyik.ik_prob where date>%s) order by date',(code,start,start))
            sqls = []
            for fv in fvs:
                fv1 = fv[0]
                fv2 = fv[1]
                fv3 = fv[2]
                fv4 = fv[3]
                dt = fv[4]
                obj = self._hy.loadone(code,dt,{'ik_data':['high','low','close','volwy'],'ik_attr':['vol5']})
                if obj:
                    self._logger.info('hyik prob handle code[%s] date[%s]....'%(code,dt))
                    hr = (obj.high-obj.close)/obj.close
                    lr = (obj.low-obj.close)/obj.close
                    vr = obj.volwy/(obj.vol5/5.0)
                    dv = self._hy.exesqlone('select k1r,k2r,k3r,k4r,k5r,k6r,k7r,k8r from hyik.ik_daily where date=%s',(dt,))
                    dlis = self._simdays(dt,dv,300)
                    self._logger.info('hyik prob handle code[%s] date[%s] simdays....'%(code,dt))
                    fv1plis = self._prob('fv1',fv1,hr,lr,vr,dlis)
                    fv2plis = self._prob('fv2',fv2,hr,lr,vr,dlis)
                    fv3plis = self._prob('fv3',fv3,hr,lr,vr,dlis)
                    fv4plis = self._prob('fv4',fv4,hr,lr,vr,dlis)
                    sqls.append(('insert into hyik.ik_prob(code,date,fv1cnt,fv1p1,fv1p2,fv1p3,fv1p4,fv1p5,fv1p6,fv1p7,fv1p8,fv2cnt,fv2p1,fv2p2,fv2p3,fv2p4,fv2p5,fv2p6,fv2p7,fv2p8,fv3cnt,fv3p1,fv3p2,fv3p3,fv3p4,fv3p5,fv3p6,fv3p7,fv3p8,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(code,dt)+(fv1plis[0],)+fv1plis[1]+(fv2plis[0],)+fv2plis[1]+(fv3plis[0],)+fv3plis[1]+(fv4plis[0],)+fv4plis[1]))
            self._hy.task(sqls)
            self._logger.info('hyik prob handle progress[%0.2f%%] code[%s] sqls[%d]....'%(100*(handled/total),code,len(sqls)))
        self._logger.info('hyik prob task done....')

    def rttask(self):
        self._logger.info('hyik rttask start....')
        hqlis = self._rtprice()
        sqls = [('update hyik.ik_rt set active=active+1',None)]
        self._logger.info('hyik rttask get hq list[%d]....'%len(hqlis))
        hbc = 0
        lbc = 0
        csrc = 0
        kdic = {1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0}
        for hq in hqlis:
            hb = 0
            if hq.high>self._stone[hq.code].lasthigh:
                hbc = hbc + 1
                hb = 1
            lb = 0
            if hq.low<self._stone[hq.code].lastlow:
                lbc = lbc + 1
                lb = 1
            kline = 0
            if hq.close>hq.open:
                kline = 1
            fv = self._fv(hb.lb,kline)
            kdic[fv] = kdic[fv]+1
            if hq.high==hq.low:
                csrc = csrc + 50.0
            else:
                csrc = csrc + round(100*((hq.close-hq.low)/(hq.high-hq.low)),2)
        all = float(len(hqlis))
        hbr = round(100*(hbc/all),2)
        lbr = round(100*(lbc/all),2)
        csrc = round(csrc/all,2)
        for k in kdic.keys():
            kdic[k]=round(100*(kdic[k]/all),2)
        dv = (kdic[1],kdic[2],kdic[3],kdic[4],kdic[5],kdic[6],kdic[7],kdic[8])
        for hq in hqlis:
            sqls.append(self._rtbuild(hq,dv))
        if len(sqls)>1:
            self._hy.task(sqls)
        self._logger.info('hyik rttask end successfully sqls[%d]....'%(len(sqls)-1))

    def daily_task(self,name):
        self._logger.info('daily_task[%s] start....'%(name))
        self.dl()
        self.attr()
        self.derivative()
        self.feature()
        self.stone()
        self._logger.info('daily_task[%s] end successfully....'%(name))

    def _taskname(self):
        dt = datetime.datetime.now()
        if dt.hour < 17:
            dt = dt + datetime.timedelta(days=-1)
        while dt.isoweekday()>5:
            dt = dt + datetime.timedelta(days=-1)
        return '%04d-%02d-%02d'%(dt.year,dt.month,dt.day)

    def _isopenday(self):
        now = datetime.datetime.now()
        wd = now.isoweekday()
        o1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
        c2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0)
        if wd == 6 or wd == 7:
            return False
        if now < o1 or now > c2:
            return False
        url = 'http://hq.sinajs.cn/list=sz399001'
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            if info[30] == '%04d-%02d-%02d'%(now.year,now.month,now.day):
                return True
        except Exception, e:
            self._logger.warn('get current url[%s] exception[%s]'%(url,e))
            return None

    def _righttime(self,now):
        tt = (now.hour,now.minute)
        all = [(9,31),(9,41),(9,51),(10,1),(10,11),(10,21),(10,31),(10,41),(10,51),(11,1),(11,11),(11,21),(13,10),(13,20),(13,30),(13,40),(13,50),(14,0),(14,10),(14,20),(14,30),(14,40),(14,50),(15,0)]
        if tt in all:
            return True 
        return False

    def _rtprice(self):
        codeliststr = ''
        codes = self._stone.keys()
        codes.sort()
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
                        hq = hyobj()
                        setattr(obj,'code',codes[i])
                        setattr(obj,'open',float(info[1]))
                        setattr(obj,'high',float(info[4]))
                        setattr(obj,'low',float(info[5]))
                        setattr(obj,'close',float(info[3]))
                        setattr(obj,'lastclose',float(info[2]))
                        setattr(obj,'volwy',float(info[9])/10000.0)
                        setattr(obj,'vilh',float(info[8])/100)
                        setattr(obj,'date',info[30])
                        setattr(obj,'time',info[31])
                        lis.append(hq)
                except Exception, e:
                    self._logger.error('get current price codes[%s] exception[%s]'%(codes[i],e))
                i = i+1
            return lis
        except Exception, e:
            self._logger.error('get current price codes[%d] url[%s] exception[%s]'%(len(codes),url,e))
            return None

    def _dayload(self):
        data = self._hy.exesqlbatch('select code,date,high8,low8,vol4,s4,s9,s19,s29,s59 from hyik.ik_stone where active=1 order by code', None)
        for row in data:
            names = self._hy.exesqlone('select name,tag from hyik.ik_tags where code=%s and tagtype=%s',(row[0],'industry'))
            hl = self._hy.exesqlone('select high,low from hyik.ik_data where code=%s and date=%s',(row[0],row[1]))
            attrs = self._hy.exesqlone('select fv1,fv2,fv3,fv4,k,d,emaf,emas,dea from hyik.ik_attr where code=%s and date=%s',(row[0],row[1]))
            if len(names)!=0 and names[0] and len(hl)!=0 and hl[0] and len(attrs)!=0 and attrs[0] and len(ffvs)!=0 and ffvs[0]:
                obj = hyobj()
                setattr(obj,'code',row[0])
                setattr(obj,'date',row[1])
                setattr(obj,'high8',row[2])
                setattr(obj,'low8',row[3])
                setattr(obj,'vol4',row[4])
                setattr(obj,'s4',row[5])
                setattr(obj,'s9',row[6])
                setattr(obj,'s19',row[7])
                setattr(obj,'s29',row[8])
                setattr(obj,'s59',row[9])
                setattr(obj,'name',names[0])
                setattr(obj,'industry',names[1])
                setattr(obj,'lasthigh',hl[0])
                setattr(obj,'lastlow',hl[1])
                setattr(obj,'fv1',attrs[0])
                setattr(obj,'fv2',attrs[1])
                setattr(obj,'fv3',attrs[2])
                setattr(obj,'fv4',attrs[3])
                setattr(obj,'k',attrs[4])
                setattr(obj,'d',attrs[5])
                setattr(obj,'emaf',attrs[6])
                setattr(obj,'emas',attrs[7])
                setattr(obj,'dea',attrs[8])
                self._stone[row[0]] = obj

    def _multiple(self):
        dt = datetime.datetime.strptime(self.time,'%H:%M:%S')
        if dt.hour==9 and dt.minute<40:
            return 24.0/1.0
        elif dt.hour==9 and dt.minute<50:
            return 24.0/2.0
        elif dt.hour==9 and dt.minute<59:
            return 24.0/3.0
        elif dt.hour==10 and dt.minute<10:
            return 24.0/4.0
        elif dt.hour==10 and dt.minute<20:
            return 24.0/5.0
        elif dt.hour==10 and dt.minute<30:
            return 24.0/6.0
        elif dt.hour==10 and dt.minute<40:
            return 24.0/7.0
        elif dt.hour==10 and dt.minute<50:
            return 24.0/8.0
        elif dt.hour==10 and dt.minute<59:
            return 24.0/9.0
        elif dt.hour==11 and dt.minute<10:
            return 24.0/10.0
        elif dt.hour==11 and dt.minute<20:
            return 24.0/11.0
        elif dt.hour==11 and dt.minute<30:
            return 24.0/12.0
        elif dt.hour==13 and dt.minute<10:
            return 24.0/13.0
        elif dt.hour==13 and dt.minute<20:
            return 24.0/14.0
        elif dt.hour==13 and dt.minute<30:
            return 24.0/15.0
        elif dt.hour==13 and dt.minute<40:
            return 24.0/16.0
        elif dt.hour==13 and dt.minute<50:
            return 24.0/17.0
        elif dt.hour==13 and dt.minute<59:
            return 24.0/18.0
        elif dt.hour==14 and dt.minute<10:
            return 24.0/19.0
        elif dt.hour==14 and dt.minute<20:
            return 24.0/20.0
        elif dt.hour==14 and dt.minute<30:
            return 24.0/21.0
        elif dt.hour==14 and dt.minute<40:
            return 24.0/22.0
        elif dt.hour==14 and dt.minute<50:
            return 24.0/23.0
        elif dt.hour==14 and dt.minute<59:
            return 24.0/24.0
        return 1.0

    def _rtbuild(self,hq,dv):
        stone = self._stone[hq.code]
        zdf = round(100*((hq.close-hq.lastclose)/hq.lastclose),2)
        csrc = 50.0
        if hq.high!=hq.low:
            csrc = round(100*((hq.close-hq.low)/(hq.high-hq.low)),2)
        high = stone.high8
        if hq.high>high:
            high = hq.high
        low = stone.low8
        if hq.low<low:
            low = hq.low
        k = 50.0
        d = 50.0
        if high != low:
            rsv = 100*((hq.close-low)/(high-low))
            k = (2.0*stone.lastk+rsv)/3.0
            d = (2.0*stone.lastd+k)/3.0
        macdparan1 = 12
        macdparan2 = 26
        macdparan3 = 9
        emaf = 2*hq.close/(macdparan1+1)+(macdparan1-1)*stone.emaf/(macdparan1+1)
        emas = 2*hq.close/(macdparan2+1)+(macdparan2-1)*stone.emas/(macdparan2+1)
        diff = round(emaf-emas,4)
        dea  = round(2*diff/(macdparan3+1)+(macdparan3-1)*stone.dea/(macdparan3+1),4)
        macd = round(2*(diff-dea),4)
        ma5 = round((stone.s4+hq.close)/5.0,2)
        ma10 = round((stone.s9+hq.close)/10.0,2)
        ma20 = round((stone.s19+hq.close)/20.0,2)
        ma30 = round((stone.s29+hq.close)/30.0,2)
        ma60 = round((stone.s59+hq.close)/60.0,2)
        vol = hq.volwy*self._multiple()
        vr = round(vol/((stone.vol4+vol)/5.0),2)
        hr = round((hq.high-hq.close)/hq.close,4)
        lr = round((hq.low-hq.close)/hq.close,4)
        hb = 0
        if hq.high>stone.lasthigh:
            hb = 1
        lb = 0
        if hq.low<stone.lastlow:
            lb = 1
        kline = 0
        if hq.close>hq.open:
            kline = 1
        fv1 = self._fv(hb,lb,kline)
        fv2 = int('%d%d'%(stone.ffv1,fv1))
        fv3 = int('%d%d'%(stone.ffv2,fv1))
        fv4 = int('%d%d'%(stone.ffv3,fv1))
        dlis = self._simdays(hq.date,dv,300)
        fv1p = self._prob('fv1',fv1,hr,lr,vr,dlis)
        fv2p = self._prob('fv2',fv2,hr,lr,vr,dlis)
        fv3p = self._prob('fv3',fv3,hr,lr,vr,dlis)
        fv4p = self._prob('fv4',fv4,hr,lr,vr,dlis)
        datetime = '%s %s'%(hq.date,hq.time)
        return ('insert into hyik.ik_rt(code,datetime,name,industry,zdf,hb,lb,csrc,volwy,vr,k,d,macd,close,ma5,ma10,ma20,ma30,ma60,fv1,fv1cnt,fv1p1,fv1p2,fv1p3,fv1p4,fv1p5,fv1p6,fv1p7,fv1p8,fv2,fv2cnt,fv2p1,fv2p2,fv2p3,fv2p4,fv2p5,fv2p6,fv2p7,fv2p8,fv3,fv3cnt,fv3p1,fv3p2,fv3p3,fv3p4,fv3p5,fv3p6,fv3p7,fv3p8,fv4,fv4cnt,fv4p1,fv4p2,fv4p3,fv4p4,fv4p5,fv4p6,fv4p7,fv4p8) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(hq.code,datetime,stone.name,stone.industry,zdf,hb,lb,csrc,hq.volwy,vr,k,d,macd,hq.close,ma5,ma10,ma20,ma30,ma60,fv1,fv1p[0])+fv1p[1]+(fv2p[0],)+fv2p[1]+(fv3p[0],)+fv3p[1]+(fv4p[0],)+fv4p[1])

    def run(self):
        pretask = ''
        open = False
        if self._isopenday():
            open = True
            self._dayload()
        while 1:
            now = datetime.datetime.now()
            if open:
                if self._righttime(now):
                    self.rttask()
            else:
                otime = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
                ctime = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=10,second=0)
                if now >= otime and now < ctime and self._isopenday():
                    open = True
                    self._logger.info('hyik market is open....')
                    self._dayload()
                    continue
                if now>=ctime:
                    open = False
                    self._logger.info('hyik market is closed....')
                taskname = self._taskname()
                if taskname != pretask:
                    self.daily_task(taskname)
                    pretask = taskname
            time.sleep(5)

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-d', '--download', action='store_true', dest='download',default=False, help='run download')
    parser.add_option('-u', '--future', action='store_true', dest='future',default=False, help='run future')
    parser.add_option('-n', '--nextn', action='store', dest='nextn',type='int',default=7, help='nextn when run future')
    parser.add_option('-a', '--attr', action='store_true', dest='attr',default=False, help='run attr')
    parser.add_option('-e', '--deri', action='store_true', dest='deri',default=False, help='run derivative')
    parser.add_option('-D', '--daily', action='store_true', dest='daily',default=False, help='run daily')
    parser.add_option('-f', '--feature', action='store_true', dest='feature',default=False, help='run feature')
    parser.add_option('-s', '--stone', action='store_true', dest='stone',default=False, help='run stone')
    parser.add_option('-p', '--prob', action='store_true', dest='prob',default=False, help='run prob')
    parser.add_option('-r', '--run', action='store_true', dest='run',default=False, help='run loop')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    ik = hyik()
    if ops.download:
        ik.dl()
    if ops.future:
        ik.future(ops.nextn)
    if ops.attr:
        ik.attr(True)
    if ops.deri:
        ik.derivative(True)
    if ops.daily:
        ik.daily()
    if ops.feature:
        ik.feature(True)
    if ops.stone:
        ik.stone()
    if ops.prob:
        ik.prob()
    if ops.run:
        ik.run()
    
    
    