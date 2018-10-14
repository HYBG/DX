#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import Queue
import MySQLdb
import urllib2
import threading
import Queue
import json
import multiprocessing
import ConfigParser
from socket import *
from bs4 import BeautifulSoup
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

g_home = os.getenv('IKNOW_HOME',None)
if not g_home:
    raise Exception('IKNOW_HOME not set')

HY_TASK_REALTIME = 'HY_TASK_REALTIME'
HY_TASK_AFTERCLOSE = 'HY_TASK_AFTERCLOSE'
HY_TASK_BEFOREOPEN = 'HY_TASK_BEFOREOPEN'
HY_TASK_UPDATEINFO = 'HY_TASK_UPDATEINFO'


class ikbase(object):
    def __init__(self,conf):
        
        self._logger = logging.getLogger('ikbase')
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        fmter = logging.Formatter(formatstr)
        rh = None
        if logfile:
            rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
        else:
            rh = RotatingFileHandler(os.path.join(os.path.join(g_home,'log'),'ikbase.log'), maxBytes=100*1024*1024,backupCount=50)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(logging.INFO)
        self._queue = Queue.Queue()
        self._offdays = set()
        self._codes = set()

    def _updatecodes(self):
        fn = os.path.join(os.path.join(self.home,'conf'),'codes.conf')
        f = open(fn,'r')
        lines = f.readlines()
        f.close()
        self._codes = set()
        for line in lines:
            self._codes.add(line.strip())

    def _updateoffday(self):
        fn = os.path.join(os.path.join(self.home,'conf'),'offday.conf')
        f = open(fn,'r')
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

    def put(self,obj):
        self._queue.put(obj)

    def get(self):
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
        self._updatecodes()
        self._updateoffday()

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
        return list(self._codes)

    def run(self):
        pass
    
    def handle_message(self,msg):
        pass

class iktask(ikbase):
    def __init__(self,logfile=None):
        if logfile:
            ikbase.__init__(self,logfile)
        else:
            ikbase.__init__(self,os.path.join(os.path.join(g_home,'log'),'iktask.log'))
        self._tasklist = []
        self._rts = [(9,31),(9,41),(9,51),(10,1),(10,11),(10,21),(10,31),(10,41),(10,51),(11,1),(11,11),(11,21),(13,10),(13,20),(13,30),(13,40),(13,50),(14,0),(14,10),(14,20),(14,30),(14,40),(14,50),(15,0)]

    def _loadtask(self):
        cur = None
        if len(self._tasklist)==0:
            now = datetime.datetime.now()
            if self.isopenday():
                if now.hour<=14:
                    cur = HY_TASK_BEFOREOPEN
                    for p in self._rts:
                        if p > (now.hour,now.minute):
                            self._tasklist.append(('%04d%02d%02d%02d%02d'%(now.year,now.month,now.day,p[0],p[1]),HY_TASK_REALTIME))
                    self._tasklist.append(('%04d%02d%02d%02d%02d'%(now.year,now.month,now.day,17,0),HY_TASK_AFTERCLOSE))
                elif now.hour<17:
                    self._tasklist.append(('%04d%02d%02d%02d%02d'%(now.year,now.month,now.day,17,0),HY_TASK_AFTERCLOSE))
                else:
                    cur = HY_TASK_BEFOREOPEN
            next = self.nextopenday()
            for p in self._rts:
                self._tasklist.append(('%s%02d%02d'%(next,p[0],p[1]),HY_TASK_REALTIME))
            self._tasklist.append(('%s1700'%(next),HY_TASK_AFTERCLOSE))
        return cur

    def onrttask(self):
        pass

    def onafterclose(self):
        pass

    def onbeforeopen(self):
        pass

    def onupdateinfo(self):
        self.loadinfo()

    def handle_message(self,msg):
        if msg[1] == HY_TASK_REALTIME:
            self.onrttask()
        elif msg[1] == HY_TASK_AFTERCLOSE:
            self.onafterclose()
        elif msg[1] == HY_TASK_BEFOREOPEN:
            self.onbeforeopen()
        elif msg[1] == HY_TASK_UPDATEINFO:
            self.onupdateinfo()
        else:
            self.error('iktask unknown task[%s]'%task)

    def _taskworker(self):
        self.info('iktask pid[%d] _taskworker thread start....'%(os.getpid()))
        while 1:
            task = self.get()
            self.info('pid[%d] _taskworker get task[%s]'%(os.getpid(),task))
            begin = datetime.datetime.now()
            self.handle_task(task)
            during = datetime.datetime.now()-begin
            self.info('iktask pid[%d] _taskworker did task[%s] with seconds[%d]'%(os.getpid(),task,during.seconds))

    def run(self):
        worker = threading.Thread(target=self._taskworker)
        worker.start()
        self.info('iktask pid[%d] run thread start....'%os.getpid())
        while 1:
            task = self._loadtask()
            if task:
                self.put(task)
            else:
                now = datetime.datetime.now()
                if '%04d%02d%02d%02d%02d'%(now.year,now.month,now.day,now.hour,now.minute)==self._tasklist[0][0]:
                    self.put(self._tasklist.pop(0))
            time.sleep(2)
            
