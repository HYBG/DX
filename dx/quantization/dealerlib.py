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
from datetime import timedelta
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import MySQLdb
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('dealer')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'dealer.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class dealerlib:
    def __init__(self):
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='dealer',charset='utf8') 
        self._cursor = self._conn.cursor()

    def __del__(self):
        self._cursor.close()
        self._conn.close()

    def _buildid(self,prefix):
        now = datetime.datetime.now()
        return "%s%04d%02d%02d%02d%02d%02d%05d"%(prefix,now.year,now.month,now.day,now.hour,now.minute,now.second,random.randint(10000,99999))

    def _reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='dealer',charset='utf8') 
        self._cursor = self._conn.cursor()
    
    def _exesqlone(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchone()
        
    def _exesqlbatch(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchall()
        
    def _task(self,sqls,log=False):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                if log:
                    g_logger.info('execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                g_logger.error('execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True

    def rtprice(self,code):
        market = None
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        else:
            market = 'sz'
        url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            v = None
            now = datetime.datetime.now()
            if int(info[8])>0 and info[30]=='%04d-%02d-%02d'%(now.year,now.month,now.day):
                v = info
            return v
        except Exception, e:
            g_logger.warning('get current price code[%s] exception[%s]'%(code,e))
            return None

    def user(self,userid):
        ext = self._exesqlone('select count(*) from dealer_user where userid=%s',(userid,))
        if ext[0]>0:
            return True
        return False

    def market(self):
        mkt = self._exesqlone('select value from dealer_global where name=%s',('market',))
        if len(mkt)>0:
            return int(mkt[0])
        return 0

    def create(self,userid):
        now = datetime.datetime.now()
        self._task([('insert into dealer_user(userid,rdate) values(%s,%s)',(userid,'%04d-%02d-%02d'%(now.year,now.month,now.day)))])

    def deposit(self,userid,amount):
        now = datetime.datetime.now()
        dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
        tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
        sqls = []
        sid = self._buildid('S')
        sqls.append(('update dealer_user set cash=cash+%s where userid=%s',(amount,userid)))
        sqls.append(('insert into dealer_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,userid,dt,tm,amount)))
        self._task(sqls)

    def open(self,userid,code,amount):
        inf = self._exesqlone("select dealer_global.value,dealer_code.status from dealer_global,dealer_code where dealer_global.name=%s and dealer_code.code=%s",('market',code))
        if (inf[0]!="1" and inf[0]!="2" and inf[2]!="1"):
            return False
        have = self._exesqlone('select cash from dealer_user where userid=%s',(userid,))
        have = have[0]
        ps = self.rtprice(code)
        need = float(ps[7])*amount*100
        if have>=need:
            oid = self._buildid('O')
            now = datetime.datetime.now()
            dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
            sqls = []
            sqls.append(('insert into dealer_order_open(orderid,userid,putdate,puttime,opendate,opentime,code,amount,openprice) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,dt,tm,code,amount*100,ps[7])))
            sqls.append(('update dealer_user set cash=cash-%s where userid=%s',(need,userid)))
            sid = self._buildid('S')
            sqls.append(('insert into dealer_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,userid,dt,tm,'%0.2f'%(-1*need))))
            if 0 == self._task(sqls):
                return True
        return False

    def put(self,userid,code,amount,price):
        st = self._exesqlone("select value from dealer_global where name=%s",('market',))
        if st[0]=="4":
            return False
        have = self._exesqlone('select cash from dealer_user where userid=%s',(userid,))
        have = have[0]
        need = price*amount*100
        if have>=need:
            oid = self._buildid('O')
            now = datetime.datetime.now()
            dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
            sqls = []
            sqls.append(('insert into dealer_order_put(orderid,userid,putdate,puttime,code,amount,putprice,freeze) values(%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,code,amount*100,price,need)))
            sqls.append(('update dealer_user set cash=cash-%s where userid=%s',(need,userid)))
            sid = self._buildid('S')
            sqls.append(('insert into dealer_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,userid,dt,tm,'%0.2f'%(-1*need))))
            if 0 == self._task(sqls):
                return True
        return False

    def close(self,orderid):
        st = self._exesqlone("select value from dealer_global where name=%s",('market',))
        if st[0]=="4":
            return False
        openorder = self._exesqlone('select userid,opendate,opentime,code,amount,openprice from dealer_order_open where orderid=%s',(orderid,))
        if len(openorder)>0:
            sqls = []
            now = datetime.datetime.now()
            dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
            ps = self.rtprice(openorder[3])
            gain = float(ps[6])*float(openorder[4])
            commission = gain*0.0015;
            earn = '%0.2f'%(gain-commission)
            commission = '%0.2f'%commission
            gain = '%0.2f'%gain
            sqls.append(('insert into dealer_order_close(orderid,userid,opendate,opentime,closedate,closetime,code,amount,openprice,closeprice,commission,earn) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(orderid,openorder[0],openorder[1],openorder[2],dt,tm,openorder[3],openorder[4],openorder[5],ps[6],commission,earn)))
            sqls.append(('delete from dealer_order_open where orderid=%s',(orderid,)))
            sqls.append(('update dealer_user set cash=cash+%s',(earn,)))
            sid = self._buildid('S')
            sqls.append(('insert into dealer_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,openorder[0],dt,tm,earn)))
            if 0 == self._task(sqls):
                return True
        return False
        
    def cancel(self,orderid):
        st = self._exesqlone("select value from dealer_global where name=%s",('market',))
        if st[0]=="4":
            return False
        putorder = self._exesqlone('select userid,putdate,puttime,code,amount,putprice,freeze from dealer_order_put where orderid=%s',(orderid,))
        if len(putorder)>0:
            sqls = []
            now = datetime.datetime.now()
            dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
            sqls.append(('insert into dealer_order_cancel(orderid,userid,putdate,puttime,canceldate,canceltime,code,amount,putprice) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(orderid,putorder[0],putorder[1],putorder[2],dt,tm,putorder[3],putorder[4],putorder[5])))
            sqls.append(('delete from dealer_order_put where orderid=%s',(orderid,)))
            sqls.append(('update dealer_user set cash=cash+%s',(putorder[6],)))
            sqls.append(('insert into dealer_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,putorder[0],dt,tm,putorder[6])))
            if 0 == self._task(sqls):
                return True
        return False

    def set(self,orderid,win,lose):
        st = self._exesqlone("select value from dealer_global where name=%s",('market',))
        if st[0]=="4":
            return False
        openorder = self._exesqlone('select userid,win,lose from dealer_order_open where orderid=%s',(orderid,))
        if len(openorder)>0:
            sqls = []
            if win and lose:
                sqls.append(('update dealer_order_open set win=%s and lose=%s where orderid=%s',(win,lose,orderid)))
            elif not lose and win:
                sqls.append(('update dealer_order_open set win=%s where orderid=%s',(win,orderid)))
            elif not win and lose:
                sqls.append(('update dealer_order_open set lose=%s where orderid=%s',(lose,orderid)))
            else:
                return False
            if 0 == self._task(sqls):
                return True
        return False

    def query(self,userid):
        money = self._exesqlone('select cash,value from dealer_user where userid=%s',(userid,))
        holds = self._exesqlbatch('select userid,code,amount,openprice,surviving from dealer_order_open where userid=%s',(userid,))       
        puts = self._exesqlbatch('select orderid,code,amount,putprice,freeze from dealer_order_put where userid=%s',(userid,))
        return (money,holds,puts)
        
    def subscribe(self,userid,code):
        hasc = self._exesqlone('select count(*) from dealer_subscribe where userid=%s and code=%s',(userid,code))
        if hasc[0] == 0:
            self._task([('insert into dealer_subscribe(userid,code) values(%s,%s)',(userid,code))])
        
    def unsubscribe(self,userid,code):
        hasc = self._exesqlone('select count(*) from dealer_subscribe where userid=%s and code=%s',(userid,code))
        if hasc[0] != 0:
            self._task([('delete from dealer_subscribe where userid=%s and code=%s',(userid,code))])
        
    def getprice(self,code):
        price = self._exesqlone('select price from dealer_subscribe_code where code=%s',(code,))
        if len(price)>0:
            return price[0]
        return None
        
