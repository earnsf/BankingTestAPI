-- MySQL dump 10.13  Distrib 5.5.37, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: earn_test
-- ------------------------------------------------------
-- Server version	5.5.37-0ubuntu0.14.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `accounts` (
  `accountId` bigint(20) NOT NULL AUTO_INCREMENT,
  `status` text,
  `accountNumber` varchar(128) DEFAULT NULL,
  `accountNumberReal` text,
  `accountNickname` text,
  `displayPosition` int(11) DEFAULT NULL,
  `institutionId` int(11) NOT NULL,
  `description` text,
  `registeredUserName` text,
  `balanceAmount` decimal(20,2) DEFAULT NULL,
  `balanceDate` datetime DEFAULT NULL,
  `balancePreviousAmount` decimal(20,2) DEFAULT NULL,
  `lastTxnDate` datetime DEFAULT NULL,
  `aggrSuccessDate` datetime DEFAULT NULL,
  `aggrAttemptDate` datetime DEFAULT NULL,
  `aggrStatusCode` text,
  `currencyCode` varchar(3) DEFAULT NULL,
  `bankId` text,
  `institutionLoginId` bigint(20) NOT NULL,
  `bankingAccountType` enum('CHECKING','SAVINGS','MONEYMRKT','RECURRINGDEPOSIT','CD','CASHMANAGEMENT','OVERDRAFT') DEFAULT NULL,
  `postedDate` datetime DEFAULT NULL,
  `availableBalanceAmount` decimal(20,2) DEFAULT NULL,
  `interestType` text,
  `originationDate` datetime DEFAULT NULL,
  `openDate` datetime DEFAULT NULL,
  `periodInterestRate` decimal(20,2) DEFAULT NULL,
  `periodDepositAmount` decimal(20,2) DEFAULT NULL,
  `periodInterestAmount` decimal(20,2) DEFAULT NULL,
  `interestAmountYtd` decimal(20,2) DEFAULT NULL,
  `interestPriorAmountYtd` decimal(20,2) DEFAULT NULL,
  `maturityDate` datetime DEFAULT NULL,
  `maturityAmount` decimal(20,2) DEFAULT NULL,
  PRIMARY KEY (`accountId`),
  UNIQUE KEY `accountId` (`accountId`,`institutionId`),
  UNIQUE KEY `accountNumber` (`accountNumber`,`institutionLoginId`),
  KEY `institutionLoginId` (`institutionLoginId`),
  KEY `institutionId` (`institutionId`),
  CONSTRAINT `accounts_ibfk_4` FOREIGN KEY (`institutionId`) REFERENCES `institutions` (`institutionId`),
  CONSTRAINT `accounts_ibfk_2` FOREIGN KEY (`institutionLoginId`) REFERENCES `logins` (`loginId`)
) ENGINE=InnoDB AUTO_INCREMENT=113 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `addresses`
--

DROP TABLE IF EXISTS `addresses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `addresses` (
  `institutionId` int(11) NOT NULL,
  `address1` text,
  `address2` text,
  `address3` text,
  `city` text,
  `state` text,
  `postalCode` int(11) DEFAULT NULL,
  `country` text,
  PRIMARY KEY (`institutionId`),
  CONSTRAINT `addresses_ibfk_1` FOREIGN KEY (`institutionId`) REFERENCES `institutions` (`institutionId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `customer_accounts`
--

