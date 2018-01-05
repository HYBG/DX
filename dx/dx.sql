CREATE TABLE `dx`.`dx_global` (
  `name` varchar(32) NOT NULL COMMENT '变量名称',
  `value` varchar(32) NOT NULL COMMENT '变量值',
  PRIMARY KEY (`name`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `dx`.`dx_code` (
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `name` varchar(20) NOT NULL COMMENT '股票名称',
  `status` int(1) NOT NULL COMMENT '状态0:初始化,1:正常,2:停牌,3:注销',
  PRIMARY KEY (`code`),
  INDEX `st` (`status` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `dx`.`dx_user` (
  `userid` varchar(32) NOT NULL COMMENT '用户ID全局唯一',
  `created` TIMESTAMP default now() COMMENT '开户时间',
  `cash` double NOT NULL DEFAULT '0',
  `value` double NOT NULL DEFAULT '0',
  PRIMARY KEY (`userid`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `dx`.`dx_account_record` (
  `seqid` VARCHAR(20) NOT NULL,
  `userid` VARCHAR(32) NOT NULL,
  `created` TIMESTAMP default now(),
  `amount` double NOT NULL,
  PRIMARY KEY (`seqid`),
  INDEX `ud` (`userid` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `dx`.`dx_order_put` (
  `orderid` varchar(20) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `created` TIMESTAMP default now(),
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

CREATE TABLE `dx`.`dx_order_cancel` (
  `orderid` varchar(20) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `puttime` TIMESTAMP NOT NULL,
  `created` TIMESTAMP default now(),
  `tag` int(1)  DEFAULT '0' COMMENT '撤单标识0:主动撤单,1:系统撤单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `putprice` double NOT NULL COMMENT '开仓价格',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `dx`.`dx_order_open` (
  `orderid` varchar(20) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `canceltime` TIMESTAMP,
  `created` TIMESTAMP default now(),
  `win` double COMMENT '止盈价格',
  `lose` double COMMENT '止损价格',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `openprice` double NOT NULL COMMENT '开仓价格',
  `benefit` double NOT NULL DEFAULT '0' COMMENT '浮动盈亏,未计算手续费',
  `surviving` int(4) NOT NULL DEFAULT '0' COMMENT '持有天数',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC),
  INDEX `bf` (`benefit` ASC))
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `dx`.`dx_order_close` (
  `orderid` varchar(20) NOT NULL COMMENT '订单ID',
  `userid` VARCHAR(32) NOT NULL COMMENT '用户ID',
  `opentime` TIMESTAMP NOT NULL,
  `created` TIMESTAMP default now(),
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `openamount` double NOT NULL COMMENT '开仓股票数量',
  `openprice` double NOT NULL COMMENT '开仓价格',
  `closeamount` double NOT NULL COMMENT '平仓股票数量',
  `closeprice` double NOT NULL COMMENT '平仓价格',
  `commission` double NOT NULL COMMENT '手续费',
  `earn` double NOT NULL COMMENT '净收益',
  PRIMARY KEY (`orderid`),
  INDEX `ud` (`userid` ASC))
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;










