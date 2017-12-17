#!/usr/bin/python

import os
import sys
import logging
import string
import re
import datetime
import time
import math
import MySQLdb
import json
import urllib2
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
reload(sys)
sys.setdefaultencoding('utf8')


g_logger = logging.getLogger('bgloop')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = '/var/www/html/bg/log/bgloop.log'
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class bgloop:
    def __init__(self):
        self._conn = MySQLdb.connect(host='localhost',user='root',passwd='123456',db='bg',charset='utf8') 
        self._cursor = self._conn.cursor()

    def _exesqlone(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchone()

    def _exesqlbatch(self,sql,para):
        n = self._cursor.execute(sql,para)
        return self._cursor.fetchall()
        
    def _task(self,sqls):
        for sql in sqls:
            try:
                n = self._cursor.execute(sql[0],sql[1])
                g_logger.info('execute sql[%s],para[%s] successfully'%(sql[0],str(sql[1])))
            except Exception,e:
                g_logger.error('execute sql[%s],para[%s] failed[%s]'%(sql[0],str(sql[1]),e))
                self._conn.rollback()
                return False
        self._conn.commit()
        return True

    def run(self):
        while 1:
            tm = time.time()
            sqls = []
            ids = self._exesqlbatch("select extid,voteid from bg_user where status!=1 and expire!=0 and expire<=%s",(tm,))
            for id in ids:
                sqls.append(("update bg_user set roomid='',voteid='',seatid='',role='',status=1,expire=0 where extid=%s",(id[0],)))
                sqls.append(("delete from bg_vote where voteid=%s",(id[1],)))

            sqls = list(set(sqls))
            rids = self._exesqlbatch("select roomid from bg_room where expire<=%s and expire!=0",(tm,))
            for rid in rids:
                sqls.append(("update bg_room set status=0,expire=0 where roomid=%s",(rid[0],)))
                sqls.append(("delete from bg_process where roomid=%s",(rid[0],)))
                sqls.append(("delete from bg_game where roomid=%s",(rid[0],)))
                sqls.append(("delete from bg_votedetail where roomid=%s",(rid[0],)))
                sqls.append(("delete from bg_global where roomid=%s",(rid[0],)))
            self._task(sqls)
            time.sleep(2)
    

if __name__ == "__main__":
    bgloop().run()





