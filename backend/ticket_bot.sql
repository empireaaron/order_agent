/*
 Navicat Premium Dump SQL

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 80018 (8.0.18)
 Source Host           : localhost:3306
 Source Schema         : ticket_bot

 Target Server Type    : MySQL
 Target Server Version : 80018 (8.0.18)
 File Encoding         : 65001

 Date: 08/04/2026 16:33:27
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for agent_status
-- ----------------------------
DROP TABLE IF EXISTS `agent_status`;
CREATE TABLE `agent_status`  (
  `agent_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '客服ID',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'offline' COMMENT '在线状态: online(在线), busy(忙碌), offline(离线)',
  `current_sessions` int(11) NULL DEFAULT 0 COMMENT '当前会话数',
  `max_sessions` int(11) NULL DEFAULT 5 COMMENT '最大并发会话数',
  `total_sessions_today` int(11) NULL DEFAULT 0 COMMENT '今日总会话数',
  `total_messages_today` int(11) NULL DEFAULT 0 COMMENT '今日总消息数',
  `last_heartbeat` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后心跳时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`agent_id`) USING BTREE,
  CONSTRAINT `fk_agent_status_agent` FOREIGN KEY (`agent_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '客服在线状态表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of agent_status
-- ----------------------------
INSERT INTO `agent_status` VALUES ('0912d5f2-acdd-492e-852f-0b915524cafc', 'online', 0, 5, 1, 0, '2026-04-05 11:50:57', '2026-04-08 07:59:55');
INSERT INTO `agent_status` VALUES ('7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'online', 0, 5, 0, 0, '2026-04-05 06:51:47', '2026-04-07 12:56:00');

-- ----------------------------
-- Table structure for api_metrics
-- ----------------------------
DROP TABLE IF EXISTS `api_metrics`;
CREATE TABLE `api_metrics`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '记录ID (UUID)',
  `metric_date` date NOT NULL COMMENT '统计日期',
  `endpoint` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'API 端点路径',
  `method` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'HTTP 方法: GET/POST/PUT/DELETE',
  `request_count` int(11) NOT NULL DEFAULT 0 COMMENT '请求次数',
  `error_count` int(11) NOT NULL DEFAULT 0 COMMENT '错误次数（4xx/5xx）',
  `latency_sum_ms` float NULL DEFAULT 0 COMMENT '总响应时间（毫秒）',
  `latency_min_ms` float NULL DEFAULT 0 COMMENT '最小响应时间',
  `latency_max_ms` float NULL DEFAULT 0 COMMENT '最大响应时间',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_date_endpoint_method`(`metric_date` ASC, `endpoint` ASC, `method` ASC) USING BTREE,
  INDEX `idx_metric_date`(`metric_date` ASC) USING BTREE,
  INDEX `idx_endpoint`(`endpoint` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'API 响应时间统计表 - 按天聚合' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_metrics
-- ----------------------------
INSERT INTO `api_metrics` VALUES ('07492a9f-0dd0-4d5a-9ef7-63ecc0454758', '2026-04-07', '/auth/refresh', 'POST', 8, 0, 438.34, 1.8751, 248.249, '2026-04-07 15:58:49', '2026-04-07 22:51:49');
INSERT INTO `api_metrics` VALUES ('1007fc2e-8e0a-4d2a-a745-9f9d0cc11ffe', '2026-04-07', '/auth/me', 'GET', 244, 0, 8384.07, 2.2592, 1168.76, '2026-04-07 15:05:03', '2026-04-07 23:49:54');
INSERT INTO `api_metrics` VALUES ('1815f84f-e4f0-4704-998d-c18419976bf9', '2026-04-07', '/chat-service/sessions/my', 'GET', 103, 0, 2434.1, 10.9317, 85.7536, '2026-04-07 15:05:49', '2026-04-07 23:43:52');
INSERT INTO `api_metrics` VALUES ('1db02bef-f027-46a9-85ef-2165e446f44a', '2026-04-08', '/auth/login', 'POST', 12, 0, 3998.53, 250.423, 558.867, '2026-04-08 00:06:40', '2026-04-08 15:49:03');
INSERT INTO `api_metrics` VALUES ('27d529bc-8e31-45cf-ac6e-9eecaf471cb4', '2026-04-08', '/tickets/', 'GET', 8, 0, 63.0596, 5.8769, 10.1885, '2026-04-08 16:00:40', '2026-04-08 16:01:00');
INSERT INTO `api_metrics` VALUES ('28b7ab88-6bfb-4f99-9639-a89d6ed48e9e', '2026-04-07', '/chat-service/sessions/{id}/messages', 'OPTIONS', 43, 0, 85.1756, 0.1764, 12.8396, '2026-04-07 18:58:18', '2026-04-07 23:50:25');
INSERT INTO `api_metrics` VALUES ('3021912e-b39f-4ba2-abad-47086c297207', '2026-04-08', '/auth/me', 'OPTIONS', 10, 0, 5.7054, 0.222, 2.1837, '2026-04-08 00:06:40', '2026-04-08 15:59:15');
INSERT INTO `api_metrics` VALUES ('32ec175d-4518-4d98-8eb6-8cd506cb9c53', '2026-04-07', '/knowledge/{id}', 'GET', 53, 0, 3716.99, 18.2684, 1164.16, '2026-04-07 15:08:46', '2026-04-07 18:40:10');
INSERT INTO `api_metrics` VALUES ('3b2d8bbb-bb52-46c2-b100-5e7a7dc17abf', '2026-04-07', '/chat-service/agent/online', 'POST', 47, 0, 1773.38, 13.7346, 444.163, '2026-04-07 15:05:49', '2026-04-07 23:43:51');
INSERT INTO `api_metrics` VALUES ('43433fb7-b971-41e6-bc71-693f564f65de', '2026-04-07', '/chat-service/ai-messages', 'POST', 16, 0, 339.152, 11.2311, 42.3043, '2026-04-07 22:07:12', '2026-04-07 23:50:15');
INSERT INTO `api_metrics` VALUES ('439809ce-72bd-4253-8647-7b7cac02c751', '2026-04-08', '/chat-service/sessions/{id}/messages', 'OPTIONS', 31, 0, 12.4043, 0.1896, 2.2224, '2026-04-08 00:06:41', '2026-04-08 16:00:16');
INSERT INTO `api_metrics` VALUES ('4c2ae807-f48f-4759-af93-c86a42bd40eb', '2026-04-08', '/chat-service/sessions', 'OPTIONS', 5, 0, 3.8177, 0.1983, 2.7453, '2026-04-08 00:07:14', '2026-04-08 15:59:34');
INSERT INTO `api_metrics` VALUES ('51c580b6-36ef-41b1-aab5-04dedf5616d9', '2026-04-07', '/chat/', 'OPTIONS', 21, 0, 7.323, 0.1613, 2.2828, '2026-04-07 15:06:19', '2026-04-07 23:46:29');
INSERT INTO `api_metrics` VALUES ('5581a455-c1fb-467c-9911-c466970ecfa4', '2026-04-07', '/auth/me', 'OPTIONS', 28, 0, 149.594, 0.1868, 115.941, '2026-04-07 15:06:03', '2026-04-07 23:43:51');
INSERT INTO `api_metrics` VALUES ('5ae156a3-aa99-4c5b-86eb-3b17ca962f1d', '2026-04-08', '/auth/me', 'GET', 42, 0, 630.349, 2.1208, 90.5696, '2026-04-08 00:06:40', '2026-04-08 16:09:04');
INSERT INTO `api_metrics` VALUES ('5caf373c-f6c7-4ad8-87d4-86e40bf51706', '2026-04-08', '/chat-service/sessions/my', 'GET', 71, 0, 1217.93, 6.2258, 79.1803, '2026-04-08 00:06:57', '2026-04-08 16:09:24');
INSERT INTO `api_metrics` VALUES ('62b0240a-0205-4353-a524-9d3954246611', '2026-04-07', '/chat/', 'POST', 51, 0, 1026580, 3254.5, 77048.3, '2026-04-07 15:06:59', '2026-04-07 23:50:14');
INSERT INTO `api_metrics` VALUES ('64e57e72-1a90-4668-b65e-96e87926ba2a', '2026-04-08', '/chat-service/sessions/waiting', 'GET', 744, 0, 5454.53, 1.6064, 95.7057, '2026-04-08 00:06:49', '2026-04-08 16:10:35');
INSERT INTO `api_metrics` VALUES ('6d90b40c-7c6c-490b-a339-9c83dcf97653', '2026-04-08', '/chat-service/sessions', 'POST', 18, 0, 1039, 15.3781, 291.42, '2026-04-08 00:07:14', '2026-04-08 16:00:16');
INSERT INTO `api_metrics` VALUES ('719e58b1-f533-4c5d-a2d3-7df4809c642a', '2026-04-08', '/chat/', 'POST', 3, 0, 47665.4, 3805.95, 38905, '2026-04-08 00:08:10', '2026-04-08 13:44:03');
INSERT INTO `api_metrics` VALUES ('788f5791-cdcc-4848-a037-47eb01752dea', '2026-04-07', '/tickets/admin/all', 'GET', 701, 0, 22436.6, 2.2793, 1221.03, '2026-04-07 15:05:04', '2026-04-07 23:51:49');
INSERT INTO `api_metrics` VALUES ('7d2fd0c4-4611-4608-953c-0559a4335b9a', '2026-04-07', '/chat-service/sessions', 'OPTIONS', 15, 0, 4.7275, 0.1863, 0.5594, '2026-04-07 18:42:51', '2026-04-07 23:50:25');
INSERT INTO `api_metrics` VALUES ('7ded2d33-2c20-406a-8781-0594c98026aa', '2026-04-08', '/knowledge/', 'GET', 10, 0, 117.025, 5.5723, 29.0765, '2026-04-08 00:17:15', '2026-04-08 16:00:45');
INSERT INTO `api_metrics` VALUES ('89132236-bc5f-4ea7-90ea-08f75c0bb7a7', '2026-04-07', '/chat-service/sessions', 'POST', 32, 0, 2119.35, 7.5527, 126.052, '2026-04-07 18:42:51', '2026-04-07 23:50:25');
INSERT INTO `api_metrics` VALUES ('89a6bd97-47a6-4ddc-a733-e1db94ee93c6', '2026-04-07', '/chat-service/ai-messages', 'OPTIONS', 7, 0, 23.502, 0.2304, 20.8975, '2026-04-07 22:07:00', '2026-04-07 23:46:29');
INSERT INTO `api_metrics` VALUES ('8bbabdca-e756-489e-97ce-4c513468d25e', '2026-04-07', '/knowledge/{id}/documents', 'GET', 53, 0, 4007.78, 16.8581, 1188.37, '2026-04-07 15:08:46', '2026-04-07 18:40:10');
INSERT INTO `api_metrics` VALUES ('8c8b0a16-960b-4a7e-9e01-26396bc2b4b2', '2026-04-07', '/knowledge/{id}', 'DELETE', 3, 0, 815.91, 82.2999, 451.861, '2026-04-07 17:22:40', '2026-04-07 18:04:46');
INSERT INTO `api_metrics` VALUES ('93c6bd52-9f62-46c7-ae45-0c54ce8a62e3', '2026-04-08', '/tickets/admin/all', 'GET', 288, 0, 3015.84, 4.7526, 93.8136, '2026-04-08 00:06:49', '2026-04-08 16:10:35');
INSERT INTO `api_metrics` VALUES ('93dc9880-4013-45b4-9acc-bcad8a5cb7c2', '2026-04-07', '/chat/clear-history', 'POST', 9, 0, 130.236, 6.7307, 29.1508, '2026-04-07 17:16:48', '2026-04-07 17:59:32');
INSERT INTO `api_metrics` VALUES ('97769595-42b0-4d17-9ef0-d834ce3ad813', '2026-04-08', '/chat-service/ai-messages', 'GET', 23, 0, 372.343, 6.3706, 42.9352, '2026-04-08 00:06:40', '2026-04-08 15:48:49');
INSERT INTO `api_metrics` VALUES ('a9388884-df12-4220-9ed3-5c498b0faf04', '2026-04-07', '/chat-service/sessions/{id}/messages', 'GET', 472, 0, 12030.2, 8.1727, 567.772, '2026-04-07 18:45:56', '2026-04-07 23:50:54');
INSERT INTO `api_metrics` VALUES ('b1f22b5b-3d7f-48d2-b47d-7ecb8db13fa2', '2026-04-07', '/users/', 'GET', 8, 0, 257.401, 12.4271, 50.7521, '2026-04-07 15:05:15', '2026-04-07 20:19:53');
INSERT INTO `api_metrics` VALUES ('b53ab132-54b6-4c68-864f-6882ce9e9c76', '2026-04-07', '/auth/login', 'POST', 62, 0, 21148.2, 251.011, 672.129, '2026-04-07 15:05:03', '2026-04-07 23:49:54');
INSERT INTO `api_metrics` VALUES ('ba99799c-49fc-4804-a7df-fd5c710360c2', '2026-04-07', '/chat-service/agent/offline', 'POST', 6, 0, 148.986, 16.9434, 39.2007, '2026-04-07 18:46:35', '2026-04-07 20:52:24');
INSERT INTO `api_metrics` VALUES ('c8a69d2b-bd7f-4159-8254-71cf5e48ee54', '2026-04-07', '/knowledge/', 'POST', 3, 0, 11086.5, 3501.93, 3926.51, '2026-04-07 17:22:58', '2026-04-07 18:05:20');
INSERT INTO `api_metrics` VALUES ('cc7bbe32-b4e8-431f-aea1-6ee257af8e51', '2026-04-07', '/knowledge/{id}/documents/{id}', 'DELETE', 7, 0, 261.667, 20.6732, 103.732, '2026-04-07 15:58:45', '2026-04-07 18:40:09');
INSERT INTO `api_metrics` VALUES ('cd2a400e-6042-463c-a021-76e688c9d313', '2026-04-08', '/chat-service/ai-messages', 'OPTIONS', 13, 0, 4.1423, 0.1945, 0.6286, '2026-04-08 00:06:40', '2026-04-08 15:48:49');
INSERT INTO `api_metrics` VALUES ('cda65be3-f93a-4743-a91a-16a74c22bfed', '2026-04-08', '/auth/refresh', 'POST', 7, 0, 82.1807, 0.9206, 79.2166, '2026-04-08 00:06:49', '2026-04-08 15:27:39');
INSERT INTO `api_metrics` VALUES ('ce259a2e-9c95-41be-8720-ecc11f18efdc', '2026-04-07', '/tickets/', 'GET', 4, 0, 53.1031, 10.3838, 16.2373, '2026-04-07 15:05:12', '2026-04-07 20:21:59');
INSERT INTO `api_metrics` VALUES ('d189ecb0-1b51-46b8-8ff4-d99522d109bd', '2026-04-07', '/chat-service/sessions/{id}/accept', 'POST', 1, 0, 60.0638, 60.0638, 60.0638, '2026-04-07 22:19:53', '2026-04-07 22:19:53');
INSERT INTO `api_metrics` VALUES ('e236528d-19b6-4931-acb8-6c34144f20d2', '2026-04-07', '/tickets/{id}/messages', 'GET', 4, 0, 60.0261, 10.998, 18.2998, '2026-04-07 20:27:15', '2026-04-07 20:34:19');
INSERT INTO `api_metrics` VALUES ('e952a0f6-fee8-4eef-b360-cadc105c7369', '2026-04-07', '/chat-service/ai-messages', 'GET', 42, 0, 968.394, 9.0739, 226.299, '2026-04-07 22:07:00', '2026-04-07 23:49:54');
INSERT INTO `api_metrics` VALUES ('ecc0a69a-c83e-43c0-bed7-3344fa4f7235', '2026-04-08', '/chat-service/sessions/{id}/close', 'POST', 15, 0, 359.691, 18.9869, 32.1123, '2026-04-08 00:06:59', '2026-04-08 15:59:55');
INSERT INTO `api_metrics` VALUES ('ee5f69ce-f69c-45f0-bb71-cffdc3f57b81', '2026-04-07', '/chat-service/sessions/waiting', 'GET', 959, 0, 17416.2, 1.1285, 580.643, '2026-04-07 15:05:49', '2026-04-07 23:51:49');
INSERT INTO `api_metrics` VALUES ('eeb38a9f-17bc-4bfb-82d3-45041a2bf42d', '2026-04-08', '/chat-service/sessions/{id}/messages', 'GET', 69, 0, 1045.81, 7.6032, 37.6723, '2026-04-08 00:06:41', '2026-04-08 16:09:26');
INSERT INTO `api_metrics` VALUES ('f007c636-eb99-4f26-9220-cfedd463773c', '2026-04-08', '/chat-service/agent/online', 'POST', 17, 0, 288.023, 8.9877, 50.1907, '2026-04-08 00:06:57', '2026-04-08 16:09:24');
INSERT INTO `api_metrics` VALUES ('f04f6a19-c721-4335-9308-18f3fe5f60ae', '2026-04-08', '/chat/', 'OPTIONS', 2, 0, 3.7322, 1.0417, 2.6905, '2026-04-08 00:08:05', '2026-04-08 13:43:05');
INSERT INTO `api_metrics` VALUES ('f0c396c5-52f3-40cc-b2de-b2dc2fac2d39', '2026-04-07', '/knowledge/{id}/documents', 'POST', 11, 0, 4761.83, 27.2738, 1490.81, '2026-04-07 15:07:52', '2026-04-07 18:39:39');
INSERT INTO `api_metrics` VALUES ('f66d8e79-62b1-46e3-94c5-11e28574c3d4', '2026-04-07', '/knowledge/', 'GET', 78, 0, 1677.88, 9.1258, 361.125, '2026-04-07 15:05:15', '2026-04-07 23:35:54');
INSERT INTO `api_metrics` VALUES ('f8c098e1-f9d8-4994-a605-f5ec9716d379', '2026-04-07', '/chat-service/sessions/{id}/close', 'POST', 23, 0, 1387.14, 29.1216, 525.389, '2026-04-07 18:45:59', '2026-04-07 23:43:51');
INSERT INTO `api_metrics` VALUES ('fd9c4e38-3af2-4759-9bef-f5b151dad912', '2026-04-08', '/chat-service/ai-messages', 'POST', 6, 0, 98.3142, 10.7527, 22.6152, '2026-04-08 00:08:05', '2026-04-08 13:44:03');

-- ----------------------------
-- Table structure for chat_messages
-- ----------------------------
DROP TABLE IF EXISTS `chat_messages`;
CREATE TABLE `chat_messages`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息ID (UUID)',
  `session_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '会话ID (AI聊天时为NULL)',
  `sender_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '发送者ID (AI/系统消息为NULL)',
  `sender_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发送者类型: customer/agent/system/ai',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息内容',
  `message_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'text' COMMENT '消息类型: text/image/file/system',
  `customer_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '客户ID (用于简化历史消息查询)',
  `is_read` tinyint(1) NULL DEFAULT 0 COMMENT '是否已读',
  `read_at` datetime NULL DEFAULT NULL COMMENT '阅读时间',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_session_id`(`session_id` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `idx_sender_id`(`sender_id` ASC) USING BTREE,
  INDEX `idx_customer_id`(`customer_id` ASC) USING BTREE,
  INDEX `idx_sender_type`(`sender_type` ASC) USING BTREE,
  CONSTRAINT `fk_chat_messages_customer` FOREIGN KEY (`customer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_chat_messages_sender` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_chat_messages_session` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '聊天记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of chat_messages
-- ----------------------------
INSERT INTO `chat_messages` VALUES ('04974679-348d-4705-9ed8-aa1388abf9bc', '08cf5863-d078-4818-9a05-a3f55c5f1808', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', 'f sadfg', 'text', NULL, 0, NULL, '2026-04-08 07:59:39');
INSERT INTO `chat_messages` VALUES ('2bd7ad34-b5c6-468b-9f9b-abf48d8048a6', '492f5837-aad2-4e17-a336-ab70ca897098', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', 'hello', 'text', NULL, 0, NULL, '2026-04-08 06:19:08');
INSERT INTO `chat_messages` VALUES ('30249e2f-1c91-4e53-8db2-d617f7255181', '492f5837-aad2-4e17-a336-ab70ca897098', NULL, 'system', '客服 aaron 已接入会话', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-08 05:44:21');
INSERT INTO `chat_messages` VALUES ('35db70b0-e819-40d3-8c40-19bdcc0b3b3f', NULL, NULL, 'ai', '📋 您的所有工单（共 2 个）\n\n状态分布：处理中: 2\n\n工单列表：\n1. TKT-20260404141650 | 订单无法支付，一直显示错误 | 处理中\n2. TKT-20260404113551 | 订单支付失败，系统持续显示错误 | 处理中\n\n💡 提示：如需查看某个工单的详细信息，请提供工单编号（如 TKT-20260404141650）\n', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-08 05:43:09');
INSERT INTO `chat_messages` VALUES ('56ab9157-85b8-4c66-81c3-89673fa92fcf', '08cf5863-d078-4818-9a05-a3f55c5f1808', NULL, 'system', '客服 aaron 已接入会话', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-08 07:59:34');
INSERT INTO `chat_messages` VALUES ('6d165dcc-0678-45c7-871f-0e5a9a35b914', NULL, NULL, 'ai', '📢 已催促处理工单 TKT-20260404141650\n\n当前状态：处理中\n优先级：已提升为高优先级\n\n客服会优先处理您的工单，请耐心等待。', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-08 05:44:04');
INSERT INTO `chat_messages` VALUES ('7e8f073f-6192-4ecd-ba8a-52ef417272aa', NULL, '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', 'TKT-20260404141650 加急工单', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-08 05:43:25');
INSERT INTO `chat_messages` VALUES ('8e56aaba-5fe1-4c83-a709-310081cfeff4', '3730eee3-1071-4f18-bb10-0a71ed7df105', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', 'sdf', 'text', NULL, 0, NULL, '2026-04-08 07:59:25');
INSERT INTO `chat_messages` VALUES ('8e58633a-5f4c-49ff-860d-7389a15f95f9', NULL, '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '工单列表', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-08 05:43:05');
INSERT INTO `chat_messages` VALUES ('c329d986-fac9-4293-ab41-685dfb1b1cce', '08cf5863-d078-4818-9a05-a3f55c5f1808', '0912d5f2-acdd-492e-852f-0b915524cafc', 'agent', 'asdfasd', 'text', NULL, 0, NULL, '2026-04-08 07:59:45');
INSERT INTO `chat_messages` VALUES ('cbf72081-c873-4fa2-b191-f19245f65f8a', '492f5837-aad2-4e17-a336-ab70ca897098', '0912d5f2-acdd-492e-852f-0b915524cafc', 'agent', 'asd', 'text', NULL, 0, NULL, '2026-04-08 07:16:23');
INSERT INTO `chat_messages` VALUES ('ce5ec3ee-1fc3-4740-918b-8f4fc48fe985', '492f5837-aad2-4e17-a336-ab70ca897098', '0912d5f2-acdd-492e-852f-0b915524cafc', 'agent', 'sdf', 'text', NULL, 0, NULL, '2026-04-08 06:18:21');
INSERT INTO `chat_messages` VALUES ('dd00e15d-1f5c-4d94-8ef4-da01d87e6911', 'f1c04b98-c889-4186-ba03-68512a561d6d', NULL, 'system', '客服 aaron 已接入会话', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-08 08:00:16');
INSERT INTO `chat_messages` VALUES ('fe6f22d0-583c-416d-ab7f-466c94ba19db', '3730eee3-1071-4f18-bb10-0a71ed7df105', NULL, 'system', '客服 aaron 已接入会话', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-08 07:17:31');

-- ----------------------------
-- Table structure for chat_sessions
-- ----------------------------
DROP TABLE IF EXISTS `chat_sessions`;
CREATE TABLE `chat_sessions`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '会话ID (UUID)',
  `customer_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '客户ID',
  `agent_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '接入客服ID',
  `ticket_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '关联工单ID',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'waiting' COMMENT '状态: waiting(排队中), connected(已接入), closed(已关闭)',
  `request_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '客户请求类型: order/payment/technical/other',
  `initial_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '客户初始消息',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `connected_at` datetime NULL DEFAULT NULL COMMENT '客服接入时间',
  `closed_at` datetime NULL DEFAULT NULL COMMENT '会话关闭时间',
  `last_message_at` datetime NULL DEFAULT NULL COMMENT '最后消息时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_agent_id`(`agent_id` ASC) USING BTREE,
  INDEX `idx_customer_id`(`customer_id` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  INDEX `fk_chat_sessions_ticket`(`ticket_id` ASC) USING BTREE,
  CONSTRAINT `fk_chat_sessions_agent` FOREIGN KEY (`agent_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_chat_sessions_customer` FOREIGN KEY (`customer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT,
  CONSTRAINT `fk_chat_sessions_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '聊天会话表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of chat_sessions
-- ----------------------------
INSERT INTO `chat_sessions` VALUES ('08cf5863-d078-4818-9a05-a3f55c5f1808', '9945a367-2c08-48e2-b172-ae16deeabf00', '0912d5f2-acdd-492e-852f-0b915524cafc', NULL, 'closed', 'general', '客户请求转人工', '2026-04-08 07:59:34', '2026-04-08 07:59:34', '2026-04-08 07:59:55', '2026-04-08 07:59:45');
INSERT INTO `chat_sessions` VALUES ('3730eee3-1071-4f18-bb10-0a71ed7df105', '9945a367-2c08-48e2-b172-ae16deeabf00', '0912d5f2-acdd-492e-852f-0b915524cafc', NULL, 'closed', 'general', '客户请求转人工', '2026-04-08 07:17:31', '2026-04-08 07:17:31', '2026-04-08 07:59:30', '2026-04-08 07:59:25');
INSERT INTO `chat_sessions` VALUES ('492f5837-aad2-4e17-a336-ab70ca897098', '9945a367-2c08-48e2-b172-ae16deeabf00', '0912d5f2-acdd-492e-852f-0b915524cafc', NULL, 'closed', 'general', '客户请求转人工', '2026-04-08 05:44:21', '2026-04-08 05:44:21', '2026-04-08 07:17:04', '2026-04-08 07:16:23');
INSERT INTO `chat_sessions` VALUES ('f1c04b98-c889-4186-ba03-68512a561d6d', '9945a367-2c08-48e2-b172-ae16deeabf00', '0912d5f2-acdd-492e-852f-0b915524cafc', NULL, 'connected', 'general', '客户请求转人工', '2026-04-08 08:00:16', '2026-04-08 08:00:16', NULL, NULL);

-- ----------------------------
-- Table structure for documents
-- ----------------------------
DROP TABLE IF EXISTS `documents`;
CREATE TABLE `documents`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文档ID (UUID)',
  `knowledge_base_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '知识库ID',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文档标题',
  `original_filename` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '原始文件名',
  `file_path` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '文件存储路径',
  `file_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '文件类型: txt, pdf, docx, md',
  `file_size` bigint(20) NULL DEFAULT 0 COMMENT '文件大小(字节)',
  `chunk_count` int(11) NULL DEFAULT 0 COMMENT '分块数量',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'processing' COMMENT '状态: processing, indexed, failed',
  `error_message` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '错误信息',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `meta_data` json NULL COMMENT '元数据',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_knowledge_base_id`(`knowledge_base_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  CONSTRAINT `fk_documents_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '文档表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of documents
-- ----------------------------
INSERT INTO `documents` VALUES ('1bf3ec19-37ac-4980-ad15-4eb9df7b14a0', 'd737e422-0ef8-4d25-b6cc-67a837db23bd', '个人简历-2026最新版.docx', '个人简历-2026最新版.docx', 'd737e422-0ef8-4d25-b6cc-67a837db23bd/个人简历-2026最新版.docx', '.docx', 43799, 17, 'indexed', NULL, '2026-04-07 10:14:21', '2026-04-07 10:14:25', NULL);
INSERT INTO `documents` VALUES ('2d84a877-2ada-47be-aadb-df861030e9f2', 'd737e422-0ef8-4d25-b6cc-67a837db23bd', '胥腾龙-个人简历-202603最新版.pdf', '胥腾龙-个人简历-202603最新版.pdf', 'd737e422-0ef8-4d25-b6cc-67a837db23bd/胥腾龙-个人简历-202603最新版.pdf', '.pdf', 556094, 20, 'indexed', NULL, '2026-04-07 10:05:29', '2026-04-07 10:05:54', NULL);
INSERT INTO `documents` VALUES ('a8618182-fcba-46f7-a683-bb2b20075c6f', '5caa3838-0145-40e0-bff1-43f040a71e62', '胥腾龙-个人简历-202603最新版.pdf', '胥腾龙-个人简历-202603最新版.pdf', '5caa3838-0145-40e0-bff1-43f040a71e62/胥腾龙-个人简历-202603最新版.pdf', '.pdf', 556094, 24, 'indexed', NULL, '2026-04-07 07:07:52', '2026-04-07 07:07:57', NULL);
INSERT INTO `documents` VALUES ('e38d562f-07de-46e5-a3b9-e84b409eaf74', '5caa3838-0145-40e0-bff1-43f040a71e62', '胥腾龙-个人简历-202603最新版.pdf', '胥腾龙-个人简历-202603最新版.pdf', '5caa3838-0145-40e0-bff1-43f040a71e62/胥腾龙-个人简历-202603最新版.pdf', '.pdf', 556094, 24, 'indexed', NULL, '2026-04-05 13:54:31', '2026-04-05 13:54:37', NULL);

-- ----------------------------
-- Table structure for error_metrics
-- ----------------------------
DROP TABLE IF EXISTS `error_metrics`;
CREATE TABLE `error_metrics`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '记录ID (UUID)',
  `metric_date` date NOT NULL COMMENT '统计日期',
  `error_type` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '错误类型: HTTP404/HTTP500/ValidationError等',
  `endpoint` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '发生错误的端点（可选）',
  `count` int(11) NOT NULL DEFAULT 0 COMMENT '错误次数',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_date_type_endpoint`(`metric_date` ASC, `error_type` ASC, `endpoint` ASC) USING BTREE,
  INDEX `idx_metric_date`(`metric_date` ASC) USING BTREE,
  INDEX `idx_error_type`(`error_type` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '错误统计表 - 按天聚合' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of error_metrics
-- ----------------------------
INSERT INTO `error_metrics` VALUES ('282107ec-762e-48d9-8889-6951c6ffba4f', '2026-04-07', 'HTTP500', '/chat-service/sessions', 1, '2026-04-07 22:13:40', '2026-04-07 22:13:40');
INSERT INTO `error_metrics` VALUES ('287d08de-3dbe-4f29-9d68-a7d675376144', '2026-04-08', 'HTTP401', '/auth/me', 3, '2026-04-08 13:42:53', '2026-04-08 15:17:10');
INSERT INTO `error_metrics` VALUES ('2d72d46c-a6e9-4f78-a3c1-930e9720cda9', '2026-04-07', 'HTTP500', '/chat-service/ai-messages', 2, '2026-04-07 22:07:12', '2026-04-07 22:07:17');
INSERT INTO `error_metrics` VALUES ('332c6402-4e55-4c95-839a-215a7eaf58ec', '2026-04-07', 'HTTP401', '/chat-service/sessions', 2, '2026-04-07 18:42:51', '2026-04-07 20:16:29');
INSERT INTO `error_metrics` VALUES ('3deb1820-03e4-48e6-927c-c996e184670b', '2026-04-08', 'HTTP401', '/chat-service/sessions/waiting', 8, '2026-04-08 00:06:49', '2026-04-08 15:27:39');
INSERT INTO `error_metrics` VALUES ('3dee5db0-dc8d-4ed1-9bb1-08d506ee59ae', '2026-04-07', 'HTTP403', '/users/', 4, '2026-04-07 15:05:15', '2026-04-07 20:19:53');
INSERT INTO `error_metrics` VALUES ('4e356fc0-c83c-466e-b106-edec55bbcda7', '2026-04-07', 'HTTP401', '/chat-service/sessions/waiting', 9, '2026-04-07 18:50:57', '2026-04-07 22:51:49');
INSERT INTO `error_metrics` VALUES ('506e73f0-1980-44e4-9454-48c2f50cc0e0', '2026-04-07', 'HTTP422', '/auth/refresh', 7, '2026-04-07 15:58:49', '2026-04-07 22:51:49');
INSERT INTO `error_metrics` VALUES ('6f56854f-9e11-4656-beb3-6cb982437d31', '2026-04-07', 'HTTP404', '/chat-service/sessions/{id}/messages', 1, '2026-04-07 19:43:26', '2026-04-07 19:43:26');
INSERT INTO `error_metrics` VALUES ('7ad3be34-a567-4151-b5ef-15176d55714b', '2026-04-08', 'HTTP401', '/tickets/admin/all', 5, '2026-04-08 00:06:49', '2026-04-08 15:27:39');
INSERT INTO `error_metrics` VALUES ('8ad8a2c2-bacd-46bf-b371-c6b1bbdebb0a', '2026-04-07', 'HTTP400', '/knowledge/{id}/documents', 1, '2026-04-07 18:14:13', '2026-04-07 18:14:13');
INSERT INTO `error_metrics` VALUES ('8db56b54-b962-4932-bf84-f8e980034c6d', '2026-04-07', 'HTTP401', '/chat/clear-history', 3, '2026-04-07 17:16:48', '2026-04-07 17:55:01');
INSERT INTO `error_metrics` VALUES ('cb5af29a-36c0-411e-a288-443d604025fe', '2026-04-07', 'HTTP401', '/tickets/admin/all', 6, '2026-04-07 15:58:49', '2026-04-07 22:51:49');
INSERT INTO `error_metrics` VALUES ('db7fa1d7-77b9-4cd7-a7a4-ba766f48f186', '2026-04-07', 'HTTP401', '/auth/me', 6, '2026-04-07 16:01:52', '2026-04-07 23:19:19');
INSERT INTO `error_metrics` VALUES ('dd4953bc-5ff2-4022-b034-fd599843c7f0', '2026-04-08', 'HTTP422', '/auth/refresh', 9, '2026-04-08 00:06:49', '2026-04-08 15:27:39');

-- ----------------------------
-- Table structure for intent_metrics
-- ----------------------------
DROP TABLE IF EXISTS `intent_metrics`;
CREATE TABLE `intent_metrics`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '记录ID (UUID)',
  `metric_date` date NOT NULL COMMENT '统计日期',
  `intent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '意图类型: create_ticket/query_ticket/process_ticket/summary/general',
  `total` int(11) NOT NULL DEFAULT 0 COMMENT '总识别次数',
  `correct` int(11) NOT NULL DEFAULT 0 COMMENT '正确次数',
  `confidence_sum` float NULL DEFAULT 0 COMMENT '置信度总和（用于计算平均置信度）',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_date_intent`(`metric_date` ASC, `intent` ASC) USING BTREE,
  INDEX `idx_metric_date`(`metric_date` ASC) USING BTREE,
  INDEX `idx_intent`(`intent` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '意图识别统计表 - 按天聚合' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of intent_metrics
-- ----------------------------
INSERT INTO `intent_metrics` VALUES ('21316ae3-a4a6-40c0-9123-c129c097ecd1', '2026-04-07', 'query_ticket', 21, 0, 21, '2026-04-07 20:22:20', '2026-04-07 23:50:14');
INSERT INTO `intent_metrics` VALUES ('64c489ab-d622-4d66-942f-740d72dca921', '2026-04-07', 'process_ticket', 7, 0, 7, '2026-04-07 20:22:46', '2026-04-07 21:15:15');
INSERT INTO `intent_metrics` VALUES ('7b19ef8d-1cbf-4a92-a928-6dd07b425e6e', '2026-04-07', 'general', 23, 0, 23, '2026-04-07 15:06:27', '2026-04-07 20:17:35');
INSERT INTO `intent_metrics` VALUES ('a3e13ddb-5960-499a-831a-abb2a6eaf035', '2026-04-08', 'process_ticket', 1, 0, 1, '2026-04-08 13:43:55', '2026-04-08 13:43:55');
INSERT INTO `intent_metrics` VALUES ('b3a87c67-fad2-490c-95cb-3c91af65c5ae', '2026-04-08', 'query_ticket', 2, 0, 2, '2026-04-08 00:08:10', '2026-04-08 13:43:09');

-- ----------------------------
-- Table structure for knowledge_bases
-- ----------------------------
DROP TABLE IF EXISTS `knowledge_bases`;
CREATE TABLE `knowledge_bases`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '知识库ID (UUID)',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '知识库名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '知识库描述',
  `collection_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Milvus Collection 名称',
  `owner_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '所有者ID (用户ID)',
  `document_count` int(11) NULL DEFAULT 0 COMMENT '文档数量',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'active' COMMENT '状态: active, inactive, building',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `embedding_model` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'sentence-transformers/all-MiniLM-L6-v2' COMMENT '嵌入模型',
  `meta_data` json NULL COMMENT '元数据',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_name`(`name` ASC) USING BTREE,
  INDEX `idx_owner_id`(`owner_id` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '知识库表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of knowledge_bases
-- ----------------------------
INSERT INTO `knowledge_bases` VALUES ('5caa3838-0145-40e0-bff1-43f040a71e62', '人事制度', NULL, 'kb_a4e3e320ed7742a1a558d4eefa9ffc25', '0912d5f2-acdd-492e-852f-0b915524cafc', 0, 'active', '2026-04-05 13:54:02', '2026-04-05 13:54:02', 'sentence-transformers/all-MiniLM-L6-v2', NULL);
INSERT INTO `knowledge_bases` VALUES ('d737e422-0ef8-4d25-b6cc-67a837db23bd', 'sad', NULL, 'kb_42e9eca3a6904adfb526c8b7f29748f0', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 2, 'active', '2026-04-07 10:05:20', '2026-04-07 10:40:10', 'sentence-transformers/all-MiniLM-L6-v2', NULL);

-- ----------------------------
-- Table structure for roles
-- ----------------------------
DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色名称: admin, agent, operator',
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '角色代码',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '角色描述',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `permissions` json NULL COMMENT '权限列表',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `name`(`name` ASC) USING BTREE,
  UNIQUE INDEX `code`(`code` ASC) USING BTREE,
  INDEX `idx_name`(`name` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 5 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '角色表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of roles
-- ----------------------------
INSERT INTO `roles` VALUES (1, '管理员', 'admin', '系统管理员，拥有所有权限', '2026-04-02 21:55:25', '2026-04-04 11:24:03', '[]');
INSERT INTO `roles` VALUES (2, '客服', 'agent', '客服人员，可以处理工单', '2026-04-02 21:55:25', '2026-04-04 11:24:01', '[]');
INSERT INTO `roles` VALUES (3, '运营', 'operator', '运营人员，可以查看数据和报表', '2026-04-02 21:55:25', '2026-04-04 11:24:00', '[]');
INSERT INTO `roles` VALUES (4, '客户', 'customer', '普通客户', '2026-04-03 23:46:13', '2026-04-04 11:44:55', '[]');

-- ----------------------------
-- Table structure for system_configs
-- ----------------------------
DROP TABLE IF EXISTS `system_configs`;
CREATE TABLE `system_configs`  (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `key` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '配置键',
  `value` json NOT NULL COMMENT '配置值',
  `description` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '描述',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `key`(`key` ASC) USING BTREE,
  INDEX `idx_key`(`key` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统配置表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of system_configs
-- ----------------------------

-- ----------------------------
-- Table structure for ticket_messages
-- ----------------------------
DROP TABLE IF EXISTS `ticket_messages`;
CREATE TABLE `ticket_messages`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息ID (UUID)',
  `ticket_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工单ID',
  `sender_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '发送者ID (用户ID或NULL表示系统)',
  `sender_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'customer' COMMENT '发送者类型: customer, agent, system',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '消息内容',
  `message_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'text' COMMENT '消息类型: text, image, file',
  `is_read` tinyint(1) NULL DEFAULT 0 COMMENT '是否已读',
  `read_at` datetime NULL DEFAULT NULL COMMENT '阅读时间',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_ticket_id`(`ticket_id` ASC) USING BTREE,
  INDEX `idx_sender_id`(`sender_id` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  CONSTRAINT `fk_messages_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '工单消息表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ticket_messages
-- ----------------------------
INSERT INTO `ticket_messages` VALUES ('03a95e9b-ed7f-4f59-82cf-57c18a0a6360', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'agent', 'hello', 'text', 0, NULL, '2026-04-04 14:48:31');
INSERT INTO `ticket_messages` VALUES ('0908f07e-766e-4e61-bc3d-0593997e8a87', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '【客户催促】请尽快处理此工单。原因：加急', 'text', 0, NULL, '2026-04-07 12:33:44');
INSERT INTO `ticket_messages` VALUES ('2b0e92e0-c116-433f-b94f-ab3477cb9eb3', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '【客户催促】请尽快处理此工单。原因：TKT-20260404141650 加急工单', 'text', 0, NULL, '2026-04-08 05:44:04');
INSERT INTO `ticket_messages` VALUES ('3f588df5-a897-45cd-b52f-571ea739bac8', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '123', 'text', 0, NULL, '2026-04-04 15:19:09');
INSERT INTO `ticket_messages` VALUES ('40600bcd-af7a-4f80-8206-a9331bc20c24', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', '你好\n', 'text', 0, NULL, '2026-04-04 14:46:57');
INSERT INTO `ticket_messages` VALUES ('5b49c2d5-73f5-4d57-b835-2ed8b9d29a38', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', '123', 'text', 0, NULL, '2026-04-04 14:58:25');
INSERT INTO `ticket_messages` VALUES ('6a916975-5c8b-417f-a114-3f3ca89a4cd2', 'cb597913-3add-4426-82fd-da3ae5506e26', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', 'aaa', 'text', 0, NULL, '2026-04-04 07:11:13');
INSERT INTO `ticket_messages` VALUES ('8ebae0b8-d3c1-44a1-861b-8c59fcfd9615', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'agent', '123', 'text', 0, NULL, '2026-04-04 14:54:50');
INSERT INTO `ticket_messages` VALUES ('9135f1b1-568c-44d9-917c-148ff948bdc8', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '【客户催促】请尽快处理此工单。原因：催促处理', 'text', 0, NULL, '2026-04-07 13:15:18');
INSERT INTO `ticket_messages` VALUES ('c4ee2d5e-3117-4abe-9bd0-c6f0e3f545b1', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', '12312', 'text', 0, NULL, '2026-04-04 15:19:28');
INSERT INTO `ticket_messages` VALUES ('c71edfbd-67c6-4a3e-97eb-05ca8ad7f324', 'cb597913-3add-4426-82fd-da3ae5506e26', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', '123', 'text', 0, NULL, '2026-04-04 15:17:49');
INSERT INTO `ticket_messages` VALUES ('c8e52eb5-3636-40bf-90be-08a50513967f', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '【客户催促】请尽快处理此工单。原因：用户要求加急处理工单', 'text', 0, NULL, '2026-04-07 12:53:15');
INSERT INTO `ticket_messages` VALUES ('cbae67d8-84c4-4e46-b52c-3c8cf5e28bbd', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '【客户催促】请尽快处理此工单。原因：用户请求工单加急处理', 'text', 0, NULL, '2026-04-07 12:48:38');
INSERT INTO `ticket_messages` VALUES ('ccb23d43-ebc4-4f65-b513-a41cf2d8b817', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', 'asdf', 'text', 0, NULL, '2026-04-04 15:03:30');
INSERT INTO `ticket_messages` VALUES ('e3c02d01-931f-4d57-afbc-7150c15e53fe', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '123', 'text', 0, NULL, '2026-04-04 14:58:00');
INSERT INTO `ticket_messages` VALUES ('fe7bb768-efe5-4df9-b8f5-b8a4abed9cea', 'cb597913-3add-4426-82fd-da3ae5506e26', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', 'bbbb', 'text', 0, NULL, '2026-04-04 07:11:37');

-- ----------------------------
-- Table structure for ticket_status_logs
-- ----------------------------
DROP TABLE IF EXISTS `ticket_status_logs`;
CREATE TABLE `ticket_status_logs`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志ID (UUID)',
  `ticket_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工单ID',
  `from_status` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '原状态',
  `to_status` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '新状态',
  `changed_by_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '变更者ID',
  `note` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '备注',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_ticket_id`(`ticket_id` ASC) USING BTREE,
  INDEX `idx_changed_by_id`(`changed_by_id` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE,
  CONSTRAINT `fk_status_logs_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '工单状态变更记录表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of ticket_status_logs
-- ----------------------------
INSERT INTO `ticket_status_logs` VALUES ('41d0ebbd-bd4d-4783-9ad8-c14a66e58fc3', 'cb597913-3add-4426-82fd-da3ae5506e26', 'pending', 'in_progress', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '状态变更为 in_progress', '2026-04-04 15:17:43');
INSERT INTO `ticket_status_logs` VALUES ('4f33b93f-f4e0-4a0f-a26d-d25b22f06da7', 'cb597913-3add-4426-82fd-da3ae5506e26', 'open', 'pending', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '状态变更为 pending', '2026-04-04 15:10:44');

-- ----------------------------
-- Table structure for tickets
-- ----------------------------
DROP TABLE IF EXISTS `tickets`;
CREATE TABLE `tickets`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工单ID (UUID)',
  `ticket_no` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工单编号',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工单标题',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '工单内容',
  `priority` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'normal' COMMENT '优先级: low, normal, high, urgent',
  `category` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'general' COMMENT '分类: technical, billing, account, other',
  `status` varchar(30) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'open' COMMENT '状态: open, pending, in_progress, resolved, closed',
  `customer_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '客户ID (用户ID)',
  `assigned_agent_id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '分配的客服ID',
  `customer_info` json NULL COMMENT '客户信息 (JSON: name, email, phone)',
  `meta_data` json NULL COMMENT '元数据 (JSON)',
  `resolved_at` datetime NULL DEFAULT NULL COMMENT '解决时间',
  `closed_at` datetime NULL DEFAULT NULL COMMENT '关闭时间',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `ticket_no`(`ticket_no` ASC) USING BTREE,
  INDEX `idx_ticket_no`(`ticket_no` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE,
  INDEX `idx_priority`(`priority` ASC) USING BTREE,
  INDEX `idx_category`(`category` ASC) USING BTREE,
  INDEX `idx_customer_id`(`customer_id` ASC) USING BTREE,
  INDEX `idx_assigned_agent_id`(`assigned_agent_id` ASC) USING BTREE,
  INDEX `idx_created_at`(`created_at` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '工单表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of tickets
-- ----------------------------
INSERT INTO `tickets` VALUES ('21e19979-e603-4234-a6ab-a54647fb9ad4', 'TKT-20260404113551', '订单支付失败，系统持续显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'in_progress', '9945a367-2c08-48e2-b172-ae16deeabf00', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-04 11:35:51', '2026-04-04 15:10:31');
INSERT INTO `tickets` VALUES ('242b76ef-e26b-489f-99bc-bea50fe5f65d', 'TKT-20260404141650', '订单无法支付，一直显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'in_progress', '9945a367-2c08-48e2-b172-ae16deeabf00', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-04 14:16:50', '2026-04-08 05:44:04');
INSERT INTO `tickets` VALUES ('cb597913-3add-4426-82fd-da3ae5506e26', 'TKT-20260404071031', '客户投诉', 'bbb', 'high', 'technical', 'in_progress', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '{\"contact\": \"13918282671\"}', NULL, NULL, NULL, '2026-04-04 07:10:32', '2026-04-04 15:18:32');

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户ID (UUID)',
  `username` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '用户名',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '邮箱',
  `password_hash` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '密码哈希',
  `full_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '全名',
  `phone` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '电话',
  `role_id` int(11) NOT NULL DEFAULT 1 COMMENT '角色ID (外键)',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT '是否激活',
  `is_verified` tinyint(1) NULL DEFAULT 0 COMMENT '是否验证邮箱',
  `last_login_at` datetime NULL DEFAULT NULL COMMENT '最后登录时间',
  `created_at` datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `avatar_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '头像URL',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE,
  INDEX `idx_username`(`username` ASC) USING BTREE,
  INDEX `idx_email`(`email` ASC) USING BTREE,
  INDEX `idx_role_id`(`role_id` ASC) USING BTREE,
  CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of users
-- ----------------------------
INSERT INTO `users` VALUES ('0912d5f2-acdd-492e-852f-0b915524cafc', 'aaron', '592235963@qq.com', '$2b$12$et1MM2G5pbTsrRRAfnYaNONQLt/UowEBuagZQsWUnqA22rfvh2mTe', 'aaron', NULL, 2, 1, 0, '2026-04-08 07:49:04', '2026-04-04 03:33:26', '2026-04-08 07:49:04', NULL);
INSERT INTO `users` VALUES ('230c67e9-4f24-448e-8bba-03adb9f88b2b', 'xjy', '592235960@qq.com', '$2b$12$heMzkM.w1CkfrWthYmGcwe6f6uNDhlEcWjq0LgntFo63EHdrNS1x6', 'xjy', NULL, 4, 1, 0, NULL, '2026-04-05 11:51:34', '2026-04-05 11:51:34', NULL);
INSERT INTO `users` VALUES ('7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'admin', 'admin@example.com', '$2b$12$W.FoBpg6qrtU5v79Tar52eTr23NqomEgncxgHQJF4mhW6u6WwYvx.', '管理员', '13918282671', 1, 1, 0, '2026-04-07 13:31:22', '2026-04-03 15:51:49', '2026-04-07 13:31:22', NULL);
INSERT INTO `users` VALUES ('9945a367-2c08-48e2-b172-ae16deeabf00', 'xlh', '592235962@qq.com', '$2b$12$HOzPDRjUNedD/dgktwMPBu9twn0ev7kHwwO7.Gl3Ou4RCyLrTkK8m', 'xu', NULL, 4, 1, 0, '2026-04-08 07:48:50', '2026-04-04 03:32:30', '2026-04-08 07:48:50', NULL);
INSERT INTO `users` VALUES ('a3ff98db-713d-47e4-bbfd-e466be173419', 'hxy', '592235965@qq.com', '$2b$12$km.ZhBLHSDyzI8j4wvSG.eALsT.XupPfSjJ5TrehkZ2Vt2TyUnj/W', 'hxy', NULL, 3, 1, 0, '2026-04-05 11:49:49', '2026-04-04 03:45:39', '2026-04-05 11:49:49', NULL);

SET FOREIGN_KEY_CHECKS = 1;
