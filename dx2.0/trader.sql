CREATE TABLE `trader`.`trader_user` (
  `userid` varchar(32) NOT NULL,
  `cash` double NOT NULL,
  PRIMARY KEY (`userid`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `trader`.`trader_stockset` (
  `date` varchar(10) NOT NULL,
  `code` varchar(6) NOT NULL,
  `name` varchar(20) NOT NULL,
  `pinyin` varchar(30) NOT NULL,
  PRIMARY KEY (`date`,`code`),
  KEY `dt` (`date`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='所有可交易品种库及更新日期';

CREATE TABLE `trader`.`trader_order_put` (
  `orderid` varchar(24) NOT NULL COMMENT '订单ID',
  `userid` varchar(32) NOT NULL COMMENT '用户ID',
  `puttime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `win` double COMMENT '止盈价格',
  `lose` double COMMENT '止损价格',
  `action` int(1)  DEFAULT '0' COMMENT '多空标识0:多单,1:空单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量(手)',
  `putprice` double NOT NULL COMMENT '开仓价格',
  `freeze` double NOT NULL COMMENT '冻结资金',
  `holddays` int(2) NOT NULL DEFAULT '1' COMMENT '持有最多天数,到期自动平仓',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = MyISAM 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_order_cancel` (
  `orderid` varchar(24) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `puttime` VARCHAR(20),
  `canceltime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `win` double COMMENT '止盈价格',
  `lose` double COMMENT '止损价格',
  `action` int(1)  DEFAULT '0' COMMENT '多空标识0:多单,1:空单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量(手)',
  `putprice` double NOT NULL COMMENT '开仓价格',
  `holddays` int(2) NOT NULL DEFAULT '1' COMMENT '持有最多天数,到期自动平仓',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = MyISAM 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_order_open` (
  `orderid` varchar(24) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `puttime` VARCHAR(20),
  `opentime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `action` int(1)  DEFAULT '0' COMMENT '多空标识0:多单,1:空单',
  `win` double COMMENT '止盈价格',
  `lose` double COMMENT '止损价格',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量(手)',
  `openprice` double NOT NULL COMMENT '开仓价格',
  `commission` double NOT NULL COMMENT '手续费',
  `surviving` int(2) NOT NULL DEFAULT '0' COMMENT '持有天数',
  `holddays` int(2) NOT NULL DEFAULT '1' COMMENT '持有最多天数,到期自动平仓',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = MyISAM 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_order_close` (
  `orderid` varchar(24) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `puttime` VARCHAR(20),
  `opentime` VARCHAR(20) NOT NULL,
  `closetime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `action` int(1)  DEFAULT '0' COMMENT '多空标识0:多单,1:空单',
  `win` double COMMENT '止盈价格',
  `lose` double COMMENT '止损价格',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量(手)',
  `openprice` double NOT NULL COMMENT '开仓价格',
  `closeprice` double NOT NULL COMMENT '平仓价格',
  `commission` double NOT NULL COMMENT '手续费',
  `earn` double NOT NULL COMMENT '净收益',
  `rate` double NOT NULL COMMENT '净收益比率',
  `surviving` int(2) NOT NULL DEFAULT '0' COMMENT '持有天数',
  `holddays` int(2) NOT NULL DEFAULT '1' COMMENT '持有最多天数,到期自动平仓',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = MyISAM 
DEFAULT CHARACTER SET = utf8;