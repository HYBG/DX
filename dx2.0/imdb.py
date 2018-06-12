#!/usr/bin/python

import os
import sys
import string
import re
import datetime
import time
import commands
from optparse import OptionParser

g_home = os.getenv('IKNOW_HOME','/var/data/iknow')
if not g_home:
    raise Exception('IKNOW_HOME not found!')

if __name__ == "__main__":
    parser  = OptionParser()
    parser.add_option('-d', '--dir', action='store', dest='dir',default=None, help='data dir')
    parser.add_option('-D', '--db', action='store', dest='db',default=None, help='db name')
    parser.add_option('-t', '--table', action='store', dest='table',default=None, help='table name')

    (ops, args) = parser.parse_args()
    if len(args) > 0:
        sys.exit(1)

    if ops.dir and ops.db and ops.table:
        files = os.listdir(ops.dir)
        files.sort()
        for fn in files:
            csvfn = os.path.join(ops.dir,fn.strip())
            sfn = os.path.join(os.path.join(g_home,'tmp'),'%s.sql'%ops.table)
            sql = "load data infile '%s' into table %s fields terminated by ',' optionally enclosed by \'\"\' escaped by \'\"\'  lines terminated by '\\n';"%(csvfn,ops.table)
            f = open(sfn,'w')
            f.write('%s'%sql)
            f.close()
            cmd = 'mysql -u root -p123456 %s < %s'%(ops.db,sfn)
            status,output = commands.getstatusoutput(cmd)
            print('import db[%s] table[%s] file[%s] status[%d] output[%s]...'%(ops.db,ops.table,fn,status,output.strip()))

    
    
    