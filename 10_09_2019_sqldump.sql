-- MySQL dump 10.17  Distrib 10.3.17-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: 127.0.0.1    Database: arbitrage
-- ------------------------------------------------------
-- Server version	10.3.17-MariaDB-1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bot_markets`
--

DROP TABLE IF EXISTS `bot_markets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bot_markets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bot_id` int(11) NOT NULL,
  `exchange_id` int(11) NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT 0,
  `refid` varchar(255) COLLATE utf8_bin NOT NULL,
  `symbol` varchar(255) COLLATE utf8_bin NOT NULL,
  `max_size` varchar(255) COLLATE utf8_bin NOT NULL DEFAULT '0.00020',
  `min_profit` varchar(255) COLLATE utf8_bin NOT NULL DEFAULT '0.80',
  `deposit_address` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bot_id` (`bot_id`),
  KEY `exchange_id` (`exchange_id`),
  CONSTRAINT `bot_markets_bots_id_fk` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `bot_markets_exchanges_id_fk` FOREIGN KEY (`exchange_id`) REFERENCES `exchanges` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bot_markets`
--

LOCK TABLES `bot_markets` WRITE;
/*!40000 ALTER TABLE `bot_markets` DISABLE KEYS */;
INSERT INTO `bot_markets` VALUES (1,1,1,1,'dogebtc','doge','0.00012','0.9',NULL),(2,1,2,1,'DOGE-BTC','DOGE','0.00012','0.9',NULL),(3,2,1,1,'zocbtc','zoc','0.0001','0.9',NULL),(4,3,1,1,'ltcbtc','ltc','0.00012','0.9',NULL),(5,4,1,1,'ethbtc','eth','0.00012','0.9',NULL),(6,2,2,1,'ZOC-BTC','ZOC','0.0001','0.9',NULL),(7,3,2,1,'LTC-BTC','LTC','0.00012','0.9',NULL),(8,4,2,1,'ETH-BTC','ETH','0.00012','0.9',NULL),(9,5,1,1,'rvnbtc','rvn','0.0001','0.9',NULL),(10,5,3,1,'RVNBTC','RVN','0.0001','0.9',NULL),(11,1,3,1,'DOGEBTC','DOGE','0.00012','0.9',NULL),(12,3,3,1,'LTCBTC','LTC','0.00012','0.9',NULL),(13,4,3,1,'ETHBTC','ETH','0.00012','0.9',NULL),(17,6,2,1,'SATC-BTC','SATC','0.0001','0.9',NULL),(18,6,1,1,'satcbtc','satc','0.0001','0.9',NULL),(19,7,2,1,'XVG-BTC','XVG','0.0001','0.9',NULL),(20,7,1,1,'xvgbtc','xvg','0.0001','0.9','asdadasdasdasdasd'),(21,7,3,1,'XVGBTC','XVG','0.00012','0.9',NULL),(22,8,1,1,'npxsbtc','npxs','0.00022','0.9',NULL),(23,8,3,1,'NPXSBTC','NPXS','0.00022','0.9',NULL),(24,9,1,1,'pivxbtc','pivx','0.00012','0.9',NULL),(25,9,2,1,'PIVX-BTC','PIVX','0.00012','0.9',NULL),(26,9,3,0,'PIVXBTC','PIVX','0.00012','0.9',NULL),(27,10,1,1,'wavesbtc','waves','0.00012','0.9',NULL),(28,10,2,1,'WAVES-BTC','WAVES','0.00012','0.9',NULL),(29,10,3,1,'WAVESBTC','WAVES','0.00012','0.9',NULL);
/*!40000 ALTER TABLE `bot_markets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bots`
--

DROP TABLE IF EXISTS `bots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `bots` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_bin NOT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `bots_id_index` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bots`
--

LOCK TABLES `bots` WRITE;
/*!40000 ALTER TABLE `bots` DISABLE KEYS */;
INSERT INTO `bots` VALUES (1,'DOGE/BTC',1),(2,'ZOC/BTC',0),(3,'LTC/BTC',1),(4,'ETH/BTC',1),(5,'RVN/BTC',0),(6,'SATC/BTC',0),(7,'XVG/BTC',1),(8,'NPXS/BTC',1),(9,'PIVX/BTC',1),(10,'WAVES/BTC',1);
/*!40000 ALTER TABLE `bots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `api_client`
--

