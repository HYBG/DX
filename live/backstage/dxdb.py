import os
import sys
import logging
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
g_logger = logging.getLogger('dxdb')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'dxdb.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class dxdblib:
    def __init__(self,host,user,passwd,db,charset):
        self._host = host
        self._user = user
        self._passwd = passwd
        self._db = db
        self._charset = charset
        self._conn = MySQLdb.connect(host=self._host,user=self._user,passwd=self._passwd,db=self._db,charset=self._charset)
        self._cursor = self._conn.cursor()

    def __del__(self):
        self._cursor.close()
        self._conn.close()
        
    def set(self,host,user,passwd,db,charset):
        self._host = host
        self._user = user
        self._passwd = passwd
        self._db = db
        self._charset = charset

    def reconn(self):
        self._cursor.close()
        self._conn.close()
        self._conn = MySQLdb.connect(host=self._host,user=self._user,passwd=self._passwd,db=self._db,charset=self._charset)
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




