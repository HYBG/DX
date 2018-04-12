import os
import sys
import datetime
reload(sys)
sys.setdefaultencoding('utf8')

g_offday = ['2018-02-15','2018-02-16','2018-02-19','2018-02-20','2018-02-21','2018-04-05','2018-04-06','2018-04-30','2018-05-01','2018-06-18','2018-09-24','2018-10-01','2018-10-02','2018-10-03','2018-10-04','2018-10-05','2018-10-06']


if __name__ == "__main__":
    
    ofn = '/var/data/iknow/tmp/openday.csv'
    end = datetime.date(2019,1,1)
    today = datetime.date.today()
    mat = []
    while today<end:
        str = '%04d-%02d-%02d'%(today.year,today.month,today.day)
        wd = today.isoweekday()
        if (str not in g_offday) and wd != 6 and wd != 7:
            mat.append(str)
        today = today+datetime.timedelta(days=1)
    f = open(ofn,'w')
    for row in mat:
        f.write('%s\n'%row)
    f.close()
    




