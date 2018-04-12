#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import random
import socket
import urllib2
import commands
import random
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')

sys.path.append(os.path.join(g_home,'lib'))
from dealerlib import dealerlib
from hylib import hylib
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('iksnow')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'iksnow.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class iksnow2:
    def __init__(self):
        self._dealer = dealerlib()
        self._hylib  = hylib()
        self._uid = 'snow-2'
        self._last = None
        self._opensell = []
    
    def __del__(self):
        pass

    def plan(self):
        tell = self._hylib.lasttell()
        if self._last == tell[1]:
            return
        buys = self._hylib.tellbuy()
        sells = self._hylib.tellsell()
        accs = self._dealer.query(self._uid)
        cash = accs[0][0]
        value = accs[0][1]
        holds = accs[1]
        for h in holds:
            orderid = h[0]
            code = h[1]
            amount = h[2]
            bprice = h[3]
            sur = h[4]
            tinf = self._hylib.lastdata(code)
            close = tinf[0][0]
            ps = tinf[3]
            lose = close*(1+(float(ps[4])-float(ps[5]))/100)
            if tinf[2][0]==2:
                if len(sells)>400:
                    win = tinf[2][3]
                    if win<close:
                        win = close
                    self._dealer.set(orderid,win,lose)
                else:
                    self._opensell.append(orderid)
            elif sur>=5:
                self._opensell.append(orderid)
            else:
                wwin = close*(1+(float(ps[2])+2*float(ps[3]))/100)
                self._dealer.set(orderid,wwin,lose)
        if len(buys)>450:
            buys = buys[:-5]
            all = cash+value
            g_logger.info('iksnow2 plan for next day[%s] all[%s] cash[%s]'%(next,str(all),str(cash)))
            while cash > all*0.2:
                use = all*0.2
                item = buys.pop()
                code = item[0]
                tinf = self._hylib.lastdata(code)
                close = tinf[0][0]
                amount = int((use/close)/100)
                self._dealer.put(self._uid,code,amount,close)
                g_logger.info('put order ret[%s,%s,%d,%0.2f]'%(self._uid,code,amount,close))
                cash = cash-close*amount
            if cash > all*0.1:
                item = buys.pop()
                code = item[0]
                tinf = self._hylib.lastdata(code)
                close = tinf[0][0]
                amount = int((use/close)/100)
                self._dealer.put(self._uid,code,amount,close)
                g_logger.info('iksnow2 put order ret[%s,%s,%d,%0.2f]'%(self._uid,code,amount,close))
        self._last = tell[1]
        g_logger.info('iksnow2 plan for next day[%s] is done....'%(self._last))

    def run(self):
        g_logger.info('iksnow2 start....')
        if not self._dealer.user(self._uid):
            self._dealer.create(self._uid)
            self._dealer.deposit(self._uid,1000000)
        while 1:
            mk = self._dealer.market()
            st = self._hylib.process()
            if int(time.time())%10==0:
                g_logger.info('iksnow2 dealer market[%d] hylib process[%s]....'%(mk,st))
            if st == 'done' and mk==5:
                self.plan()
            if mk>=1 and mk<=2:
                for slorder in self._opensell:
                    self._dealer.close(slorder)
            elif mk==3:
                self._opensell = []
            time.sleep(1)
        g_logger.info('iksnow2 exit....')

if __name__ == "__main__":
    iksnow2().run()


