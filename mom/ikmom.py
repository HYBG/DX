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
import MySQLdb
reload(sys)
sys.setdefaultencoding('utf8')

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')
    
logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('ikmom')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'ikmom.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class ikmom:
    def __init__(self):
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
        self._cursor = self._conn.cursor()
    
    def __del__(self):
        self._cursor.close()
        self._conn.close()
        
    def _reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='hy',charset='utf8') 
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
        
    def _loadusers(self):
        "select "
        
    def _buildid(self,prefix):
        now = datetime.datetime.now()
        return "%s%04d%02d%02d%02d%02d%02d%05d"%(prefix[0],now.year,now.month,now.day,now.hour,now.minute,now.second,random.randint(10000,99999))

    def _buysell_v(self,pid,bs,code,amount,price):
        if (bs==0):
            need = '%0.2f'%(price*amount*1.0003)
            have = self._exesqlone("select cash from ikmom_invest_account_v where pid=%s",(pid,))
            if (have[0]>need):
                seq = self._buildid('O')
                oseq = self._buildid('S')
                now = datetime.datetime.now()
                td = '%04d-%02d-%02d'%(now.year,now.month,now.day)
                tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
                sqls = []
                sqls.append(("insert into ikmom_order_seq_v(seqnum,pid,date,time,otype,orderseq) values(%s,%s,%s,%s,0,%s)",(oseq,pid,td,tm,seq)))
                sqls.append(("insert into ikmom_order_v(seqnum,pid,buysell,code,amount,price,status) values(%s,'%s,0,%s,%s,%s,0)",(seq,pid,code,amount,price)))
                sqls.append(("update ikmom_invest_account_v set cash=cash-%s,freeze=freeze+%s where pid=%s",(need,need,pid)))
                return self._task(sqls)
            else:
                return False
        elif(bs==1):
            have = self._exesqlone("select amount from ikmom_project_hold_v where pid=%s and code=%s",(pid,code))
            if len(have)>0:
                if have[0]>=amount:
                    seq = self._builid('O')
                    oseq = self._builid('S')
                    now = datetime.datetime.now()
                    td = '%04d-%02d-%02d'%(now.year,now.month,now.day)
                    tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
                    sqls = []
                    sqls.append(("insert into ikmom_order_seq_v(seqnum,pid,date,time,otype,orderseq) values(%s,%s,%s,%s,1,%s)",(oseq,pid,td,tm,seq)))
                    sqls.append(("insert into ikmom_order_v(seqnum,pid,buysell,code,amount,price,status) values(%s,%s,1,%s,%s,%s,0)",(seq,pid,code,amount,price)))
                    sqls.append(("update ikmom_project_hold_v set amount=amount-%s,freeze=freeze+%s where pid=%s and code=%s",(amount,amount,pid,code)))
                    return self._task(sqls)
                else:
                    return False
        return False

    def _isopen(self):
        now = datetime.datetime.now()
        wd = now.isoweekday()
        o1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=9,minute=30,second=0)
        c1 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=11,minute=30,second=0)
        o2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=13,minute=0,second=0)
        c2 = datetime.datetime(year=now.year,month=now.month,day=now.day,hour=15,minute=0,second=0)
        if wd == 6 or wd == 7:
            return False
        if now < o1 or now > c2 or (now>c1 and now < o2):
            return False
        url = 'http://hq.sinajs.cn/list=sz399001'
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            if info[-3] == '%04d-%02d-%02d'%(now.year,now.month,now.day):
                return True
        except Exception, e:
            g_logger.warning('get current url[%s] exception[%s]'%(url,e))
            return None

    def _rtprice(self,code):
        market = None
        if code[:2]=='60' or code[0]=='5':
            market = 'sh'
        else:
            market = 'sz'
        url = 'http://hq.sinajs.cn/list=%s%s'%(market,code)
        try:
            line = urllib2.urlopen(url).readline()
            info = line.split('"')[1].split(',')
            v = (info[-3],float(info[1]),float(info[4]),float(info[5]),float(info[3]),int(info[8]),float(info[2]))
            return v
        except Exception, e:
            g_logger.warning('get current price code[%s] exception[%s]'%(code,e))
            return None
            
    def dailytask(self):
        g_logger.info('dailytask start....')
        pinfs = self._exesqlbatch('select pid,baseline,peak,manager,retmax from ikmom_project_v where status=0 or status=3',None)
        for pinf in pinfs:
            sqls = []
            pid = pinf[0]
            bl = pinf[1]
            pk = pinf[2]
            uid = pinf[3]
            rmax = pinf[4]
            data = self._exesqlbatch("select code,amount from ikmom_project_hold_v where pid=%s",(pid,))
            val = 0.0
            for row in data:
                close = self._rtprice(row[0])
                val = val + close[4]*float(row[1])
            fre = self._exesqlone("select freeze from ikmom_invest_account_v where pid=%s",(pid,))
            if fre[0] != 0:
                self._task([('update ikmom_invest_account_v set cash=cash+freeze,freeze=0 where pid=%s',(pid,))],True)
            money = self._exesqlone("select cash from ikmom_invest_account_v where pid=%s",(pid,))
            all = val + money[0]
            rate = (all-bl)/bl
            if all>pk:
                pk = all
            rt = (all-pk)/pk
            status = 0
            sm = self._exesqlone("select settlemin from ikmom_user where uid=%s",(uid,))
            g_logger.info('pid[%s] all[%0.2f] peak[%0.2f] ret[%0.2f] rmax[%0.2f]'%(pid,all,pk,rt,rmax))
            if rate>=sm[0]:
                if abs(rt)>rmax:
                    status = 4
                else:
                    status = 3
            elif abs(rt)>rmax:
                status = 5
            sqls.append(("update ikmom_project_v set rate=%s,peak=%s,status=%s where manager=%s",(rate,pk,status,uid)))
            codes = self._exesqlbatch("select code from ikmom_project_hold_v where pid=%s",(pid,))
            for code in codes:
                hold = self._exesqlone("select amount,freeze from ikmom_project_hold_v where pid=%s and code=%s",(pid,code[0]))
                amt = hold[0]+hold[1]
                g_logger.info('dailytask hold code[%s],amount[%d],freeze[%d]'%(code[0],hold[0],hold[1]))
                if hold[1]>0:
                    sqls.append(("update ikmom_project_hold_v set amount=%s,freeze=0 where pid=%s and code=%s",(amt,pid,code[0])))
                elif amt==0:
                    sqls.append(("delete from ikmom_project_hold_v where pid=%s and code=%s",(pid,code[0])))
                now = datetime.datetime.now()
                dt = '%04d-%02d-%02d'%(now.year,now.month,now.day)
                tm = '%02d:%02d:%02d'%(now.hour,now.minute,now.second)
                sqls.append(("insert into ikmom_hold_snapshot_v(pid,code,amount,date,time) values(%s,%s,%s,%s,%s)",(pid,code[0],amt,dt,tm)))
            self._task(sqls,True)
        g_logger.info('dailytask done....')

    def assignproject_v(self):
        g_logger.info('assignproject_v start....')
        data = self._exesqlbatch("select code,amount from ikmom_project_hold_v where pid in (select pid from ikmom_project_v where status=1)",None)
        sqls = []
        for row in data:
            close = self._rtprice(row[0])
            uids = self._exesqlbatch("select manager,baseline from ikmom_project_v where status=0 or status=3",None)
            val = float(row[1])*close[4]
            for uid in uids:
                limp = self._exesqlone("select limper from ikmom_user where uid='%s'",(uid[0],))
                buf = limp[0]-uid[1]
                if (buf>val):
                    seq = self._builid('S')
                    sqls.append(("insert into ikmom_assign_v(seqnum,uid,code,amount,price,status) values(%s,%s,%s,%s,%s,0)",(seq,uid[0],row[0],row[1],close[4])))
                    break
        self._task(sqls)
        g_logger.info('assignproject_v done....')

    def run(self):
        g_logger.info('ikmom trade start....')
        while 1:
            now = datetime.datetime.now()
            wd = now.isoweekday()
            if self._isopen():
                self._reconn()
                data = self._exesqlbatch('select seqnum,pid,buysell,code,amount,price from ikmom_order_v where status=0',None)
                g_logger.info('ikmom there are %d orders waiting...'%len(data))
                for row in data:
                    p = self._rtprice(row[3])
                    sqls = []
                    if row[2]==0: #buy
                        if p[4]<=row[5]:
                            need = '%0.2f'%(row[4]*row[5]*1.0003)
                            sqls.append(("update ikmom_order_v set status=1 where seqnum=%s",(row[0],)))
                            have = self._exesqlone("select count(*) from ikmom_project_hold_v where pid=%s and code=%s",(row[1],row[3]))
                            if (have[0]==0):
                                sqls.append(("insert into ikmom_project_hold_v(pid,code,amount,freeze) values(%s,%s,0,%s)",(row[1],row[3],row[4])))
                            else:
                                sqls.append(("update ikmom_project_hold_v set freeze=freeze+%s where pid=%s and code=%s",(row[4],row[1],row[3])))
                            sqls.append(("update ikmom_invest_account_v set freeze=freeze-%s where pid=%s",(need,row[1])))
                            self._task(sqls)
                    else: #sell
                        if p[4]>=row[5]:
                            earn = '%0.2f'%(row[4]*row[5]*(1-0.0013))
                            sqls.append(("update ikmom_order_v set status=1 where seqnum=%s",(row[0],)))
                            amt = self._exesqlone('select amount from ikmom_project_hold_v where pid=%s and code=%s',(row[1],row[3]))
                            sqls.append(("update ikmom_project_hold_v set freeze=freeze-%s where pid=%s and code=%s",(row[4],row[1],row[3])))
                            sqls.append(("update ikmom_invest_account_v set cash=cash+%s where pid=%s",(earn,row[1])))
                            self._task(sqls)
            elif wd != 6 and wd != 7 and now.hour==17 and now.minute==0 and now.second<=1:
                self._reconn()
                self.dailytask()
                self.assignproject_v()
                time.sleep(1)
            time.sleep(1)
        g_logger.info('ikmom trade stop....')

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-d', '--daily', action='store_true', dest='daily',default=False, help='daily update')
    parser.add_option('-a', '--assign', action='store_true', dest='assign',default=False, help='assign project')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    im = ikmom()
    if ops.daily:
        im.dailytask()
    elif ops.assign:
        im.assignproject_v()
    else:
        im.run()