class iknet(ikbase):
    def __init__(self,logfile,host,port,connnum):
        if logfile:
            ikbase.__init__(self,logfile)
        else:
            ikbase.__init__(self,os.path.join(os.path.join(g_home,'log'),'iknet.log'))
        self._host = host
        self._port = port
        self._connnum = connnum

    def handle_massage(self,msg):
        pass

    def _networker(self):
        self.info('iknet pid[%d] _networker thread start....'%(os.getpid()))
        while 1:
            try:
                client,data = self.get()
                self.info('iknet pid[%d]_networker get msg[%d] from %s'%(os.getpid(),len(data),client))
                data = json.loads(data)
                if data.has_key('name') and data.has_key('paras'):
                    self.handle_massage((client,data['name'],data['paras']))
                else:
                    client.send(json.loads('{"retcode":1001,"errmsg":"invalid"}'))
            except Exception,e:
                self.error('iknet pid[%d] _network exception[%s]'%(os.getpid(),e))

    def run(self):
        ADDR = (self._host,self._port)
        sock = socket(AF_INET,SOCK_STREAM)
        sock.bind(ADDR)
        sock.listen(self._connnum)
        self.info('iknet pid[%d] listening port[%s:%d]'%(os.getpid(),self._host,self._port))
        worker = threading.Thread(target=self._networker)
        worker.start()
        while True:
            client,addr = sock.accept()
            self.info('iknet pid[%d] connected from addr[%s]'%(os.getpid(),addr))
            while True:
                try:
                    data = client.recv(4096)
                    self.put((client,data))
                except Exception,e:
                    self.info('iknet pid[%d] data exception[%s]'%(os.getpid(),e))
            time.sleep(1)
            client.close()
        client.close()

class iknow(object):
    def __init__(self,conf=None):
        self.conf = conf
        if not conf:
            home = os.getenv('IKNOW_HOME')
            if not home:
                raise Exception('env IKNOW_HOME is missing')
            self.conf = os.path.join(os.path.join(home,'conf'),'iknow.conf')
        if not os.path.isfile(self.conf):
            raise Exception('configuration file[%s] missing'%self.conf)
        config = ConfigParser.ConfigParser()
        config.read(self.conf)
        self._logfile = config.get('iknow','logfile')
        self._libdir = config.get('iknow','libdir')
        self._host = host
        self._port = port
        self._connnum = connnum

    def _iknet(self,args):
        net = iknet(self._logfile,self._host,self._port,self._connnum)
        net.run()
    
    def _iktask(self,args):
        task = iktask(self._logfile)
        task.run()
    
    def start(self):
        pnet = multiprocessing.Process(target = self._iknet, args = (None,))
        pnet.start()
        pnet.join()
        ptask = multiprocessing.Process(target = self._iktask, args = (None,))
        ptask.start()
        ptask.join()
        

if __name__ == "__main__":
    ik = iknow()
    ik.start()