DROP TABLE IF EXISTS `customer_accounts`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `customer_accounts` (
  `customerId` int(11) NOT NULL DEFAULT '0',
  `accountId` bigint(20) NOT NULL DEFAULT '0',
  PRIMARY KEY (`customerId`,`accountId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `inst_keys`
--

DROP TABLE IF EXISTS `inst_keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inst_keys` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `institutionId` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `val` text,
  `status` text,
  `valueLengthMin` int(11) DEFAULT NULL,
  `valueLengthMax` int(11) DEFAULT NULL,
  `displayFlag` tinyint(1) DEFAULT '1',
  `displayOrder` int(11) DEFAULT '5',
  `mask` tinyint(1) DEFAULT NULL,
  `instructions` text,
  `description` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `institutionId` (`institutionId`,`name`),
  UNIQUE KEY `id_order` (`institutionId`,`displayOrder`),
  CONSTRAINT `inst_keys_ibfk_1` FOREIGN KEY (`institutionId`) REFERENCES `institutions` (`institutionId`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `institutions`
--

DROP TABLE IF EXISTS `institutions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `institutions` (
  `institutionId` int(11) NOT NULL AUTO_INCREMENT,
  `institutionName` text,
  `homeUrl` text,
  `phoneNumber` int(10) unsigned zerofill DEFAULT NULL,
  `virtual` tinyint(1) DEFAULT '0',
  `status` text,
  `emailAddress` text,
  `specialText` text,
  `currencyCode` varchar(3) DEFAULT NULL,
  PRIMARY KEY (`institutionId`)
) ENGINE=InnoDB AUTO_INCREMENT=1001 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `logins`
--

DROP TABLE IF EXISTS `logins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `logins` (
  `institutionId` int(11) DEFAULT NULL,
  `loginId` bigint(20) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`loginId`)
) ENGINE=InnoDB AUTO_INCREMENT=202 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `transactions`
--

DROP TABLE IF EXISTS `transactions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `transactions` (
  `accountId` bigint(20) NOT NULL,
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `currencyType` varchar(3) DEFAULT NULL,
  `institutionTransactionId` varchar(128) DEFAULT NULL,
  `correctInstitutionTransactionId` varchar(128) DEFAULT NULL,
  `correctAction` enum('Replace','Delete') DEFAULT NULL,
  `serverTransactionId` varchar(128) DEFAULT NULL,
  `checkNumber` varchar(128) DEFAULT NULL,
  `refNumber` varchar(128) DEFAULT NULL,
  `confirmationNumber` varchar(128) DEFAULT NULL,
  `payeeId` varchar(128) DEFAULT NULL,
  `payeeName` varchar(128) DEFAULT NULL,
  `extendedPayeeName` varchar(128) DEFAULT NULL,
  `memo` text,
  `type` varchar(128) DEFAULT NULL,
  `valueType` varchar(128) DEFAULT NULL,
  `currencyRate` decimal(20,2) DEFAULT NULL,
  `originalCurrency` tinyint(1) DEFAULT NULL,
  `postedDate` datetime NOT NULL,
  `userDate` datetime DEFAULT NULL,
  `availableDate` datetime DEFAULT NULL,
  `amount` decimal(20,2) DEFAULT NULL,
  `runningBalanceAmount` decimal(20,2) DEFAULT NULL,
  `pending` tinyint(1) DEFAULT NULL,
  `categorization` text,
  `normalizedPayeeName` varchar(128) DEFAULT NULL,
  `merchant` varchar(128) DEFAULT NULL,
  `sic` varchar(128) DEFAULT NULL,
  `source` enum('AGGR','OFX','CAT') DEFAULT NULL,
  `categoryName` varchar(128) DEFAULT NULL,
  `contextType` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `accountId` (`accountId`),
  CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`accountId`) REFERENCES `accounts` (`accountId`)
) ENGINE=InnoDB AUTO_INCREMENT=401407840027 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_credentials`
--

DROP TABLE IF EXISTS `user_credentials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_credentials` (
  `institutionId` int(11) NOT NULL,
  `institutionLoginId` bigint(20) NOT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(128) NOT NULL,
  `value` text NOT NULL,
  PRIMARY KEY (`institutionLoginId`,`institutionId`,`id`),
  KEY `id` (`id`),
  KEY `institutionId` (`institutionId`),
  CONSTRAINT `user_credentials_ibfk_1` FOREIGN KEY (`institutionId`) REFERENCES `institutions` (`institutionId`)
) ENGINE=InnoDB AUTO_INCREMENT=48 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2014-11-06 15:38:55
