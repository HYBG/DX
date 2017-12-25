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
g_logger = logging.getLogger('iktrader')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'iktrader.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class iktrader:
    def __init__(self):
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()

    def __del__(self):
        self._cursor.close()
        self._conn.close()

    def _buildid(self,prefix):
        now = datetime.datetime.now()
        return "%s%04d%02d%02d%02d%02d%02d%05d"%(prefix,now.year,now.month,now.day,now.hour,now.minute,now.second,random.randint(10000,99999))

    def _user(self,userid):
        ext = self.exesqlone('select count(*) from trader_user where userid=%s',(userid,))
        if ext[0]>0:
            return True
        return False

    def reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()
    
    def exesqlone(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchone()
        
    def exesqlbatch(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchall()
        
    def task(self,sqls,log=False):
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

    def market(self):
        mkt = self.exesqlone('select value from trader_global where name=%s',('market',))
        if len(mkt)>0:
            return mkt[0]
        return 0

    def create(self,userid):
        if self._user(userid):
            return (10010,'user[%s] has been exist'%userid)
        now = datetime.datetime.now()
        if 0 == self.task([('insert into trader_user(userid,rdate) values(%s,%s)',(userid,'%04d-%02d-%02d'%(now.year,now.month,now.day)))]):
            return (10000,'successfully')
        return (10002,'create user[%s] failed'%userid)

    def deposit(self,userid,amount):
        if not self._user(userid):
            return (10010,'user[%s] not exist'%userid)
        if amount <= 0:
            return (10011,'parameter[%0.2f] error'%amount)
        now = datetime.datetime.now()
        dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
        tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
        sqls = []
        sid = self._buildid('S')
        sqls.append(('update trader_user set cash=cash+%s where userid=%s',(amount,userid)))
        sqls.append(('insert into trader_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,userid,dt,tm,amount)))
        if 0 == self.task(sqls):
            return (10000,'successfully')
        return (10002,'deposit[%0.2f] user[%s] failed'%(amount,userid))

    def open(self,userid,code,amount,win,lose):
        st = self.exesqlone("select value from trader_global where name=%s",('market',))
        if (st[0]!="1" and st[0]!="2"):
            return (10020,'timing is wrong')
        st = self.exesqlone("select status from trader_code where code=%s",(code,))
        if st[0]!='1':
            return (10021,'stock[%s] is not trading'%code)
        have = self.exesqlone('select cash from trader_user where userid=%s',(userid,))
        have = have[0]
        ps = self.rtprice(code)
        need = float(ps[7])*amount*100
        if have>=need:
            oid = self._buildid('O')
            now = datetime.datetime.now()
            dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
            sqls = []
            if not (win or lose):
                sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,opendate,opentime,code,amount,openprice) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,dt,tm,code,amount*100,ps[7])))
            elif win and not lose:
                sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,opendate,opentime,code,amount,openprice,win) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,dt,tm,code,amount*100,ps[7],win)))
            elif lose and not win:
                sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,opendate,opentime,code,amount,openprice,lose) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,dt,tm,code,amount*100,ps[7],lose)))
            else:
                sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,opendate,opentime,code,amount,openprice,win,lose) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,dt,tm,code,amount*100,ps[7],win,lose)))
            sqls.append(('update trader_user set cash=cash-%s where userid=%s',(need,userid)))
            sid = self._buildid('S')
            sqls.append(('insert into trader_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,userid,dt,tm,'%0.2f'%(-1*need))))
            if 0 == self.task(sqls):
                return (10000,'successfully')
            return (10002,'user[%s] open order failed'%(userid))
        return (10004,'user[%s] cash not enough'%(userid))

    def put(self,userid,code,amount,price,win,lose):
        st = self.exesqlone("select value from trader_global where name=%s",('market',))
        if (st[0]!="1" and st[0]!="2"):
            return (10020,'timing is wrong')
        st = self.exesqlone("select status from trader_code where code=%s",(code,))
        if st[0]!='1':
            return (10021,'stock[%s] is not trading'%code)
        have = self.exesqlone('select cash from trader_user where userid=%s',(userid,))
        have = have[0]
        ps = self.rtprice(code)
        need = float(ps[7])*amount*100
        if have>=need:
            oid = self._buildid('O')
            now = datetime.datetime.now()
            dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
            sqls = []
            if not (win or lose):
                sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,code,amount,putprice,freeze) values(%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,code,amount*100,ps[7],need)))
            elif win and not lose:
                sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,code,amount,openprice,freeze,win) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,code,amount*100,ps[7],need,win)))
            elif lose and not win:
                sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,code,amount,openprice,freeze,lose) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,code,amount*100,ps[7],need,lose)))
            else:
                sqls.append(('insert into trader_order_open(orderid,userid,putdate,puttime,code,amount,openprice,freeze,win,lose) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(oid,userid,dt,tm,code,amount*100,ps[7],need,win,lose)))
            sqls.append(('update trader_user set cash=cash-%s where userid=%s',(need,userid)))
            sid = self._buildid('S')
            sqls.append(('insert into trader_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,userid,dt,tm,'%0.2f'%(-1*need))))
            if 0 == self.task(sqls):
                return (10000,'successfully')
            return (10002,'user[%s] put order failed'%(userid))
        return (10004,'user[%s] cash not enough'%(userid))
        
    def close(self,orderid):
        st = self.exesqlone("select value from trader_global where name=%s",('market',))
        if st[0]=="4":
            return (10020,'timing is wrong')
        openorder = self.exesqlone('select userid,opendate,opentime,code,amount,openprice from trader_order_open where orderid=%s',(orderid,))
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
            sqls.append(('insert into trader_order_close(orderid,userid,opendate,opentime,closedate,closetime,code,amount,openprice,closeprice,commission,earn) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',(orderid,openorder[0],openorder[1],openorder[2],dt,tm,openorder[3],openorder[4],openorder[5],ps[6],commission,earn)))
            sqls.append(('delete from trader_order_open where orderid=%s',(orderid,)))
            sqls.append(('update trader_user set cash=cash+%s',(earn,)))
            sid = self._buildid('S')
            sqls.append(('insert into trader_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,openorder[0],dt,tm,earn)))
            if 0 == self.task(sqls):
                return (10000,'successfully')
            return (10002,'user[%s] close order failed'%(openorder[0]))
        return (10004,'order[%s] not exist'%(orderid))
        
    def cancel(self,orderid):
        st = self.exesqlone("select value from trader_global where name=%s",('market',))
        if st[0]=="4":
            return (10020,'timing is wrong')
        putorder = self.exesqlone('select userid,putdate,puttime,code,amount,putprice,freeze from trader_order_put where orderid=%s',(orderid,))
        if len(putorder)>0:
            sqls = []
            now = datetime.datetime.now()
            dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
            tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
            sqls.append(('insert into trader_order_cancel(orderid,userid,putdate,puttime,canceldate,canceltime,code,amount,putprice) values(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(orderid,putorder[0],putorder[1],putorder[2],dt,tm,putorder[3],putorder[4],putorder[5])))
            sqls.append(('delete from trader_order_put where orderid=%s',(orderid,)))
            sqls.append(('update trader_user set cash=cash+%s',(putorder[6],)))
            sqls.append(('insert into trader_account_record(seqid,userid,date,time,amount) values(%s,%s,%s,%s,%s)',(sid,putorder[0],dt,tm,putorder[6])))
            if 0 == self.task(sqls):
                return (10000,'successfully')
            return (10002,'user[%s] cancel order failed'%(putorder[0]))
        return (10004,'order[%s] not exist'%(orderid))

    def set(self,orderid,win,lose):
        st = self.exesqlone("select value from trader_global where name=%s",('market',))
        if st[0]=="4":
            return (10020,'timing is wrong')
        openorder = self.exesqlone('select userid,win,lose from trader_order_open where orderid=%s',(orderid,))
        if len(openorder)>0:
            sqls = []
            if win and lose:
                sqls.append(('update trader_order_open set win=%s and lose=%s where orderid=%s',(win,lose,orderid)))
            elif not lose and win:
                sqls.append(('update trader_order_open set win=%s where orderid=%s',(win,orderid)))
            elif not win and lose:
                sqls.append(('update trader_order_open set lose=%s where orderid=%s',(lose,orderid)))
            else:
                return (10011,'parameter error')
            if 0 == self.task(sqls):
                return (10000,'successfully')
            return (10002,'orderid[%s] set win/lose failed'%(orderid))
        return (10004,'order[%s] not exist'%(orderid))

    def query(self,userid):
        money = self.exesqlone('select cash,value from trader_user where userid=%s',(userid,))
        holds = self.exesqlbatch('select userid,code,amount,openprice,surviving from trader_order_open where userid=%s',(userid,))       
        puts = self.exesqlbatch('select orderid,code,amount,putprice,freeze from trader_order_put where userid=%s',(userid,))
        return (money,holds,puts)
        
    def next(self):
        now = datetime.datetime.now()
        start = datetime.date(now.year,now.month,now.day)
        if now.hour>=9:
            start = datetime.date.today()+timedelta(days=1)
        wd = start.isoweekday()
        rest = self.exesqlone('select count(*) from trader_global where name=%s',('%04d-%02d-%02d'%(start.year,start.month,start.day),))
        while wd != 6 and wd != 7 and rest[0]==0:
            start = start+timedelta(days=1)
            wd = start.isoweekday()
            rest = self.exesqlone('select count(*) from trader_global where name=%s',('%04d-%02d-%02d'%(start.year,start.month,start.day),))
        return '%04d-%02d-%02d'%(start.year,start.month,start.day)
                 

        
        
        