DROP TABLE IF EXISTS `exchanges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exchanges` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` text NOT NULL,
  `enabled` int(11) DEFAULT NULL,
  `key` text DEFAULT NULL,
  `secret` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `exchanges_id_index` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `api_client`
--

LOCK TABLES `exchanges` WRITE;
/*!40000 ALTER TABLE `exchanges` DISABLE KEYS */;
INSERT INTO `exchanges` VALUES (1,'Graviex',1,'gx4D8JHsxTdXQGd2kdOVVxxc1GOTPC8YAK1Bbwa3','7KNZMzxUNDcfSPxOJWJZMlW98VeeXaw0EcJPSHQP'),(2,'Crex24',1,'ea33efcd-71cc-4445-8ca5-61f85bb0d04b','6SiG6QG2xmd8YD/+Jj8MfQysCldp8U7uS9CmZNIoTqY+cBXvMgbb6D108MtOuLabONpTBdb9rbhkBJ840srMvA=='),(3,'Binance',1,'IVQudCyo6HgA9n3KOY2Qac7DZQ5gM49T6tntYzeqhmy0HVccH3hvK6HWm0ptPJzv','oqQr4q5sU6f3ZnIX0F0awCUfBZX8MfuqMHL1csbk0Vxp8SAXzAvMPlw0qnUndbTU');
/*!40000 ALTER TABLE `exchanges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jobs`
--

DROP TABLE IF EXISTS `jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `jobs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bot_id` int(11) NOT NULL,
  `buy_bot_market_id` int(11) NOT NULL,
  `sell_bot_market_id` int(11) NOT NULL,
  `buy_order_id` int(11) NOT NULL,
  `sell_order_id` int(11) NOT NULL,
  `profit` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `profit_percent` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `created` datetime NOT NULL,
  `closed` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bot_id` (`bot_id`),
  KEY `buy_bot_market_id` (`buy_bot_market_id`),
  KEY `sell_bot_market_id` (`sell_bot_market_id`),
  KEY `buy_order_id` (`buy_order_id`),
  KEY `sell_order_id` (`sell_order_id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobs`
--

LOCK TABLES `jobs` WRITE;
/*!40000 ALTER TABLE `jobs` DISABLE KEYS */;
INSERT INTO `jobs` VALUES (1,1,2,3,4,5,'6','7','1970-01-01 00:00:00','2019-08-06 22:12:04'),(4,22,0,0,333,333,'44','4','2019-08-06 22:18:19','2019-08-06 22:18:21'),(5,333,33233,1113233,0,0,'44','4','2019-08-06 22:18:19',NULL),(16,311111,2343,2424,0,0,'1','20','2019-08-07 01:13:57','2019-08-07 01:13:57'),(17,311111,2343,2424,0,0,'1','20','2019-08-07 01:14:58','2019-08-07 01:14:58');
/*!40000 ALTER TABLE `jobs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `orders` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `bot_id` int(11) NOT NULL,
  `order_id` int(11) DEFAULT NULL,
  `refid` varchar(255) COLLATE utf8_bin NOT NULL,
  `status` varchar(255) COLLATE utf8_bin NOT NULL,
  `side` varchar(255) COLLATE utf8_bin NOT NULL,
  `price` varchar(255) COLLATE utf8_bin NOT NULL,
  `volume` varchar(255) COLLATE utf8_bin NOT NULL,
  `executed_volume` varchar(255) COLLATE utf8_bin NOT NULL,
  `created` datetime NOT NULL DEFAULT curtime(),
  `modified` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bot_market_id` (`bot_id`),
  CONSTRAINT `orders_bot_markets_bot_id_fk` FOREIGN KEY (`bot_id`) REFERENCES `bot_markets` (`bot_id`)
) ENGINE=InnoDB AUTO_INCREMENT=33339 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-09-10 13:44:16
