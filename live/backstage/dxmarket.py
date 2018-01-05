import os
import sys
import logging
import string
import re
import urllib2
import datetime
from optparse import OptionParser
from logging.handlers import RotatingFileHandler
import web
import json

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')

sys.path.append(os.path.join(g_home,'lib'))
from dxdb import dxdblib

logd = os.path.join(g_home, 'log')
if not os.path.isdir(logd):
    os.makedirs(logd, 0777)
g_logger = logging.getLogger('market')
formatstr = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logfile = os.path.join(logd,'market.log')
rh = RotatingFileHandler(logfile, maxBytes=100*1024*1024,backupCount=50)
rh.setLevel(logging.INFO)
fmter = logging.Formatter(formatstr)
rh.setFormatter(fmter)
g_logger.addHandler(rh)
g_logger.setLevel(logging.INFO)

class dxmarket:
    def __init__(self):
        self._db = dxdblib('localhost','root','123456','dx','utf8')

    def __del__(self):
        pass

    def GET(self):
        try:
            fromip = self._db.exesqlone('select count(*) from dx_global where name=%s and value=%s',(web.ctx.ip,'1'))
            if fromip[0]==0:
                return json.dumps({'retcode':'10003','retmessage':'ip reject'})
            full = web.ctx.fullpath
            items = full[1:].split('&')
            if len(items)>0:
                md = {}
                url = 'http://hq.sinajs.cn/list=%s'%(items[0])
                for its in items[1:]:
                    url = '%s,%s'%(url,its)
                try:
                    lines = urllib2.urlopen(url).readlines()
                    for line in lines:
                        info = line.split(' ')[1].split('=')
                        name = info[0][len('hq_str_'):]
                        vals = info[1].split(',')
                        md[name]=vals[1:-1]
                except Exception, e:
                    g_logger.warning('get current price codes[%s] exception[%s]'%(full,e))
                    md = {'retcode':'10004','retmessage':'system exception[%s]'%e}
                return json.dumps(md)
            else:
                return json.dumps({'retcode':'10005','retmessage':'url error'})
        except Exception,e:
            g_logger.warning('system exception[%s]'%e)
            return json.dumps({'retcode':'10006','retmessage':'system exception[%s]'%e})

if __name__ == "__main__":
    urls = (
    '/.*', 'dxmarket')

    app = web.application(urls, globals())
    app.run()


