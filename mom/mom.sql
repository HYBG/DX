CREATE TABLE `hy`.`iknow_keys` (
  `keyword` VARCHAR(20) NOT NULL,
  `callback` VARCHAR(20) NOT NULL COMMENT '回调函数',
  PRIMARY KEY (`keyword`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `hy`.`iknow_synonym` (
  `name` VARCHAR(20) NOT NULL,
  `value` VARCHAR(20) NOT NULL,
  PRIMARY KEY (`name`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

/*全局配置,休市日期信息也记录在该表*/
CREATE TABLE `hy`.`iknow_global` (
  `name` VARCHAR(20) NOT NULL,
  `value` VARCHAR(40) NOT NULL,
  PRIMARY KEY (`name`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_name` (
  `code` varchar(6) NOT NULL,
  `name` varchar(20) NOT NULL,
  `bdcode` varchar(6) NOT NULL,
  `bdname` varchar(20) NOT NULL,
  PRIMARY KEY (`code`),
  INDEX `bd` (`bdcode` ASC))
ENGINE=InnoDB 
DEFAULT CHARACTER SET=utf8;

CREATE TABLE `iknow_user` (
  `userid` varchar(40) NOT NULL COMMENT '用户ID全局唯一',
  `nickname` varchar(20) COMMENT '用户昵称',
  `rdate` varchar(10) NOT NULL COMMENT '开户日期',
  `role` int(1) NOT NULL  DEFAULT '100' COMMENT '角色0:root,100:普通注册用户,1-99为保留值',
  `money` double NOT NULL DEFAULT '0' COMMENT '余额',
  PRIMARY KEY (`userid`),
  INDEX `nm` (`nickname` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_account_hold_v` (
  `pid` VARCHAR(32) NOT NULL,
  `ppid` VARCHAR(32) COMMENT '父项目ID,为空表示该项目为根项目',
  `code` VARCHAR(6) NOT NULL COMMENT '0为现金代码,其他表示股票代码',
  `amount` DOUBLE NOT NULL COMMENT '持有数量',
  `freeze` DOUBLE NOT NULL COMMENT '冻结数量',
  `price` DOUBLE NOT NULL COMMENT '当前价格,非实时价格,估算持仓价值用,后台程序每N分钟更新一次',
  `hvalue` DOUBLE NOT NULL COMMENT 'amount*price,与price同时更新',
  PRIMARY KEY (`pid`,`code`),
  INDEX `pd` (`pid` ASC),
  INDEX `ppd` (`ppid` ASC),
  INDEX `cd` (`code` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_project_info_v` (
  `pid` VARCHAR(32) NOT NULL,
  `userid` VARCHAR(40) NOT NULL COMMENT '绑定账户ID',
  `baseline` DOUBLE NOT NULL DEFAULT '200000' COMMENT '基准金额,计提依据的水平线',
  `edate` VARCHAR(10) NOT NULL COMMENT '生效日期',
  `ddate` VARCHAR(10) COMMENT '系统回收日期',
  `cdate` VARCHAR(10) COMMENT '关闭日期',
  `closereason` INT(1) COMMENT '关闭原因0:主动关闭,1:被动关闭(回撤原因),2:到期关闭,3:其他原因被动关闭(比如管理者失联)',
  `status` INT(1) NOT NULL DEFAULT '0' COMMENT '项目状态0:正常,1:关闭',
  `returnrate` DOUBLE NOT NULL DEFAULT '0' COMMENT '收益率,包括子项目',
  `dailyrate` DOUBLE NOT NULL DEFAULT '0' COMMENT '日复合增长率sqrt(1+R,n)-1,R为收益率,n为天数',
  PRIMARY KEY (`pid`),
  INDEX `ud` (`uid` ASC),
  INDEX `uds` (`uid` ASC, `status` ASC),
  INDEX `ppd` (`ppid` ASC))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;

CREATE TABLE `iknow_order_v` (
  `seqid` varchar(32) NOT NULL COMMENT '流水ID',
  `orderid` varchar(32) NOT NULL COMMENT '订单ID',
  `pid` VARCHAR(32) NOT NULL COMMENT '项目ID',
  `timestamp` varchar(24) NOT NULL COMMENT '时间戳',
  `oper` int(1) NOT NULL COMMENT '买卖标记1:买入,2:卖出',
  `typ` int(1) NOT NULL COMMENT '0:市价单,1:限价单',
  `code` varchar(6) NOT NULL COMMENT '股票代码',
  `amount` double NOT NULL COMMENT '股票数量',
  `price` double NOT NULL COMMENT '订单价格',
  `status` int(1) NOT NULL COMMENT '订单状态0:已报,1:已成,2:撤单',
  PRIMARY KEY (`seqid`),
  INDEX `oid` (`orderid` ASC),
  INDEX `pd` (`pid` ASC),
  INDEX `op` (`oper` ASC),
  INDEX `tp` (`typ` ASC),
  INDEX `st` (`status` ASC))
ENGINE = InnoDB 
DEFAULT CHARACTER SET = utf8;
