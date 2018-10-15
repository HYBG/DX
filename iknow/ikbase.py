#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import logging
import string
import datetime
import time
import Queue
import MySQLdb
import threading
import Queue
import ConfigParser
from logging.handlers import RotatingFileHandler

class ikmessage(object):
    def __init__(self,name,type,data,delay,active):
        self.name = name
        self.type = type
        self.data = data
        self.delay = delay
        self.active = active

class ikset:
    def __init__(self):
        self._store = {}

    def set(self,key,value):
        self._store[key] = value

    def get(self,key):
        try:
            return self._store[key]
        except Exception,e:
            pass
        return None

    def keys(self,rev=False):
        keys = self._store.keys()
        keys.sort(reverse=rev)
        return keys

    def length(self):
        return len(self._store)

class ikobj:
    def __init__(self):
        pass

class ikbase(object):
    def __init__(self,conf):
        config = ConfigParser.ConfigParser()
        config.read(conf)
        self._logfile = config.get('ikbase','log_file')
        self._dbname = config.get('ikbase','datebase','iknow')
        self._dbhost = config.get('ikbase','dbhost','localhost')
        self._dbuser = config.get('ikbase','username','root')
        self._dbpasswd = config.get('ikbase','password','123456')
        self._offdayfile = config.get('ikbase','offday_file')
        self._codesfile = config.get('ikbase','code_file')
        self._sqllogon = config.getboolean('ikbase','sql_log_on')
        self._sleepinterval = config.getint('ikbase','sleep_interval')
        if not (self._offdayfile and self._codesfile):
            raise Exception('codes file or offday file unset')
        self._logger = logging.getLogger('ikbase')
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        fmter = logging.Formatter(formatstr)
        rh = RotatingFileHandler(self._logfile, maxBytes=100*1024*1024,backupCount=50)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(logging.INFO)
        self._queue = Queue.Queue()
        self._offdays = set()
        self._codes = set()
        self._connection = None
        self._cursor = None
        self._workerflag = True
        self._mainflag = True
        self._lasttask = None
        self._loadcodes()
        self._loadoffday()

    def __del__(self):
        self._connection = None
        self._cursor = None

    def _loadcodes(self):
        f = open(self._codesfile,'r')
        lines = f.readlines()
        f.close()
        self._codes = set()
        for line in lines:
            self._codes.add(line.strip())

    def _loadoffday(self):
        f = open(self._offdayfile,'r')
        lines = f.readlines()
        f.close()
        now = datetime.datetime.now()
        td = '%04d-%02d-%02d'%(now.year,now.month,now.day)
        past = set()
        for row in lines:
            self._offdays.add(row.strip())
        for d in self._offdays:
            if d < td:
                past.add(d)
        self._offdays = self._offdays - past

    def lasttask(self):
        return self._lasttask

    def reconn(self):
        try:
            if self._cursor:
                self._cursor.close()
            if self._connection:
                self._connection.close()
            self._connection = MySQLdb.connect(host=self._dbhost,user=self._dbuser,passwd=self._dbpasswd,db=self._dbname,charset='utf8')
            self._cursor = self._connection.cursor()
            return True
        except Exception,e:
            self.info('pid[%d] ikbase connect db[%s] error[%s]'%(os.getpid(),self._dbname,e))
        return False

    def exesqlquery(self,sql,param,log=False):
        n = 0
        if log:
            self.info('pid[%d] ikbase prepare to query sql[%s],para[%s]'%(os.getpid(),sql,str(param)))
        if param:
            n = self._cursor.execute(sql,param)
        else:
            n = self._cursor.execute(sql)
        mat = []
        while n>0:
            ret = self._cursor.fetchone()
            if len(ret)==1:
                mat.append(ret[0])
            elif len(ret)>1:
                mat.append(list(ret))
            n = n-1
        if log:
            self.info('pid[%d] ikbase query results[%d]'%(os.getpid(),len(mat)))
        return mat

    def task(self,sqls,log=False):
        show = self._sqllogon
        if log:
            show = log
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if show:
                    self.info('pid[%d] ikbase execute sql[%s],para[%s] successfully'%(os.getpid(),sql[0],str(sql[1])))
            except Exception,e:
                self.error('pid[%d] ikbase execute sql[%s],para[%s] failed[%s]'%(os.getpid(),sql[0],str(sql[1]),e))
                self._connection.rollback()
                return False
        self._connection.commit()
        return True

    def loadset(self,table,code,fields):
        items = ''
        if 'date' not in fields:
            fields.append('date')
        for it in fields:
            items = items+it+','
        items = items[:-1]
        sql = 'select '+items+' from '+table+' where code=%s'
        self.debug('loadset sql[%s] code[%s]'%(sql,code))
        n = self._cursor.execute(sql,(code,))
        set = ikset()
        while n>0:
            ret = self._cursor.fetchone()
            obj = ikobj()
            for i in range(len(ret)):
                setattr(obj,fields[i],ret[i])
            set.set(getattr(obj,'date'),obj)
            n = n-1
        return set

    def loadone(self,code,date,dic):
        items = ''
        tabs  = ''
        cond  = ''
        paras = []
        attrs = []
        obj = ikobj()
        for tab in dic.keys():
            tabs = tabs+tab+','
            cond = cond+tab+'.code=%s and '+tab+'.date=%s and '
            for it in dic[tab]:
                item = '%s.%s'%(tab,it)
                attrs.append(it)
                items = items+item+','
            paras.append(code)
            paras.append(date)
        if len(tabs)!=0 and len(items)!=0 and len(cond)!=0:
            tabs = tabs[:-1]
            items = items[:-1]
            cond = cond[:-5]
            sql = 'select %s from %s where %s'%(items,tabs,cond)
            self.debug('loadone sql[%s],paras[%s]'%(sql,str(paras)))
            n = self._cursor.execute(sql,tuple(paras))
            if n==1:
                ret = self._cursor.fetchone()
                for i in range(len(ret)):
                    setattr(obj,attrs[i],ret[i])
                return obj
        return None

    def lastday(self,table,code=None,default=None):
        ld = None
        if code:
            ld = self.exesqlquery('select date from '+table+' where code=%s order by date desc limit 1',(code,))
        else:
            ld = self.exesqlquery('select date from '+table+' order by date desc limit 1',None)
        if ld and len(ld)>0:
            return ld[0]
        return default

    def lastdays(self,table,codes,default=None):
        dic = {}
        for code in codes:
            dic[code]=self.lastday(table,code,default)
        return dic

    def prob(self,item,iv,hr,lr,vr):
        self.debug('pid[%d] iktask _prob handle item[%s] val[%s] start....'%(os.getpid(),str(item),str(iv)))
        plis = []
        dn = 0.7
        up = 1.3
        vcond = 'vr<=%s'%(dn)
        if vr>=up:
            vcond = 'vr>=%s'%str(up)
        elif vr>=dn:
            vcond = 'vr>%s and vr<%s'%(str(dn),str(up))
        fcond = item+'=%s'
        all = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8))',(iv,hr,lr,hr,lr,hr,lr,hr,lr),True)
        if all[0]==0:
            return (0,(0,0,0,0,0,0,0,0))
        c1 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=1',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c1[0])/all[0]),2))
        c2 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=2',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c2[0])/all[0]),2))
        c3 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=3',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c3[0])/all[0]),2))
        c4 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=4',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c4[0])/all[0]),2))
        c5 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=5',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c5[0])/all[0]),2))
        c6 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=6',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c6[0])/all[0]),2))
        c7 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=7',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c7[0])/all[0]),2))
        c8 = self.exesqlquery('select count(*) from ik_feature where '+fcond+' and '+vcond+' and not ((highr<=%s or lowr<%s) and (nextfv=1 or nextfv=2)) and not ((lowr>=%s or highr>%s) and (nextfv=3 or nextfv=4)) and not ((highr<=%s or lowr>=%s) and (nextfv=5 or nextfv=6)) and not ((highr>%s or lowr<%s) and (nextfv=7 or nextfv=8)) and nextfv=8',(iv,hr,lr,hr,lr,hr,lr,hr,lr))
        plis.append(round(100*(float(c8[0])/all[0]),2))
        self.debug('pid[%d] iktask _prob handle item[%s] val[%s] done....'%(os.getpid(),str(item),str(iv)))
        return (all[0],tuple(plis))

    def putq(self,obj):
        self._queue.put(obj)

    def getq(self):
        return self._queue.get()

    def setloglevel(self,level):
        self._logger.setLevel(level)

    def debug(self,str):
        self._logger.debug(str)

    def info(self,str):
        self._logger.info(str)

    def error(self,str):
        self._logger.error(str)

    def loadinfo(self):
        self._loadcodes()
        self._loadoffday()

    def isopenday(self,offset=0):
        now = datetime.datetime.now()
        target = now+datetime.timedelta(days=offset)
        td = '%04d-%02d-%02d'%(target.year,target.month,target.day)
        wd = target.isoweekday()
        if wd!=6 and wd!=7 and (td not in self._offdays):
            return True
        return False

    def nextopenday(self):
        now = datetime.datetime.now()
        offset = 1
        next = None
        while 1:
            target = now+datetime.timedelta(days=offset)
            next = '%04d-%02d-%02d'%(target.year,target.month,target.day)
            wd = target.isoweekday()
            if wd!=6 and wd!=7 and (next not in self._offdays):
                break
            offset = offset + 1
        return next

    def codes(self):
        lis = list(self._codes)
        lis.sort()
        return lis

    def setworkerflag(self,flag):
        self._workerflag = flag

    def setmainflag(self,flag):
        self._mainflag = flag

    def setsleepinterval(self,interval,default=None):
        if interval:
            self._sleepinterval = interval
        else:
            self._sleepinterval = default

    def worker(self):
        self.info('pid[%d] ikbase worker thread start....'%(os.getpid()))
        self.reconn()
        while self._workerflag:
            msg = self.getq()
            self.info('pid[%d] worker get task[%s]'%(os.getpid(),msg.name))
            begin = datetime.datetime.now()
            self.handle_message(msg)
            during = datetime.datetime.now()-begin
            self.info('pid[%d] ikbase worker did task[%s] with seconds[%d]'%(os.getpid(),msg.name,during.seconds))
            self._lasttask = msg
        self.info('pid[%d] ikbase worker thread end....'%(os.getpid()))

    def beforerun(self):
        pass

    def afterrun(self):
        pass

    def handle_message(self,msg):
        pass

    def main(self):
        pass

    def run(self):
        worker = threading.Thread(target=self.worker)
        worker.start()
        self.beforerun()
        while self._mainflag:
            self.main()
            time.sleep(self._sleepinterval)
        self.afterrun()

