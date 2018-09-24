CREATE TABLE `trader`.`trader_order_cancel` (
  `orderid` varchar(24) NOT NULL COMMENT '订单ID',
  `userid` varchar(32) NOT NULL COMMENT '用户ID',
  `puttime` varchar(20) DEFAULT NULL,
  `canceltime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `action` int(1) DEFAULT '0' COMMENT '多空标识0:买入,1:卖出',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量(手)',
  `putprice` double NOT NULL COMMENT '开仓价格',
  PRIMARY KEY (`orderid`),
  KEY `ud` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `trader_order_close` (
  `orderid` varchar(24) NOT NULL COMMENT '订单ID',
  `userid` varchar(32) NOT NULL COMMENT '用户ID',
  `puttime` varchar(20) DEFAULT NULL,
  `opentime` varchar(20) NOT NULL,
  `closetime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `action` int(1) DEFAULT '0' COMMENT '多空标识0:买入,1:卖出',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量(手)',
  `openprice` double NOT NULL COMMENT '开仓价格',
  `closeprice` double NOT NULL COMMENT '平仓价格',
  `commission` double NOT NULL COMMENT '手续费',
  PRIMARY KEY (`orderid`),
  KEY `ud` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `trader_order_open` (
  `orderid` varchar(24) NOT NULL COMMENT '订单ID',
  `userid` varchar(32) NOT NULL COMMENT '用户ID',
  `puttime` varchar(20) DEFAULT NULL,
  `opentime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `action` int(1) DEFAULT '0' COMMENT '多空标识0:多单,1:空单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量(手)',
  `openprice` double NOT NULL COMMENT '开仓价格',
  `commission` double NOT NULL COMMENT '手续费',
  PRIMARY KEY (`orderid`),
  KEY `ud` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `trader_order_put` (
  `orderid` varchar(24) NOT NULL COMMENT '订单ID',
  `userid` varchar(32) NOT NULL COMMENT '用户ID',
  `puttime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `action` int(1) DEFAULT '0' COMMENT '多空标识0:多单,1:空单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量(手)',
  `putprice` double NOT NULL COMMENT '开仓价格',
  `freeze` double NOT NULL COMMENT '冻结资金',
  PRIMARY KEY (`orderid`),
  KEY `ud` (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;



