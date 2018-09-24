#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import Queue
from optparse import OptionParser
from logging.handlers import RotatingFileHandler

class ikbase(object):
    def __init__(self,logfile=None):
        self.home = os.getenv('IKNOW_HOME','/var/data/iknow')
        self._logger = logging.getLogger('iknow')
        formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        fmter = logging.Formatter(formatstr)
        rh = None
        if logfile:
            rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
        else:
            rh = RotatingFileHandler(os.path.join(os.path.join(self.home,'log'),'ikbase.log'), maxBytes=100*1024*1024,backupCount=50)
        #rh.setLevel(logging.INFO)
        rh.setFormatter(fmter)
        self._logger.addHandler(rh)
        self._logger.setLevel(logging.INFO)
        self._handlers = []
        self._openday = None
        self._next = None
        self._taskq = Queue.Queue()

    def _setopenday(self):
        fn = os.path.join(os.path.join(self.home,'conf'),'offday.conf')
        now = datetime.datetime.now()
        td = '%04d-%02d-%02d'%(now.year,now.month,now.day)
        wd = now.isoweekday()
        if wd==6 or wd==7:
            self._openday = False
        else:
            f = open(fn,'r')
            lines = f.readlines()
            f.close()
            self._openday = True
            for row in lines:
                if row.strip()==td:
                    self._openday = False
                    break
            if self._openday:
                if now<datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0):
                    self.onbeforeopen()
        if self._openday:
            self._logger.info('iknow date[%s] is open day'%td)
        else:
            self._logger.info('iknow date[%s] is off day'%td)

    def _init(self):
        now = datetime.datetime.now()
        now = (now.hour,now.minute)
        self._setopenday()
        self._handlers.sort(key=lambda x:x[1])
        for item in self._handlers:
            if item[0]=='all' and item[1]>now:
                self._taskq.put((item[1],item[2]))
            if item[0]=='open' and self._openday and item[1]>now:
                self._taskq.put((item[1],item[2]))
            if item[0]=='close' and (not self._openday) and item[1]>now:
                self._taskq.put((item[1],item[2]))
        if self._taskq.empty():
            self._next = ((0,1),self._initday)
        self._next = self._taskq.get()
        self._logger.info('iknow init done')

    def _initday(self):
        self._setopenday()
        self._handlers.sort(key=lambda x:x[1])
        for item in self._handlers:
            if item[0]=='all' and item[1]>(0,1):
                self._taskq.put((item[1],item[2]))
            if item[0]=='open' and self._openday and item[1]>(0,1):
                self._taskq.put((item[1],item[2]))
            if item[0]=='close' and (not self._openday) and item[1]>(0,1):
                self._taskq.put((item[1],item[2]))
        if self._taskq.empty():
            while 1:
                now = datetime.datetime.now()
                if now>datatime.datetime(year=now.year,month=now.month,day=now.day,hour=0,minute=1,second=0):
                    self._next = ((0,1),self._initday)
                    break
                time.sleep(5)
        self._next = self._taskq.get()
        now = datetime.datetime.now()
        self._logger.info('iknow init[%04d-%02d-%02d %02d:%02d:%02d] done'%(now.year,now.month,now.day,now.hour,now.minute,now.second))

    def _gettask(self):
        if not self._taskq.empty():
            return self._taskq.get()
        return ((0,1),self._initday)

    def addhandler(self,openday,time,handler):
        self._handlers.append((openday,time,handler))

    def setloglevel(self,level):
        self._logger.setLevel(level)

    def onafterclose(self):
        pass

    def onbeforeopen(self):
        pass

    def debug(self,str):
        self._logger.debug(str)

    def info(self,str):
        self._logger.info(str)

    def error(self,str):
        self._logger.error(str)
        
    def loadcsv(self,filename):
        f = open(filename,'r')
        lines = f.readlines()
        f.close()
        mat = []
        for line in lines:
            items = line.split(',')
            if len(items)==1:
                mat.append(items[0].strip())
            elif len(items)>1:
                tmp = []
                for it in items:
                    tmp.append(it.strip())
                mat.append(tmp)
        return mat

    def codes(self):
        return self.loadcsv(os.path.join(os.path.join(self.home,'conf'),'codes.conf'))

    def run(self):
        self._init()
        while 1:
            now = datetime.datetime.now()
            now = (now.hour,now.minute)
            if now == self._next[0]:
                self._logger.info('iknow execute task[%s] time[%s]'%(str(self._next[1]),str(self._next[0])))
                self._next[1]()
                self._next = self._gettask()
            time.sleep(4)


if __name__ == "__main__":
    ik = ikbase()
    ik.run()

    
    