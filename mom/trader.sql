CREATE DATABASE trader;
CREATE TABLE `trader`.`trader_global` (
  `name` varchar(32) NOT NULL COMMENT '变量名称',
  `value` varchar(32) NOT NULL COMMENT '变量值',
  PRIMARY KEY (`name`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_code` (
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `name` varchar(20) NOT NULL COMMENT '股票名称',
  `boardcode` varchar(6) NOT NULL COMMENT '板块代码',
  `boardname` varchar(20) NOT NULL COMMENT '板块名称',
  `status` int(1) NOT NULL COMMENT '状态0:初始化,1:正常,2:停牌,3:注销',
  PRIMARY KEY (`code`),
  INDEX `st` (`status` ASC),
  INDEX `bd` (`boardcode` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_user` (
  `userid` varchar(32) NOT NULL COMMENT '用户ID全局唯一',
  `rdate` varchar(10) NOT NULL COMMENT '开户日期',
  `cash` double NOT NULL DEFAULT '0',
  `value` double NOT NULL DEFAULT '0',
  PRIMARY KEY (`userid`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_account_record` (
  `seqid` VARCHAR(32) NOT NULL,
  `userid` VARCHAR(32) NOT NULL,
  `date` varchar(10) NOT NULL,
  `time` varchar(10) NOT NULL,
  `amount` double NOT NULL,
  PRIMARY KEY (`userid`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_order_put` (
  `orderid` varchar(32) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `putdate` varchar(10) NOT NULL COMMENT '挂单日期',
  `puttime` varchar(10) NOT NULL COMMENT '挂单时间',
  `otype` int(1) COMMENT '订单方向1:多单,-1:空单',
  `win` double COMMENT '止盈价格',
  `lose` double COMMENT '止损价格',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `putprice` double NOT NULL COMMENT '开仓价格',
  `freeze` double NOT NULL COMMENT '冻结资金',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_order_cancel` (
  `orderid` varchar(32) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `putdate` varchar(10) NOT NULL COMMENT '挂单日期',
  `puttime` varchar(10) NOT NULL COMMENT '挂单时间',
  `canceldate` varchar(10) NOT NULL COMMENT '撤单日期',
  `canceltime` varchar(10) NOT NULL COMMENT '撤单时间',
  `tag` int(1)  DEFAULT '0' COMMENT '撤单标识0:主动撤单,1:系统撤单',
  `otype` int(1) COMMENT '订单方向1:多单,-1:空单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `putprice` double NOT NULL COMMENT '开仓价格',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_order_open` (
  `orderid` varchar(32) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `putdate` varchar(10) NOT NULL COMMENT '挂单日期',
  `puttime` varchar(10) NOT NULL COMMENT '挂单时间',
  `opendate` varchar(10) NOT NULL COMMENT '开仓日期',
  `opentime` varchar(10) NOT NULL COMMENT '开仓时间',
  `otype` int(1) COMMENT '订单方向1:多单,-1:空单',
  `tag` int(1) DEFAULT '0' COMMENT '止盈止损生效标识0:未生效,1:生效',
  `win` double COMMENT '止盈价格',
  `lose` double COMMENT '止损价格',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `openprice` double NOT NULL COMMENT '开仓价格',
  `benefit` double NOT NULL DEFAULT '0' COMMENT '浮动盈亏,未计算手续费',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC),
  INDEX `bf` (`benefit` ASC))
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `trader`.`trader_order_close` (
  `orderid` varchar(32) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `opendate` varchar(10) NOT NULL COMMENT '开仓日期',
  `opentime` varchar(10) NOT NULL COMMENT '开仓时间',
  `closedate` varchar(10) NOT NULL COMMENT '平仓日期',
  `closetime` varchar(10) NOT NULL COMMENT '平仓时间',
  `otype` int(1) COMMENT '订单方向1:多单,-1:空单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `openprice` double NOT NULL COMMENT '开仓价格',
  `closeprice` double NOT NULL COMMENT '平仓价格',
  `commission` double NOT NULL COMMENT '手续费',
  `earn` double NOT NULL COMMENT '净收益',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;










