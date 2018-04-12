CREATE TABLE `iknow_data` (
  `code` varchar(6) NOT NULL  COMMENT '股票代码',
  `date` varchar(10) NOT NULL COMMENT '数据日期',
  `open` double NOT NULL COMMENT '开盘价',
  `high` double NOT NULL COMMENT '最高价',
  `low` double NOT NULL COMMENT '最低价',
  `close` double NOT NULL COMMENT '收盘价',
  `volh` double NOT NULL COMMENT '成交量(手)',
  `volwy` double NOT NULL COMMENT '成交金额',
  PRIMARY KEY (`code`,`date`),
  KEY `v` (`volwy`),
  KEY `cd` (`code`),
  KEY `dt` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `iknow_attr` (
  `code` varchar(6) NOT NULL,
  `date` varchar(10) NOT NULL,
  `zdf` double NOT NULL  COMMENT '涨跌幅(-0.101,0.101)',
  `zf` double NOT NULL  COMMENT '振幅',
  `scoreo` double NOT NULL  COMMENT '开盘得分(0,1)',
  `scorec` double NOT NULL  COMMENT '收盘得分(0,1)',
  `ranking` int(4) NOT NULL  COMMENT '成交量排名',
  PRIMARY KEY (`code`,`date`),
  KEY `cd` (`code`),
  KEY `dt` (`date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `iknow_base` (
  `code` varchar(6) NOT NULL,
  `date` varchar(10) NOT NULL,
  `hb` int(1) NOT NULL COMMENT '= is not break',
  `lb` int(1) NOT NULL,
  `k` int(1) NOT NULL COMMENT '= is yin',
  `v1` int(1) NOT NULL COMMENT '>0 is 1,others is 0',
  `v2` int(1) NOT NULL,
  `zdfz` double NOT NULL,
  `zfz` double NOT NULL,
  `scoreoz` double NOT NULL,
  `scorecz` double NOT NULL,
  `openf` double NOT NULL,
  `highf` double NOT NULL,
  `lowf` double NOT NULL,
  `closef` double NOT NULL,
  `useful` int(1) NOT NULL,
  PRIMARY KEY (`code`,`date`),
  KEY `tp` (`hb`,`k`,`lb`,`v1`,`v2`),
  KEY `cd` (`code`),
  KEY `dt` (`date`),
  KEY `tpd` (`date`,`hb`,`lb`,`k`,`v1`,`v2`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `iknow_base2` (
  `code` varchar(6) NOT NULL,
  `date` varchar(10) NOT NULL,
  `hb` int(1) NOT NULL COMMENT '= is not break',
  `lb` int(1) NOT NULL,
  `k` int(1) NOT NULL COMMENT '= is yin',
  `v1` int(1) NOT NULL COMMENT '>0 is 1,others is 0',
  `v2` int(1) NOT NULL,
  `zdff` int(1) NOT NULL COMMENT '涨跌幅标识,涨跌幅针对120日均线标准化后的值以(-0.43,0.43)为界，取值0,1,2',
  `zff` int(1) NOT NULL COMMENT '振幅标识,振幅针对120日均线标准化后的值以(-0.43,0.43)为界，取值0,1,2',
  `scoreof` int(1) NOT NULL COMMENT '开盘分标识,开盘分针对120日均线标准化后的值以(-0.43,0.43)为界，取值0,1,2',
  `scorecf` int(1) NOT NULL COMMENT '收盘分标识,收盘分针对120日均线标准化后的值以(-0.43,0.43)为界，取值0,1,2',
  `openf` double NOT NULL,
  `highf` double NOT NULL,
  `lowf` double NOT NULL,
  `closef` double NOT NULL,
  `useful` int(1) NOT NULL,
  `nextdate` varchar(10) COMMENT '',
  `hp` int(1) COMMENT '',
  `lp` int(1) COMMENT '',
  `status` int(1) NOT NULL COMMENT '0:基础数据写入,1:结果数据写入',
  PRIMARY KEY (`code`,`date`),
  KEY `tp` (`hb`,`k`,`lb`,`v1`,`v2`,`zdff`,`zff`,`scoreof`,`scorecf`),
  KEY `cd` (`code`),
  KEY `dt` (`date`),
  KEY `tpd` (`date`,`hb`,`lb`,`k`,`v1`,`v2`,`zdff`,`zff`,`scoreof`,`scorecf`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE `iknow_tell2` (
  `fv` varchar(9) NOT NULL,
  `hbp` double NOT NULL,
  `lbp` double NOT NULL,
  `kp` double NOT NULL,
  `openev` double NOT NULL,
  `highev` double NOT NULL,
  `lowev` double NOT NULL,
  `closeev` double NOT NULL,
  `hpp` double NOT NULL,
  `lpp` double NOT NULL,
  PRIMARY KEY (`fv`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;










