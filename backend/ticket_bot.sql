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

 Date: 09/04/2026 16:36:39
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
  `last_heartbeat` datetime(6) NULL DEFAULT NULL,
  `updated_at` datetime(6) NULL DEFAULT NULL,
  PRIMARY KEY (`agent_id`) USING BTREE,
  CONSTRAINT `fk_agent_status_agent` FOREIGN KEY (`agent_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '客服在线状态表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of agent_status
-- ----------------------------
INSERT INTO `agent_status` VALUES ('0912d5f2-acdd-492e-852f-0b915524cafc', 'offline', 0, 5, 1, 0, '2026-04-05 11:50:57.000000', '2026-04-09 14:26:46.000000');
INSERT INTO `agent_status` VALUES ('7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'online', 0, 5, 0, 0, '2026-04-05 06:51:47.000000', '2026-04-09 16:34:23.087002');

-- ----------------------------
-- Table structure for alembic_version
-- ----------------------------
DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version`  (
  `version_num` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  PRIMARY KEY (`version_num`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of alembic_version
-- ----------------------------
INSERT INTO `alembic_version` VALUES ('001');

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
  `created_at` datetime(6) NULL DEFAULT NULL,
  `updated_at` datetime(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_date_endpoint_method`(`metric_date` ASC, `endpoint` ASC, `method` ASC) USING BTREE,
  INDEX `idx_metric_date`(`metric_date` ASC) USING BTREE,
  INDEX `idx_endpoint`(`endpoint` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'API 响应时间统计表 - 按天聚合' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of api_metrics
-- ----------------------------
INSERT INTO `api_metrics` VALUES ('050b5c07-f80c-40a7-92d2-4b0868558dc4', '2026-04-09', '/chat-service/sessions', 'OPTIONS', 2, 0, 0.5501, 0.2282, 0.3219, '2026-04-09 16:03:09.000000', '2026-04-09 16:32:02.000000');
INSERT INTO `api_metrics` VALUES ('07492a9f-0dd0-4d5a-9ef7-63ecc0454758', '2026-04-07', '/auth/refresh', 'POST', 8, 0, 438.34, 1.8751, 248.249, '2026-04-07 15:58:49.000000', '2026-04-07 22:51:49.000000');
INSERT INTO `api_metrics` VALUES ('0d7dd674-ea34-4123-b6c8-cb6f9bd54b78', '2026-04-09', '/chat-service/sessions/{id}/messages', 'GET', 52, 0, 767.688, 8.4005, 31.1626, '2026-04-09 03:23:16.000000', '2026-04-09 16:34:42.000000');
INSERT INTO `api_metrics` VALUES ('0f1011d6-384f-45d5-8d80-b27bf53b0ee8', '2026-04-08', '/dashboard/ticket-categories', 'GET', 40, 0, 2105.44, 15.6629, 120.962, '2026-04-08 18:02:00.000000', '2026-04-08 22:43:48.000000');
INSERT INTO `api_metrics` VALUES ('1007fc2e-8e0a-4d2a-a745-9f9d0cc11ffe', '2026-04-07', '/auth/me', 'GET', 244, 0, 8384.07, 2.2592, 1168.76, '2026-04-07 15:05:03.000000', '2026-04-07 23:49:54.000000');
INSERT INTO `api_metrics` VALUES ('1815f84f-e4f0-4704-998d-c18419976bf9', '2026-04-07', '/chat-service/sessions/my', 'GET', 103, 0, 2434.1, 10.9317, 85.7536, '2026-04-07 15:05:49.000000', '2026-04-07 23:43:52.000000');
INSERT INTO `api_metrics` VALUES ('1db02bef-f027-46a9-85ef-2165e446f44a', '2026-04-08', '/auth/login', 'POST', 24, 0, 7591.25, 245.017, 558.867, '2026-04-08 00:06:40.000000', '2026-04-08 22:43:48.000000');
INSERT INTO `api_metrics` VALUES ('206c06ac-98bf-4e63-ba88-2da839a906a2', '2026-04-08', '/chat-service/agent/offline', 'POST', 1, 0, 11.2707, 11.2707, 11.2707, '2026-04-08 22:09:26.000000', '2026-04-08 22:09:26.000000');
INSERT INTO `api_metrics` VALUES ('229d46e6-eaa5-43b4-aa50-96fdae13a1c7', '2026-04-08', '/metrics/websocket', 'GET', 97, 0, 3281.44, 7.441, 246.849, '2026-04-08 19:34:18.000000', '2026-04-08 22:57:03.000000');
INSERT INTO `api_metrics` VALUES ('23573e7e-b087-4420-9448-11b5dd9789cd', '2026-04-08', '/metrics/api', 'GET', 97, 0, 3217.49, 16.1585, 253.143, '2026-04-08 19:34:18.000000', '2026-04-08 22:57:03.000000');
INSERT INTO `api_metrics` VALUES ('27d529bc-8e31-45cf-ac6e-9eecaf471cb4', '2026-04-08', '/tickets/', 'GET', 36, 0, 285.93, 5.3423, 14.1507, '2026-04-08 16:00:40.000000', '2026-04-08 22:16:31.000000');
INSERT INTO `api_metrics` VALUES ('28b7ab88-6bfb-4f99-9639-a89d6ed48e9e', '2026-04-07', '/chat-service/sessions/{id}/messages', 'OPTIONS', 43, 0, 85.1756, 0.1764, 12.8396, '2026-04-07 18:58:18.000000', '2026-04-07 23:50:25.000000');
INSERT INTO `api_metrics` VALUES ('299f0433-89ff-4556-afc8-477b009ad553', '2026-04-09', '/dashboard/ticket-trends', 'GET', 68, 0, 4849.3, 38.8111, 271.586, '2026-04-09 00:05:29.000000', '2026-04-09 16:31:05.000000');
INSERT INTO `api_metrics` VALUES ('3021912e-b39f-4ba2-abad-47086c297207', '2026-04-08', '/auth/me', 'OPTIONS', 12, 0, 6.3558, 0.222, 2.1837, '2026-04-08 00:06:40.000000', '2026-04-08 22:09:33.000000');
INSERT INTO `api_metrics` VALUES ('32ec175d-4518-4d98-8eb6-8cd506cb9c53', '2026-04-07', '/knowledge/{id}', 'GET', 53, 0, 3716.99, 18.2684, 1164.16, '2026-04-07 15:08:46.000000', '2026-04-07 18:40:10.000000');
INSERT INTO `api_metrics` VALUES ('3b2d8bbb-bb52-46c2-b100-5e7a7dc17abf', '2026-04-07', '/chat-service/agent/online', 'POST', 47, 0, 1773.38, 13.7346, 444.163, '2026-04-07 15:05:49.000000', '2026-04-07 23:43:51.000000');
INSERT INTO `api_metrics` VALUES ('3fa72c27-c14d-476b-8812-eafe499d244d', '2026-04-09', '/dashboard/recent-activities', 'GET', 68, 0, 4490.06, 18.4235, 273.185, '2026-04-09 00:05:29.000000', '2026-04-09 16:31:05.000000');
INSERT INTO `api_metrics` VALUES ('43433fb7-b971-41e6-bc71-693f564f65de', '2026-04-07', '/chat-service/ai-messages', 'POST', 16, 0, 339.152, 11.2311, 42.3043, '2026-04-07 22:07:12.000000', '2026-04-07 23:50:15.000000');
INSERT INTO `api_metrics` VALUES ('439809ce-72bd-4253-8647-7b7cac02c751', '2026-04-08', '/chat-service/sessions/{id}/messages', 'OPTIONS', 35, 0, 13.7247, 0.1832, 2.2224, '2026-04-08 00:06:41.000000', '2026-04-08 22:09:36.000000');
INSERT INTO `api_metrics` VALUES ('4571f1b2-616b-4f37-b529-5bf3cc4b34fa', '2026-04-09', '/tickets/admin/all', 'GET', 880, 0, 17098.4, 1.3135, 412.944, '2026-04-09 00:05:29.000000', '2026-04-09 16:36:25.000000');
INSERT INTO `api_metrics` VALUES ('47690747-8e54-4875-8390-a5bd3bb42486', '2026-04-08', '/dashboard/ticket-trends', 'GET', 40, 0, 2180.61, 29.5049, 115.732, '2026-04-08 18:02:00.000000', '2026-04-08 22:43:48.000000');
INSERT INTO `api_metrics` VALUES ('4b7b3309-61d7-4d44-92c3-3593012a41a6', '2026-04-09', '/chat-service/ai-messages', 'GET', 10, 0, 175.142, 9.1146, 39.0395, '2026-04-09 03:23:14.000000', '2026-04-09 16:33:47.000000');
INSERT INTO `api_metrics` VALUES ('4be7f150-bebf-4855-8c20-6ec4561282a3', '2026-04-09', '/auth/me', 'OPTIONS', 4, 0, 1.4394, 0.2536, 0.4586, '2026-04-09 03:23:10.000000', '2026-04-09 16:31:48.000000');
INSERT INTO `api_metrics` VALUES ('4c2ae807-f48f-4759-af93-c86a42bd40eb', '2026-04-08', '/chat-service/sessions', 'OPTIONS', 5, 0, 3.8177, 0.1983, 2.7453, '2026-04-08 00:07:14.000000', '2026-04-08 15:59:34.000000');
INSERT INTO `api_metrics` VALUES ('4ca6540d-3763-495e-b110-f5d72658c83c', '2026-04-09', '/chat-service/ai-messages', 'OPTIONS', 11, 0, 5.2113, 0.2084, 1.2402, '2026-04-09 03:23:13.000000', '2026-04-09 16:33:47.000000');
INSERT INTO `api_metrics` VALUES ('50ebf84e-3b19-44a2-80aa-83ee2a70003e', '2026-04-09', '/chat-service/agent/online', 'POST', 6, 0, 127.66, 8.0676, 62.2995, '2026-04-09 01:59:35.000000', '2026-04-09 16:31:43.000000');
INSERT INTO `api_metrics` VALUES ('51c580b6-36ef-41b1-aab5-04dedf5616d9', '2026-04-07', '/chat/', 'OPTIONS', 21, 0, 7.323, 0.1613, 2.2828, '2026-04-07 15:06:19.000000', '2026-04-07 23:46:29.000000');
INSERT INTO `api_metrics` VALUES ('52010382-ad44-4804-a5ea-6e63bb56da7f', '2026-04-09', '/knowledge/', 'GET', 26, 0, 199.872, 5.649, 11.5991, '2026-04-09 01:59:22.000000', '2026-04-09 16:31:38.000000');
INSERT INTO `api_metrics` VALUES ('5341695c-9442-4f56-bd87-911397f011b3', '2026-04-09', '/auth/refresh', 'POST', 20, 0, 403.005, 0.8155, 99.5651, '2026-04-09 00:36:44.000000', '2026-04-09 15:46:04.000000');
INSERT INTO `api_metrics` VALUES ('54eaad38-a76a-478b-b838-93625aef17f3', '2026-04-08', '/metrics/intent', 'GET', 99, 0, 2369.08, 6.9991, 334.811, '2026-04-08 19:34:18.000000', '2026-04-08 22:57:03.000000');
INSERT INTO `api_metrics` VALUES ('5581a455-c1fb-467c-9911-c466970ecfa4', '2026-04-07', '/auth/me', 'OPTIONS', 28, 0, 149.594, 0.1868, 115.941, '2026-04-07 15:06:03.000000', '2026-04-07 23:43:51.000000');
INSERT INTO `api_metrics` VALUES ('5ae156a3-aa99-4c5b-86eb-3b17ca962f1d', '2026-04-08', '/auth/me', 'GET', 64, 0, 1426.28, 2.1208, 225.022, '2026-04-08 00:06:40.000000', '2026-04-08 22:53:06.000000');
INSERT INTO `api_metrics` VALUES ('5caf373c-f6c7-4ad8-87d4-86e40bf51706', '2026-04-08', '/chat-service/sessions/my', 'GET', 77, 0, 1301.16, 6.0127, 79.1803, '2026-04-08 00:06:57.000000', '2026-04-08 22:09:25.000000');
INSERT INTO `api_metrics` VALUES ('5f15e9ce-9a69-4863-b2ed-f577b4f1c82b', '2026-04-09', '/chat-service/sessions/{id}/messages', 'OPTIONS', 14, 0, 6.3187, 0.1973, 1.8266, '2026-04-09 03:23:16.000000', '2026-04-09 16:34:15.000000');
INSERT INTO `api_metrics` VALUES ('60681533-f075-4d9a-acb3-288866dc3f3e', '2026-04-09', '/metrics/intent', 'GET', 336, 0, 8863.04, 6.3118, 526.238, '2026-04-09 00:05:30.000000', '2026-04-09 16:31:38.000000');
INSERT INTO `api_metrics` VALUES ('62b0240a-0205-4353-a524-9d3954246611', '2026-04-07', '/chat/', 'POST', 51, 0, 1026580, 3254.5, 77048.3, '2026-04-07 15:06:59.000000', '2026-04-07 23:50:14.000000');
INSERT INTO `api_metrics` VALUES ('64ce8466-109d-4ddd-a550-02f4ac33b066', '2026-04-08', '/metrics/intent/annotate', 'POST', 7, 0, 153.933, 16.1979, 28.6944, '2026-04-08 22:16:13.000000', '2026-04-08 22:16:20.000000');
INSERT INTO `api_metrics` VALUES ('64e57e72-1a90-4668-b65e-96e87926ba2a', '2026-04-08', '/chat-service/sessions/waiting', 'GET', 877, 0, 6302.63, 1.0794, 95.7057, '2026-04-08 00:06:49.000000', '2026-04-08 22:11:22.000000');
INSERT INTO `api_metrics` VALUES ('65d00f2f-768f-4d81-a17a-8ad7ca489454', '2026-04-09', '/chat/', 'OPTIONS', 3, 0, 7.236, 0.5203, 4.635, '2026-04-09 03:23:26.000000', '2026-04-09 16:33:40.000000');
INSERT INTO `api_metrics` VALUES ('69d29f2d-0403-4953-8817-783487812cc8', '2026-04-08', '/dashboard/recent-activities', 'GET', 40, 0, 2068.93, 22.5402, 108.221, '2026-04-08 18:02:00.000000', '2026-04-08 22:43:48.000000');
INSERT INTO `api_metrics` VALUES ('6d90b40c-7c6c-490b-a339-9c83dcf97653', '2026-04-08', '/chat-service/sessions', 'POST', 18, 0, 1039, 15.3781, 291.42, '2026-04-08 00:07:14.000000', '2026-04-08 16:00:16.000000');
INSERT INTO `api_metrics` VALUES ('6eef038d-9888-4b70-99e7-576e371fdca8', '2026-04-09', '/chat-service/sessions/my', 'GET', 12, 0, 200.902, 7.2064, 44.0331, '2026-04-09 01:59:35.000000', '2026-04-09 16:34:23.000000');
INSERT INTO `api_metrics` VALUES ('719e58b1-f533-4c5d-a2d3-7df4809c642a', '2026-04-08', '/chat/', 'POST', 10, 0, 127436, 2719.54, 38905, '2026-04-08 00:08:10.000000', '2026-04-08 22:15:56.000000');
INSERT INTO `api_metrics` VALUES ('71f5569b-c749-4b13-abca-7241e9ba996b', '2026-04-08', '/auth/register', 'POST', 1, 0, 317.993, 317.993, 317.993, '2026-04-08 22:05:29.000000', '2026-04-08 22:05:29.000000');
INSERT INTO `api_metrics` VALUES ('788f5791-cdcc-4848-a037-47eb01752dea', '2026-04-07', '/tickets/admin/all', 'GET', 701, 0, 22436.6, 2.2793, 1221.03, '2026-04-07 15:05:04.000000', '2026-04-07 23:51:49.000000');
INSERT INTO `api_metrics` VALUES ('7d18dc81-2c9e-4099-86b1-42aeb43609e1', '2026-04-09', '/dashboard/stats', 'GET', 68, 0, 3400.05, 16.6578, 236.327, '2026-04-09 00:05:28.000000', '2026-04-09 16:31:05.000000');
INSERT INTO `api_metrics` VALUES ('7d2fd0c4-4611-4608-953c-0559a4335b9a', '2026-04-07', '/chat-service/sessions', 'OPTIONS', 15, 0, 4.7275, 0.1863, 0.5594, '2026-04-07 18:42:51.000000', '2026-04-07 23:50:25.000000');
INSERT INTO `api_metrics` VALUES ('7ded2d33-2c20-406a-8781-0594c98026aa', '2026-04-08', '/knowledge/', 'GET', 49, 0, 532.982, 5.0375, 129.061, '2026-04-08 00:17:15.000000', '2026-04-08 22:56:48.000000');
INSERT INTO `api_metrics` VALUES ('818ebd3c-b010-4a0a-8a83-bbfc8319e150', '2026-04-08', '/metrics/errors', 'GET', 98, 0, 3833.66, 14.8136, 457.059, '2026-04-08 19:34:18.000000', '2026-04-08 22:57:03.000000');
INSERT INTO `api_metrics` VALUES ('89132236-bc5f-4ea7-90ea-08f75c0bb7a7', '2026-04-07', '/chat-service/sessions', 'POST', 32, 0, 2119.35, 7.5527, 126.052, '2026-04-07 18:42:51.000000', '2026-04-07 23:50:25.000000');
INSERT INTO `api_metrics` VALUES ('89a6bd97-47a6-4ddc-a733-e1db94ee93c6', '2026-04-07', '/chat-service/ai-messages', 'OPTIONS', 7, 0, 23.502, 0.2304, 20.8975, '2026-04-07 22:07:00.000000', '2026-04-07 23:46:29.000000');
INSERT INTO `api_metrics` VALUES ('8bbabdca-e756-489e-97ce-4c513468d25e', '2026-04-07', '/knowledge/{id}/documents', 'GET', 53, 0, 4007.78, 16.8581, 1188.37, '2026-04-07 15:08:46.000000', '2026-04-07 18:40:10.000000');
INSERT INTO `api_metrics` VALUES ('8c8b0a16-960b-4a7e-9e01-26396bc2b4b2', '2026-04-07', '/knowledge/{id}', 'DELETE', 3, 0, 815.91, 82.2999, 451.861, '2026-04-07 17:22:40.000000', '2026-04-07 18:04:46.000000');
INSERT INTO `api_metrics` VALUES ('917ee366-43fa-4f60-97e2-8ea2d908c565', '2026-04-09', '/metrics/websocket', 'GET', 337, 0, 16858.5, 6.666, 623.479, '2026-04-09 00:05:30.000000', '2026-04-09 16:31:38.000000');
INSERT INTO `api_metrics` VALUES ('93c6bd52-9f62-46c7-ae45-0c54ce8a62e3', '2026-04-08', '/tickets/admin/all', 'GET', 593, 0, 8220.18, 1.2921, 345.249, '2026-04-08 00:06:49.000000', '2026-04-08 23:14:06.000000');
INSERT INTO `api_metrics` VALUES ('93dc9880-4013-45b4-9acc-bcad8a5cb7c2', '2026-04-07', '/chat/clear-history', 'POST', 9, 0, 130.236, 6.7307, 29.1508, '2026-04-07 17:16:48.000000', '2026-04-07 17:59:32.000000');
INSERT INTO `api_metrics` VALUES ('9450491e-39b4-4231-b810-c5f6c8a30bc2', '2026-04-08', '/dashboard/stats', 'GET', 40, 0, 1506.73, 16.273, 104.887, '2026-04-08 18:02:00.000000', '2026-04-08 22:43:48.000000');
INSERT INTO `api_metrics` VALUES ('97769595-42b0-4d17-9ef0-d834ce3ad813', '2026-04-08', '/chat-service/ai-messages', 'GET', 25, 0, 409.857, 6.3706, 42.9352, '2026-04-08 00:06:40.000000', '2026-04-08 22:09:35.000000');
INSERT INTO `api_metrics` VALUES ('9e4964e7-0e33-434e-b183-1fadb07a64ab', '2026-04-08', '/users/', 'GET', 41, 0, 1115.05, 5.3579, 363.981, '2026-04-08 18:04:08.000000', '2026-04-08 22:56:48.000000');
INSERT INTO `api_metrics` VALUES ('9f87c6c4-055a-4b7c-a16a-260a06df382a', '2026-04-08', '/metrics/intent/sample-stats', 'GET', 18, 0, 286.405, 10.7226, 35.5685, '2026-04-08 22:08:14.000000', '2026-04-08 22:56:55.000000');
INSERT INTO `api_metrics` VALUES ('a0b48e8c-0223-45c2-a18f-af4dbecbb9be', '2026-04-09', '/tickets/', 'GET', 24, 0, 205.69, 6.4525, 12.0038, '2026-04-09 01:59:49.000000', '2026-04-09 16:31:22.000000');
INSERT INTO `api_metrics` VALUES ('a31c7c99-b604-4bab-879e-f6f3728855a4', '2026-04-09', '/chat-service/sessions', 'POST', 11, 0, 280.47, 8.3298, 64.574, '2026-04-09 16:03:09.000000', '2026-04-09 16:34:15.000000');
INSERT INTO `api_metrics` VALUES ('a9388884-df12-4220-9ed3-5c498b0faf04', '2026-04-07', '/chat-service/sessions/{id}/messages', 'GET', 472, 0, 12030.2, 8.1727, 567.772, '2026-04-07 18:45:56.000000', '2026-04-07 23:50:54.000000');
INSERT INTO `api_metrics` VALUES ('ac1a6037-67f7-40bb-b8f4-1e508c5e4944', '2026-04-09', '/metrics/intent/sample', 'GET', 25, 0, 281.161, 6.7804, 20.9673, '2026-04-09 02:52:25.000000', '2026-04-09 14:22:51.000000');
INSERT INTO `api_metrics` VALUES ('b0880f5f-2f01-445c-ab9d-e1d2fd6a8e8d', '2026-04-09', '/metrics/intent/trend', 'GET', 331, 0, 14566.5, 10.3707, 387.486, '2026-04-09 00:24:00.000000', '2026-04-09 16:31:38.000000');
INSERT INTO `api_metrics` VALUES ('b1f22b5b-3d7f-48d2-b47d-7ecb8db13fa2', '2026-04-07', '/users/', 'GET', 8, 0, 257.401, 12.4271, 50.7521, '2026-04-07 15:05:15.000000', '2026-04-07 20:19:53.000000');
INSERT INTO `api_metrics` VALUES ('b53ab132-54b6-4c68-864f-6882ce9e9c76', '2026-04-07', '/auth/login', 'POST', 62, 0, 21148.2, 251.011, 672.129, '2026-04-07 15:05:03.000000', '2026-04-07 23:49:54.000000');
INSERT INTO `api_metrics` VALUES ('b6ca8ff1-5efe-428b-acb0-51810e05ff74', '2026-04-08', '/metrics/intent/sample', 'GET', 1, 0, 41.9727, 41.9727, 41.9727, '2026-04-08 22:15:52.000000', '2026-04-08 22:15:52.000000');
INSERT INTO `api_metrics` VALUES ('ba99799c-49fc-4804-a7df-fd5c710360c2', '2026-04-07', '/chat-service/agent/offline', 'POST', 6, 0, 148.986, 16.9434, 39.2007, '2026-04-07 18:46:35.000000', '2026-04-07 20:52:24.000000');
INSERT INTO `api_metrics` VALUES ('c422a12a-67c7-4361-8bce-def2da7b3dd9', '2026-04-09', '/metrics/api', 'GET', 337, 0, 16871.5, 9.8301, 405.511, '2026-04-09 00:05:30.000000', '2026-04-09 16:31:38.000000');
INSERT INTO `api_metrics` VALUES ('c8a69d2b-bd7f-4159-8254-71cf5e48ee54', '2026-04-07', '/knowledge/', 'POST', 3, 0, 11086.5, 3501.93, 3926.51, '2026-04-07 17:22:58.000000', '2026-04-07 18:05:20.000000');
INSERT INTO `api_metrics` VALUES ('cc7bbe32-b4e8-431f-aea1-6ee257af8e51', '2026-04-07', '/knowledge/{id}/documents/{id}', 'DELETE', 7, 0, 261.667, 20.6732, 103.732, '2026-04-07 15:58:45.000000', '2026-04-07 18:40:09.000000');
INSERT INTO `api_metrics` VALUES ('cd0bba2a-bef3-4f44-a8e3-44680e566948', '2026-04-09', '/auth/login', 'POST', 24, 0, 8271.68, 247.199, 503.864, '2026-04-09 00:05:28.000000', '2026-04-09 16:33:47.000000');
INSERT INTO `api_metrics` VALUES ('cd2a400e-6042-463c-a021-76e688c9d313', '2026-04-08', '/chat-service/ai-messages', 'OPTIONS', 16, 0, 5.2465, 0.1945, 0.6286, '2026-04-08 00:06:40.000000', '2026-04-08 22:09:44.000000');
INSERT INTO `api_metrics` VALUES ('cda65be3-f93a-4743-a91a-16a74c22bfed', '2026-04-08', '/auth/refresh', 'POST', 11, 0, 8288.4, 0.9206, 7227.65, '2026-04-08 00:06:49.000000', '2026-04-08 23:14:06.000000');
INSERT INTO `api_metrics` VALUES ('cde63324-e195-4b45-a346-23f6886c31b0', '2026-04-09', '/dashboard/ticket-categories', 'GET', 68, 0, 4631.08, 14.6268, 272.477, '2026-04-09 00:05:28.000000', '2026-04-09 16:31:05.000000');
INSERT INTO `api_metrics` VALUES ('ce259a2e-9c95-41be-8720-ecc11f18efdc', '2026-04-07', '/tickets/', 'GET', 4, 0, 53.1031, 10.3838, 16.2373, '2026-04-07 15:05:12.000000', '2026-04-07 20:21:59.000000');
INSERT INTO `api_metrics` VALUES ('cf48655f-2fba-4896-8607-ccb144ee7d4a', '2026-04-09', '/chat-service/agent/offline', 'POST', 2, 0, 30.5614, 13.2568, 17.3046, '2026-04-09 01:59:37.000000', '2026-04-09 14:26:46.000000');
INSERT INTO `api_metrics` VALUES ('d1494b5a-fb7a-42e0-a2b3-56b28a8f9277', '2026-04-09', '/chat-service/sessions/{id}/close', 'POST', 2, 0, 46.268, 19.7338, 26.5342, NULL, '2026-04-09 16:34:23.000000');
INSERT INTO `api_metrics` VALUES ('d189ecb0-1b51-46b8-8ff4-d99522d109bd', '2026-04-07', '/chat-service/sessions/{id}/accept', 'POST', 1, 0, 60.0638, 60.0638, 60.0638, '2026-04-07 22:19:53.000000', '2026-04-07 22:19:53.000000');
INSERT INTO `api_metrics` VALUES ('d27405af-2dbd-4436-abb4-2eb3811aba1d', '2026-04-09', '/chat-service/ai-messages', 'POST', 15, 0, 267.615, 5.5133, 47.566, '2026-04-09 03:23:27.000000', '2026-04-09 16:34:35.000000');
INSERT INTO `api_metrics` VALUES ('d955ec78-0f80-4acf-b8bf-ca6f2493028b', '2026-04-09', '/metrics/intent/annotate', 'POST', 5, 0, 118.45, 22.0796, 25.435, '2026-04-09 03:32:35.000000', '2026-04-09 13:56:11.000000');
INSERT INTO `api_metrics` VALUES ('d99b566b-e4ab-4720-b80a-a3db1cb16a59', '2026-04-09', '/chat-service/sessions/waiting', 'GET', 309, 0, 3283.67, 1.5361, 193.544, '2026-04-09 01:59:35.000000', '2026-04-09 16:36:25.000000');
INSERT INTO `api_metrics` VALUES ('e20eba5d-b249-4a65-8985-5a199c03393e', '2026-04-09', '/metrics/intent/sample-stats', 'GET', 227, 0, 7633.54, 6.0792, 171.673, '2026-04-09 00:05:40.000000', '2026-04-09 16:31:38.000000');
INSERT INTO `api_metrics` VALUES ('e236528d-19b6-4931-acb8-6c34144f20d2', '2026-04-07', '/tickets/{id}/messages', 'GET', 4, 0, 60.0261, 10.998, 18.2998, '2026-04-07 20:27:15.000000', '2026-04-07 20:34:19.000000');
INSERT INTO `api_metrics` VALUES ('e952a0f6-fee8-4eef-b360-cadc105c7369', '2026-04-07', '/chat-service/ai-messages', 'GET', 42, 0, 968.394, 9.0739, 226.299, '2026-04-07 22:07:00.000000', '2026-04-07 23:49:54.000000');
INSERT INTO `api_metrics` VALUES ('ea2e7b03-e7a4-4dd7-8301-19d1d67b36b7', '2026-04-09', '/metrics/errors', 'GET', 336, 0, 16293.2, 3.5366, 342.934, '2026-04-09 00:05:30.000000', '2026-04-09 16:31:38.000000');
INSERT INTO `api_metrics` VALUES ('ebb77f6e-1a80-4083-b72f-0736b32044b1', '2026-04-09', '/users/', 'GET', 52, 0, 1858.19, 6.7064, 381.189, '2026-04-09 00:27:01.000000', '2026-04-09 16:31:37.000000');
INSERT INTO `api_metrics` VALUES ('ecc0a69a-c83e-43c0-bed7-3344fa4f7235', '2026-04-08', '/chat-service/sessions/{id}/close', 'POST', 16, 0, 383.338, 18.9869, 32.1123, '2026-04-08 00:06:59.000000', '2026-04-08 22:09:25.000000');
INSERT INTO `api_metrics` VALUES ('ece6eb79-8407-4c24-a68b-5df5cf434d7c', '2026-04-09', '/chat/', 'POST', 8, 0, 83396.3, 418.364, 19566.6, '2026-04-09 03:23:39.000000', '2026-04-09 16:34:35.000000');
INSERT INTO `api_metrics` VALUES ('ed89158a-7c59-4522-974b-1b029c3eb9ed', '2026-04-09', '/auth/me', 'GET', 71, 0, 2741.71, 2.7275, 243.559, '2026-04-09 00:05:28.000000', '2026-04-09 16:34:41.000000');
INSERT INTO `api_metrics` VALUES ('ee5f69ce-f69c-45f0-bb71-cffdc3f57b81', '2026-04-07', '/chat-service/sessions/waiting', 'GET', 959, 0, 17416.2, 1.1285, 580.643, '2026-04-07 15:05:49.000000', '2026-04-07 23:51:49.000000');
INSERT INTO `api_metrics` VALUES ('eeb38a9f-17bc-4bfb-82d3-45041a2bf42d', '2026-04-08', '/chat-service/sessions/{id}/messages', 'GET', 75, 0, 1142.3, 7.6032, 37.6723, '2026-04-08 00:06:41.000000', '2026-04-08 22:09:36.000000');
INSERT INTO `api_metrics` VALUES ('f007c636-eb99-4f26-9220-cfedd463773c', '2026-04-08', '/chat-service/agent/online', 'POST', 21, 0, 444.416, 8.9877, 120.767, '2026-04-08 00:06:57.000000', '2026-04-08 22:09:22.000000');
INSERT INTO `api_metrics` VALUES ('f04f6a19-c721-4335-9308-18f3fe5f60ae', '2026-04-08', '/chat/', 'OPTIONS', 3, 0, 5.9225, 1.0417, 2.6905, '2026-04-08 00:08:05.000000', '2026-04-08 22:09:44.000000');
INSERT INTO `api_metrics` VALUES ('f0c396c5-52f3-40cc-b2de-b2dc2fac2d39', '2026-04-07', '/knowledge/{id}/documents', 'POST', 11, 0, 4761.83, 27.2738, 1490.81, '2026-04-07 15:07:52.000000', '2026-04-07 18:39:39.000000');
INSERT INTO `api_metrics` VALUES ('f66d8e79-62b1-46e3-94c5-11e28574c3d4', '2026-04-07', '/knowledge/', 'GET', 78, 0, 1677.88, 9.1258, 361.125, '2026-04-07 15:05:15.000000', '2026-04-07 23:35:54.000000');
INSERT INTO `api_metrics` VALUES ('f8c098e1-f9d8-4994-a605-f5ec9716d379', '2026-04-07', '/chat-service/sessions/{id}/close', 'POST', 23, 0, 1387.14, 29.1216, 525.389, '2026-04-07 18:45:59.000000', '2026-04-07 23:43:51.000000');
INSERT INTO `api_metrics` VALUES ('fd9c4e38-3af2-4759-9bef-f5b151dad912', '2026-04-08', '/chat-service/ai-messages', 'POST', 20, 0, 358.887, 10.1873, 44.6815, '2026-04-08 00:08:05.000000', '2026-04-08 22:15:56.000000');

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
  `read_at` datetime(6) NULL DEFAULT NULL,
  `created_at` datetime(6) NULL DEFAULT NULL,
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
INSERT INTO `chat_messages` VALUES ('4960cb2a-5b50-4eec-803e-a6afb977df49', 'fd6f6ac0-8d8f-4219-bcfb-53967fa55c6f', NULL, 'system', '客服 admin 已接入会话', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-09 16:34:15.672668');
INSERT INTO `chat_messages` VALUES ('4cb8ce33-cb6f-44f4-b338-a2255984ce87', NULL, NULL, 'ai', '📋 您的所有工单（共 8 个）\n\n状态分布：待处理: 6 | 处理中: 2\n\n工单列表：\n1. TKT-20260409135554 | 订单支付失败，系统持续显示错误 | 待处理\n2. TKT-20260409135445 | 订单无法支付，持续显示错误 | 待处理\n3. TKT-20260409135307 | 订单支付失败，持续显示错误 | 待处理\n4. TKT-20260409032815 | 订单支付失败，持续显示错误 | 待处理\n5. TKT-20260409032339 | 订单支付失败并持续报错 | 待处理\n6. TKT-20260408221556 | 订单无法支付，一直显示错误 | 待处理\n7. TKT-20260404141650 | 订单无法支付，一直显示错误 | 处理中\n8. TKT-20260404113551 | 订单支付失败，系统持续显示错误 | 处理中\n\n💡 提示：如需查看某个工单的详细信息，请提供工单编号（如 TKT-20260409135554）\n', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-09 16:34:35.550223');
INSERT INTO `chat_messages` VALUES ('5300c10a-cd01-40b1-b0ea-9e2ec816ae8f', NULL, '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '工单列表', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-09 16:33:52.789247');
INSERT INTO `chat_messages` VALUES ('62c6c4b3-1fe3-4728-aa0a-52fb43483c2b', NULL, NULL, 'ai', '📋 您的所有工单（共 8 个）\n\n状态分布：待处理: 6 | 处理中: 2\n\n工单列表：\n1. TKT-20260409135554 | 订单支付失败，系统持续显示错误 | 待处理\n2. TKT-20260409135445 | 订单无法支付，持续显示错误 | 待处理\n3. TKT-20260409135307 | 订单支付失败，持续显示错误 | 待处理\n4. TKT-20260409032815 | 订单支付失败，持续显示错误 | 待处理\n5. TKT-20260409032339 | 订单支付失败并持续报错 | 待处理\n6. TKT-20260408221556 | 订单无法支付，一直显示错误 | 待处理\n7. TKT-20260404141650 | 订单无法支付，一直显示错误 | 处理中\n8. TKT-20260404113551 | 订单支付失败，系统持续显示错误 | 处理中\n\n💡 提示：如需查看某个工单的详细信息，请提供工单编号（如 TKT-20260409135554）\n', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-09 16:33:58.883164');
INSERT INTO `chat_messages` VALUES ('700a7ccb-28cd-4495-b794-f03f870174bb', NULL, '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '工单列表', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-09 16:34:30.722442');
INSERT INTO `chat_messages` VALUES ('cfa9a889-15ff-41a3-997e-f08018a8df35', 'fd6f6ac0-8d8f-4219-bcfb-53967fa55c6f', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '3器e', 'text', NULL, 0, NULL, '2026-04-09 16:34:18.850275');
INSERT INTO `chat_messages` VALUES ('d2c2ca45-b814-46f3-84c5-452019bdbbba', 'b6fc9520-0cac-4119-a462-5bc3bc40dcc8', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', 'waer', 'text', NULL, 0, NULL, '2026-04-09 16:32:05.749777');
INSERT INTO `chat_messages` VALUES ('d68a22a3-8b4c-4e13-bfae-1ab18dd6efae', 'b6fc9520-0cac-4119-a462-5bc3bc40dcc8', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', 'asdf', 'text', NULL, 0, NULL, '2026-04-09 16:32:18.655888');
INSERT INTO `chat_messages` VALUES ('eec0ee33-ec15-4373-9107-f2db8624d858', 'b6fc9520-0cac-4119-a462-5bc3bc40dcc8', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '工单列表', 'text', NULL, 0, NULL, '2026-04-09 16:32:30.103097');
INSERT INTO `chat_messages` VALUES ('fb32a5b3-8ab8-4c5f-a2fd-cd787d381210', 'b6fc9520-0cac-4119-a462-5bc3bc40dcc8', NULL, 'system', '客服 admin 已接入会话', 'text', '9945a367-2c08-48e2-b172-ae16deeabf00', 0, NULL, '2026-04-09 16:32:02.358676');

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
  `created_at` datetime(6) NULL DEFAULT NULL,
  `connected_at` datetime(6) NULL DEFAULT NULL,
  `closed_at` datetime(6) NULL DEFAULT NULL,
  `last_message_at` datetime(6) NULL DEFAULT NULL,
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
INSERT INTO `chat_sessions` VALUES ('b6fc9520-0cac-4119-a462-5bc3bc40dcc8', '9945a367-2c08-48e2-b172-ae16deeabf00', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', NULL, 'closed', 'general', '客户请求转人工', '2026-04-09 16:32:02.334175', '2026-04-09 16:32:02.344705', '2026-04-09 16:33:23.596294', '2026-04-09 16:32:30.101600');
INSERT INTO `chat_sessions` VALUES ('fd6f6ac0-8d8f-4219-bcfb-53967fa55c6f', '9945a367-2c08-48e2-b172-ae16deeabf00', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', NULL, 'closed', 'general', '客户请求转人工', '2026-04-09 16:34:15.642446', '2026-04-09 16:34:15.656906', '2026-04-09 16:34:23.075137', '2026-04-09 16:34:18.836388');

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
  `created_at` datetime(6) NULL DEFAULT NULL,
  `updated_at` datetime(6) NULL DEFAULT NULL,
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
INSERT INTO `documents` VALUES ('1bf3ec19-37ac-4980-ad15-4eb9df7b14a0', 'd737e422-0ef8-4d25-b6cc-67a837db23bd', '个人简历-2026最新版.docx', '个人简历-2026最新版.docx', 'd737e422-0ef8-4d25-b6cc-67a837db23bd/个人简历-2026最新版.docx', '.docx', 43799, 17, 'indexed', NULL, '2026-04-07 10:14:21.000000', '2026-04-07 10:14:25.000000', NULL);
INSERT INTO `documents` VALUES ('2d84a877-2ada-47be-aadb-df861030e9f2', 'd737e422-0ef8-4d25-b6cc-67a837db23bd', '胥腾龙-个人简历-202603最新版.pdf', '胥腾龙-个人简历-202603最新版.pdf', 'd737e422-0ef8-4d25-b6cc-67a837db23bd/胥腾龙-个人简历-202603最新版.pdf', '.pdf', 556094, 20, 'indexed', NULL, '2026-04-07 10:05:29.000000', '2026-04-07 10:05:54.000000', NULL);
INSERT INTO `documents` VALUES ('a8618182-fcba-46f7-a683-bb2b20075c6f', '5caa3838-0145-40e0-bff1-43f040a71e62', '胥腾龙-个人简历-202603最新版.pdf', '胥腾龙-个人简历-202603最新版.pdf', '5caa3838-0145-40e0-bff1-43f040a71e62/胥腾龙-个人简历-202603最新版.pdf', '.pdf', 556094, 24, 'indexed', NULL, '2026-04-07 07:07:52.000000', '2026-04-07 07:07:57.000000', NULL);
INSERT INTO `documents` VALUES ('e38d562f-07de-46e5-a3b9-e84b409eaf74', '5caa3838-0145-40e0-bff1-43f040a71e62', '胥腾龙-个人简历-202603最新版.pdf', '胥腾龙-个人简历-202603最新版.pdf', '5caa3838-0145-40e0-bff1-43f040a71e62/胥腾龙-个人简历-202603最新版.pdf', '.pdf', 556094, 24, 'indexed', NULL, '2026-04-05 13:54:31.000000', '2026-04-05 13:54:37.000000', NULL);

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
  `created_at` datetime(6) NULL DEFAULT NULL,
  `updated_at` datetime(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_date_type_endpoint`(`metric_date` ASC, `error_type` ASC, `endpoint` ASC) USING BTREE,
  INDEX `idx_metric_date`(`metric_date` ASC) USING BTREE,
  INDEX `idx_error_type`(`error_type` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '错误统计表 - 按天聚合' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of error_metrics
-- ----------------------------
INSERT INTO `error_metrics` VALUES ('0908a877-2507-4a08-8919-694589455751', '2026-04-08', 'HTTP403', '/dashboard/ticket-trends', 4, '2026-04-08 22:05:36.000000', '2026-04-08 22:05:43.000000');
INSERT INTO `error_metrics` VALUES ('18ccad38-8304-41f1-980d-30e675d06494', '2026-04-09', 'HTTP422', '/metrics/intent/trend', 8, '2026-04-09 00:53:40.000000', '2026-04-09 01:52:10.000000');
INSERT INTO `error_metrics` VALUES ('2391cb38-a114-4c60-85c6-157fd6ca32da', '2026-04-08', 'HTTP403', '/dashboard/stats', 4, '2026-04-08 22:05:36.000000', '2026-04-08 22:05:43.000000');
INSERT INTO `error_metrics` VALUES ('254cd171-6815-4ac0-9ea1-dd7bb1a01baf', '2026-04-09', 'HTTP401', '/auth/me', 3, '2026-04-09 03:23:10.000000', '2026-04-09 16:02:17.000000');
INSERT INTO `error_metrics` VALUES ('282107ec-762e-48d9-8889-6951c6ffba4f', '2026-04-07', 'HTTP500', '/chat-service/sessions', 1, '2026-04-07 22:13:40.000000', '2026-04-07 22:13:40.000000');
INSERT INTO `error_metrics` VALUES ('287d08de-3dbe-4f29-9d68-a7d675376144', '2026-04-08', 'HTTP401', '/auth/me', 5, '2026-04-08 13:42:53.000000', '2026-04-08 22:09:33.000000');
INSERT INTO `error_metrics` VALUES ('2b9c0aa0-0da9-49f5-8a4f-d656a6ac7d41', '2026-04-09', 'NameError', '/metrics/errors', 19, '2026-04-09 01:38:40.000000', '2026-04-09 01:42:56.000000');
INSERT INTO `error_metrics` VALUES ('2d72d46c-a6e9-4f78-a3c1-930e9720cda9', '2026-04-07', 'HTTP500', '/chat-service/ai-messages', 2, '2026-04-07 22:07:12.000000', '2026-04-07 22:07:17.000000');
INSERT INTO `error_metrics` VALUES ('332c6402-4e55-4c95-839a-215a7eaf58ec', '2026-04-07', 'HTTP401', '/chat-service/sessions', 2, '2026-04-07 18:42:51.000000', '2026-04-07 20:16:29.000000');
INSERT INTO `error_metrics` VALUES ('34ec5c04-5086-4dda-bf46-253a7dfee5b2', '2026-04-09', 'HTTP401', '/users/', 2, '2026-04-09 00:36:43.000000', '2026-04-09 00:36:44.000000');
INSERT INTO `error_metrics` VALUES ('39d28c88-67fc-42a8-8ade-06b9cd94c509', '2026-04-08', 'HTTP422', '/metrics/errors', 3, '2026-04-08 22:54:04.000000', '2026-04-08 22:55:42.000000');
INSERT INTO `error_metrics` VALUES ('3d812bc1-b933-4433-86a2-c49a6d0df7dd', '2026-04-09', 'HTTP422', '/metrics/intent/sample-stats', 3, '2026-04-09 13:21:41.000000', '2026-04-09 13:21:58.000000');
INSERT INTO `error_metrics` VALUES ('3deb1820-03e4-48e6-927c-c996e184670b', '2026-04-08', 'HTTP401', '/chat-service/sessions/waiting', 10, '2026-04-08 00:06:49.000000', '2026-04-08 22:11:22.000000');
INSERT INTO `error_metrics` VALUES ('3dee5db0-dc8d-4ed1-9bb1-08d506ee59ae', '2026-04-07', 'HTTP403', '/users/', 4, '2026-04-07 15:05:15.000000', '2026-04-07 20:19:53.000000');
INSERT INTO `error_metrics` VALUES ('3e63a2e0-6904-42c6-a036-62d369c90ecd', '2026-04-09', 'HTTP422', '/auth/refresh', 20, '2026-04-09 00:36:44.000000', '2026-04-09 15:46:04.000000');
INSERT INTO `error_metrics` VALUES ('44edd88a-2241-49e7-a25c-b1f930cabc75', '2026-04-09', 'HTTP422', '/metrics/api', 9, '2026-04-09 00:05:48.000000', '2026-04-09 01:52:10.000000');
INSERT INTO `error_metrics` VALUES ('484d1fa8-1114-4554-9cfb-9d85e5eb151f', '2026-04-09', 'HTTP401', '/chat-service/sessions/waiting', 2, '2026-04-09 02:12:25.000000', '2026-04-09 14:56:24.000000');
INSERT INTO `error_metrics` VALUES ('4e356fc0-c83c-466e-b106-edec55bbcda7', '2026-04-07', 'HTTP401', '/chat-service/sessions/waiting', 9, '2026-04-07 18:50:57.000000', '2026-04-07 22:51:49.000000');
INSERT INTO `error_metrics` VALUES ('506e73f0-1980-44e4-9454-48c2f50cc0e0', '2026-04-07', 'HTTP422', '/auth/refresh', 7, '2026-04-07 15:58:49.000000', '2026-04-07 22:51:49.000000');
INSERT INTO `error_metrics` VALUES ('561d4ab2-506b-4d3d-a8df-58dc6d6f785e', '2026-04-08', 'HTTP422', '/metrics/intent', 4, '2026-04-08 22:50:44.000000', '2026-04-08 22:55:42.000000');
INSERT INTO `error_metrics` VALUES ('64aa1514-e719-4619-bf2f-a076f8161ed7', '2026-04-08', 'HTTP403', '/dashboard/recent-activities', 4, '2026-04-08 22:05:36.000000', '2026-04-08 22:05:43.000000');
INSERT INTO `error_metrics` VALUES ('68f77307-e8f9-4ea5-bae1-4715413a2493', '2026-04-09', 'HTTP401', '/tickets/admin/all', 10, '2026-04-09 00:36:43.000000', '2026-04-09 15:46:04.000000');
INSERT INTO `error_metrics` VALUES ('6bbf7385-6912-44ea-8bf3-eac9c5dc5204', '2026-04-09', 'HTTP401', '/metrics/intent/trend', 2, '2026-04-09 00:36:43.000000', '2026-04-09 00:36:44.000000');
INSERT INTO `error_metrics` VALUES ('6f56854f-9e11-4656-beb3-6cb982437d31', '2026-04-07', 'HTTP404', '/chat-service/sessions/{id}/messages', 1, '2026-04-07 19:43:26.000000', '2026-04-07 19:43:26.000000');
INSERT INTO `error_metrics` VALUES ('7ad3be34-a567-4151-b5ef-15176d55714b', '2026-04-08', 'HTTP401', '/tickets/admin/all', 9, '2026-04-08 00:06:49.000000', '2026-04-08 23:14:06.000000');
INSERT INTO `error_metrics` VALUES ('8559d58c-4bf4-40e8-809d-9fd7350710c9', '2026-04-09', 'HTTP422', '/metrics/errors', 9, '2026-04-09 00:05:48.000000', '2026-04-09 01:52:10.000000');
INSERT INTO `error_metrics` VALUES ('8974bcf5-2765-4e75-bd5d-0711e7429b86', '2026-04-09', 'TypeError', '/metrics/intent/sample-stats', 11, '2026-04-09 00:05:40.000000', '2026-04-09 02:41:10.000000');
INSERT INTO `error_metrics` VALUES ('8ad8a2c2-bacd-46bf-b371-c6b1bbdebb0a', '2026-04-07', 'HTTP400', '/knowledge/{id}/documents', 1, '2026-04-07 18:14:13.000000', '2026-04-07 18:14:13.000000');
INSERT INTO `error_metrics` VALUES ('8db56b54-b962-4932-bf84-f8e980034c6d', '2026-04-07', 'HTTP401', '/chat/clear-history', 3, '2026-04-07 17:16:48.000000', '2026-04-07 17:55:01.000000');
INSERT INTO `error_metrics` VALUES ('919186a3-07b5-498e-85cf-c63cd36290a1', '2026-04-09', 'NameError', '/chat-service/sessions/waiting', 2, '2026-04-09 16:09:30.000000', '2026-04-09 16:10:30.000000');
INSERT INTO `error_metrics` VALUES ('91a603cf-31ed-4916-a18e-7aac5ff61da5', '2026-04-08', 'HTTP403', '/users/', 20, '2026-04-08 18:04:08.000000', '2026-04-08 22:05:41.000000');
INSERT INTO `error_metrics` VALUES ('9396b31b-4fc1-4e5b-94ba-05721dfdd4d0', '2026-04-09', 'HTTP401', '/metrics/api', 2, '2026-04-09 00:36:43.000000', '2026-04-09 00:36:44.000000');
INSERT INTO `error_metrics` VALUES ('98c36e68-189d-4068-8b40-f6b8b1d99bd7', '2026-04-08', 'TypeError', '/metrics/intent/sample-stats', 18, '2026-04-08 22:08:14.000000', '2026-04-08 22:56:55.000000');
INSERT INTO `error_metrics` VALUES ('9bfd4109-2e18-43a7-b03c-fd09b52e6250', '2026-04-09', 'HTTP401', '/metrics/errors', 2, '2026-04-09 00:36:43.000000', '2026-04-09 00:36:44.000000');
INSERT INTO `error_metrics` VALUES ('a382a7d9-51ee-44ec-87f4-0cf5ebdb257c', '2026-04-09', 'HTTP401', '/chat/', 1, NULL, NULL);
INSERT INTO `error_metrics` VALUES ('af7e2550-4c8e-4da1-a085-fd5290a0a7ff', '2026-04-09', 'TypeError', '/chat-service/sessions/waiting', 15, '2026-04-09 16:03:25.000000', '2026-04-09 16:15:30.000000');
INSERT INTO `error_metrics` VALUES ('b7ab9134-55f3-4e97-a818-c21d69f13cc3', '2026-04-08', 'HTTP422', '/metrics/api', 3, '2026-04-08 22:54:04.000000', '2026-04-08 22:55:42.000000');
INSERT INTO `error_metrics` VALUES ('b823ea43-c936-4630-875e-1b74ed753d74', '2026-04-09', 'HTTP403', '/users/', 6, '2026-04-09 14:26:26.000000', '2026-04-09 15:15:13.000000');
INSERT INTO `error_metrics` VALUES ('bb716375-f795-4349-b11f-975fa926056c', '2026-04-09', 'HTTP401', '/metrics/intent', 2, '2026-04-09 00:36:43.000000', '2026-04-09 00:36:44.000000');
INSERT INTO `error_metrics` VALUES ('c2e93876-be54-402d-980b-9dc99ef8edbf', '2026-04-08', 'HTTP403', '/dashboard/ticket-categories', 4, '2026-04-08 22:05:36.000000', '2026-04-08 22:05:43.000000');
INSERT INTO `error_metrics` VALUES ('c4c40353-f8ad-47ad-bd67-f868cd5f381e', '2026-04-09', 'HTTP401', '/chat-service/ai-messages', 1, NULL, NULL);
INSERT INTO `error_metrics` VALUES ('cb5af29a-36c0-411e-a288-443d604025fe', '2026-04-07', 'HTTP401', '/tickets/admin/all', 6, '2026-04-07 15:58:49.000000', '2026-04-07 22:51:49.000000');
INSERT INTO `error_metrics` VALUES ('db7fa1d7-77b9-4cd7-a7a4-ba766f48f186', '2026-04-07', 'HTTP401', '/auth/me', 6, '2026-04-07 16:01:52.000000', '2026-04-07 23:19:19.000000');
INSERT INTO `error_metrics` VALUES ('dd4953bc-5ff2-4022-b034-fd599843c7f0', '2026-04-08', 'HTTP422', '/auth/refresh', 13, '2026-04-08 00:06:49.000000', '2026-04-08 23:14:06.000000');
INSERT INTO `error_metrics` VALUES ('ea04bd2a-d9ad-49f5-8adb-8d598d81360f', '2026-04-09', 'HTTP401', '/metrics/websocket', 2, '2026-04-09 00:36:44.000000', '2026-04-09 00:36:44.000000');
INSERT INTO `error_metrics` VALUES ('edcf0520-0865-4923-911d-89c20c263da3', '2026-04-09', 'HTTP422', '/metrics/intent', 9, '2026-04-09 00:05:48.000000', '2026-04-09 01:52:10.000000');
INSERT INTO `error_metrics` VALUES ('f63a59c2-d140-4997-8898-0a18d75b0b6c', '2026-04-09', 'HTTP401', '/metrics/intent/sample-stats', 1, '2026-04-09 00:36:43.000000', '2026-04-09 00:36:43.000000');

-- ----------------------------
-- Table structure for intent_classification_logs
-- ----------------------------
DROP TABLE IF EXISTS `intent_classification_logs`;
CREATE TABLE `intent_classification_logs`  (
  `id` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '日志ID (UUID)',
  `metric_date` date NOT NULL COMMENT '统计日期',
  `intent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '识别的意图',
  `user_input` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL COMMENT '用户输入内容',
  `confidence` float NULL DEFAULT 1 COMMENT '置信度',
  `is_sampled` tinyint(1) NOT NULL DEFAULT 0 COMMENT '是否被抽样',
  `is_correct` tinyint(1) NULL DEFAULT NULL COMMENT '人工标注是否正确（null表示未标注）',
  `annotated_by` varchar(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '标注人ID',
  `annotated_at` datetime(6) NULL DEFAULT NULL,
  `created_at` datetime(6) NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_metric_date`(`metric_date` ASC) USING BTREE,
  INDEX `idx_intent`(`intent` ASC) USING BTREE,
  INDEX `idx_is_sampled`(`is_sampled` ASC) USING BTREE,
  INDEX `idx_date_sampled`(`metric_date` ASC, `is_sampled` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '意图识别明细日志表 - 用于抽样标注' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of intent_classification_logs
-- ----------------------------
INSERT INTO `intent_classification_logs` VALUES ('0ca7ad9c-550a-418d-81e1-d857c700744d', '2026-04-08', 'process_ticket', 'TKT-20260404113551  工单加急', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-08 22:16:17.000000', '2026-04-08 22:12:13.000000');
INSERT INTO `intent_classification_logs` VALUES ('28f01280-2716-42aa-816a-3aa3cd070355', '2026-04-09', 'create_ticket', '我的订单无法支付，一直显示错误', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-09 13:55:25.000000', '2026-04-09 13:54:31.000000');
INSERT INTO `intent_classification_logs` VALUES ('5191d28e-f30a-434f-a2c6-06f1c7cee09b', '2026-04-09', 'create_ticket', '我的订单无法支付，一直显示错误', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-09 13:53:59.000000', '2026-04-09 13:53:00.000000');
INSERT INTO `intent_classification_logs` VALUES ('526180bd-cda9-49cd-bbab-141bdcc50780', '2026-04-09', 'query_ticket', '工单列表', 1, 0, NULL, NULL, NULL, NULL);
INSERT INTO `intent_classification_logs` VALUES ('55aa6d89-71da-4679-a899-b59e7cb44d07', '2026-04-09', 'create_ticket', '我的订单无法支付，一直显示错误', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-09 03:32:36.000000', '2026-04-09 03:28:07.000000');
INSERT INTO `intent_classification_logs` VALUES ('6337f890-c360-4313-a43f-2b3c0500fee3', '2026-04-09', 'create_ticket', '我的订单无法支付，一直显示错误', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-09 03:32:35.000000', '2026-04-09 03:23:31.000000');
INSERT INTO `intent_classification_logs` VALUES ('751f69cd-1918-4d73-89fe-574036aebe2f', '2026-04-08', 'summary', '我的工单统计', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-08 22:16:20.000000', '2026-04-08 22:15:05.000000');
INSERT INTO `intent_classification_logs` VALUES ('a2d1f3c8-45ea-453f-b57f-706563619ab7', '2026-04-09', 'query_ticket', '工单列表', 1, 0, NULL, NULL, NULL, NULL);
INSERT INTO `intent_classification_logs` VALUES ('c6e68f69-1b44-4dd6-90ff-d3687dc0257b', '2026-04-08', 'create_ticket', '我的订单无法支付，一直显示错误', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-08 22:16:15.000000', '2026-04-08 22:15:43.000000');
INSERT INTO `intent_classification_logs` VALUES ('d0399442-ed05-4d74-8bd5-53426638adcc', '2026-04-08', 'summary', '我的工单统计', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-08 22:16:19.000000', '2026-04-08 22:14:59.000000');
INSERT INTO `intent_classification_logs` VALUES ('e31659c2-7a15-4739-9769-516dfbf7ec6d', '2026-04-09', 'create_ticket', '我的订单无法支付，一直显示错误', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-09 13:56:11.000000', '2026-04-09 13:55:43.000000');
INSERT INTO `intent_classification_logs` VALUES ('e38c1cf6-626d-4219-87c8-8636c6989b00', '2026-04-08', 'query_ticket', '工单列表', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-08 22:16:14.000000', '2026-04-08 22:09:48.000000');
INSERT INTO `intent_classification_logs` VALUES ('f24f6821-6f1b-49f7-8fd1-20764c503819', '2026-04-08', 'process_ticket', 'TKT-20260404141650  工单加急', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-08 22:16:18.000000', '2026-04-08 22:10:29.000000');
INSERT INTO `intent_classification_logs` VALUES ('f54e87a0-4d13-4ae6-83c1-141215562dff', '2026-04-08', 'general', '如何使用退货功能', 1, 1, 1, '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '2026-04-08 22:16:13.000000', '2026-04-08 22:13:40.000000');

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
  `created_at` datetime(6) NULL DEFAULT NULL,
  `updated_at` datetime(6) NULL DEFAULT NULL,
  `sampled` int(11) NULL DEFAULT 0 COMMENT '抽样检查数量',
  `sampled_correct` int(11) NULL DEFAULT 0 COMMENT '抽样中正确的数量',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_date_intent`(`metric_date` ASC, `intent` ASC) USING BTREE,
  INDEX `idx_metric_date`(`metric_date` ASC) USING BTREE,
  INDEX `idx_intent`(`intent` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '意图识别统计表 - 按天聚合' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Records of intent_metrics
-- ----------------------------
INSERT INTO `intent_metrics` VALUES ('21316ae3-a4a6-40c0-9123-c129c097ecd1', '2026-04-07', 'query_ticket', 21, 0, 21, '2026-04-07 20:22:20.000000', '2026-04-07 23:50:14.000000', 0, 0);
INSERT INTO `intent_metrics` VALUES ('22c29837-84ad-4f9b-8a0a-af99f5f80222', '2026-04-08', 'general', 1, 0, 1, '2026-04-08 22:13:40.000000', '2026-04-08 22:16:13.000000', 1, 1);
INSERT INTO `intent_metrics` VALUES ('29280b8b-e880-4449-a863-0147e0928650', '2026-04-08', 'create_ticket', 1, 0, 1, '2026-04-08 22:15:43.000000', '2026-04-08 22:16:15.000000', 1, 1);
INSERT INTO `intent_metrics` VALUES ('64c489ab-d622-4d66-942f-740d72dca921', '2026-04-07', 'process_ticket', 7, 0, 7, '2026-04-07 20:22:46.000000', '2026-04-07 21:15:15.000000', 0, 0);
INSERT INTO `intent_metrics` VALUES ('6addf5ce-883d-4fb4-8287-3e3b376f4f7e', '2026-04-08', 'summary', 2, 0, 2, '2026-04-08 22:14:59.000000', '2026-04-08 22:16:20.000000', 2, 2);
INSERT INTO `intent_metrics` VALUES ('7b19ef8d-1cbf-4a92-a928-6dd07b425e6e', '2026-04-07', 'general', 23, 0, 23, '2026-04-07 15:06:27.000000', '2026-04-07 20:17:35.000000', 0, 0);
INSERT INTO `intent_metrics` VALUES ('86756819-59cf-4081-b8df-d73dab89f791', '2026-04-09', 'create_ticket', 5, 0, 5, '2026-04-09 03:23:31.000000', '2026-04-09 13:56:11.000000', 5, 5);
INSERT INTO `intent_metrics` VALUES ('952fed82-7266-45c6-a5cf-3686824110d0', '2026-04-09', 'query_ticket', 2, 0, 2, NULL, '2026-04-09 16:34:35.000000', 0, 0);
INSERT INTO `intent_metrics` VALUES ('a3e13ddb-5960-499a-831a-abb2a6eaf035', '2026-04-08', 'process_ticket', 3, 0, 3, '2026-04-08 13:43:55.000000', '2026-04-08 22:16:18.000000', 2, 2);
INSERT INTO `intent_metrics` VALUES ('b3a87c67-fad2-490c-95cb-3c91af65c5ae', '2026-04-08', 'query_ticket', 3, 0, 3, '2026-04-08 00:08:10.000000', '2026-04-08 22:16:14.000000', 1, 1);

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
  `created_at` datetime(6) NULL DEFAULT NULL,
  `updated_at` datetime(6) NULL DEFAULT NULL,
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
INSERT INTO `knowledge_bases` VALUES ('5caa3838-0145-40e0-bff1-43f040a71e62', '人事制度', NULL, 'kb_a4e3e320ed7742a1a558d4eefa9ffc25', '0912d5f2-acdd-492e-852f-0b915524cafc', 0, 'active', '2026-04-05 13:54:02.000000', '2026-04-05 13:54:02.000000', 'sentence-transformers/all-MiniLM-L6-v2', NULL);
INSERT INTO `knowledge_bases` VALUES ('d737e422-0ef8-4d25-b6cc-67a837db23bd', 'sad', NULL, 'kb_42e9eca3a6904adfb526c8b7f29748f0', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 2, 'active', '2026-04-07 10:05:20.000000', '2026-04-07 10:40:10.000000', 'sentence-transformers/all-MiniLM-L6-v2', NULL);

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
) ENGINE = InnoDB AUTO_INCREMENT = 1 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = '系统配置表' ROW_FORMAT = Dynamic;

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
INSERT INTO `ticket_messages` VALUES ('1c2f46dc-d79d-463f-ae9c-1c663d7657c1', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '【客户催促】请尽快处理此工单。原因：工单加急', 'text', 0, NULL, '2026-04-08 22:10:35');
INSERT INTO `ticket_messages` VALUES ('2b0e92e0-c116-433f-b94f-ab3477cb9eb3', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '【客户催促】请尽快处理此工单。原因：TKT-20260404141650 加急工单', 'text', 0, NULL, '2026-04-08 05:44:04');
INSERT INTO `ticket_messages` VALUES ('3f588df5-a897-45cd-b52f-571ea739bac8', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '123', 'text', 0, NULL, '2026-04-04 15:19:09');
INSERT INTO `ticket_messages` VALUES ('40600bcd-af7a-4f80-8206-a9331bc20c24', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', '你好\n', 'text', 0, NULL, '2026-04-04 14:46:57');
INSERT INTO `ticket_messages` VALUES ('5b49c2d5-73f5-4d57-b835-2ed8b9d29a38', '242b76ef-e26b-489f-99bc-bea50fe5f65d', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', '123', 'text', 0, NULL, '2026-04-04 14:58:25');
INSERT INTO `ticket_messages` VALUES ('6a916975-5c8b-417f-a114-3f3ca89a4cd2', 'cb597913-3add-4426-82fd-da3ae5506e26', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'agent', 'aaa', 'text', 0, NULL, '2026-04-04 07:11:13');
INSERT INTO `ticket_messages` VALUES ('851d161b-fa59-4e03-8c6f-bd9c6f5d79a6', '21e19979-e603-4234-a6ab-a54647fb9ad4', '9945a367-2c08-48e2-b172-ae16deeabf00', 'customer', '【客户催促】请尽快处理此工单。原因：工单加急', 'text', 0, NULL, '2026-04-08 22:12:18');
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
  `resolved_at` datetime(6) NULL DEFAULT NULL,
  `closed_at` datetime(6) NULL DEFAULT NULL,
  `created_at` datetime(6) NULL DEFAULT NULL,
  `updated_at` datetime(6) NULL DEFAULT NULL,
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
INSERT INTO `tickets` VALUES ('0552a174-f0cc-4053-a07d-5348aab4223b', 'TKT-20260409135445', '订单无法支付，持续显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'open', '9945a367-2c08-48e2-b172-ae16deeabf00', NULL, '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-09 13:54:46.000000', '2026-04-09 13:54:46.000000');
INSERT INTO `tickets` VALUES ('0b0cbe54-f015-4fc9-b3d7-1b7ba45db28a', 'TKT-20260409032339', '订单支付失败并持续报错', '我的订单无法支付，一直显示错误', 'high', 'billing', 'open', '9945a367-2c08-48e2-b172-ae16deeabf00', NULL, '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-09 03:23:40.000000', '2026-04-09 03:23:40.000000');
INSERT INTO `tickets` VALUES ('0ef652a7-8a3a-4d3f-9f70-6a5d02fb27bd', 'TKT-20260409135307', '订单支付失败，持续显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'open', '9945a367-2c08-48e2-b172-ae16deeabf00', NULL, '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-09 13:53:08.000000', '2026-04-09 13:53:08.000000');
INSERT INTO `tickets` VALUES ('21e19979-e603-4234-a6ab-a54647fb9ad4', 'TKT-20260404113551', '订单支付失败，系统持续显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'in_progress', '9945a367-2c08-48e2-b172-ae16deeabf00', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-04 11:35:51.000000', '2026-04-08 22:12:18.000000');
INSERT INTO `tickets` VALUES ('2405aa0f-c619-4c84-a7b0-8637e993ada6', 'TKT-20260409135554', '订单支付失败，系统持续显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'open', '9945a367-2c08-48e2-b172-ae16deeabf00', NULL, '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-09 13:55:54.000000', '2026-04-09 13:55:54.000000');
INSERT INTO `tickets` VALUES ('242b76ef-e26b-489f-99bc-bea50fe5f65d', 'TKT-20260404141650', '订单无法支付，一直显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'in_progress', '9945a367-2c08-48e2-b172-ae16deeabf00', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-04 14:16:50.000000', '2026-04-08 22:10:35.000000');
INSERT INTO `tickets` VALUES ('a2c9b213-6698-42b5-ac9b-669558e52662', 'TKT-20260409032815', '订单支付失败，持续显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'open', '9945a367-2c08-48e2-b172-ae16deeabf00', NULL, '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-09 03:28:15.000000', '2026-04-09 03:28:15.000000');
INSERT INTO `tickets` VALUES ('cb597913-3add-4426-82fd-da3ae5506e26', 'TKT-20260404071031', '客户投诉', 'bbb', 'high', 'technical', 'in_progress', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '7b023ee9-a64f-47f8-8ddb-f621b673ee5c', '{\"contact\": \"13918282671\"}', NULL, NULL, NULL, '2026-04-04 07:10:32.000000', '2026-04-04 15:18:32.000000');
INSERT INTO `tickets` VALUES ('d0b1c0f7-ba22-4233-a6cb-138e94647d76', 'TKT-20260408221556', '订单无法支付，一直显示错误', '我的订单无法支付，一直显示错误', 'high', 'billing', 'open', '9945a367-2c08-48e2-b172-ae16deeabf00', NULL, '{\"email\": \"592235962@qq.com\", \"phone\": null, \"username\": \"xlh\"}', NULL, NULL, NULL, '2026-04-08 22:15:56.000000', '2026-04-08 22:15:56.000000');

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
  `last_login_at` datetime(6) NULL DEFAULT NULL,
  `created_at` datetime(6) NULL DEFAULT NULL,
  `updated_at` datetime(6) NULL DEFAULT NULL,
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
INSERT INTO `users` VALUES ('0912d5f2-acdd-492e-852f-0b915524cafc', 'aaron', '592235963@qq.com', '$2b$12$et1MM2G5pbTsrRRAfnYaNONQLt/UowEBuagZQsWUnqA22rfvh2mTe', 'aaron', NULL, 2, 1, 0, '2026-04-09 15:15:20.000000', '2026-04-04 03:33:26.000000', '2026-04-09 15:15:20.000000', NULL);
INSERT INTO `users` VALUES ('230c67e9-4f24-448e-8bba-03adb9f88b2b', 'xjy', '592235960@qq.com', '$2b$12$heMzkM.w1CkfrWthYmGcwe6f6uNDhlEcWjq0LgntFo63EHdrNS1x6', 'xjy', NULL, 4, 1, 0, NULL, '2026-04-05 11:51:34.000000', '2026-04-05 11:51:34.000000', NULL);
INSERT INTO `users` VALUES ('2e0ed49e-fd72-4b94-9c33-fcd92719fa4d', 'yy', '592235981@qq.com', '$2b$12$yIDdhX4vVyj5MP.8qisbwOe7ApUwDg8Gc8SCxE3ok/KcvOcI08dd6', 'yy', NULL, 3, 1, 0, '2026-04-08 22:05:36.000000', '2026-04-08 22:05:30.000000', '2026-04-08 22:05:36.000000', NULL);
INSERT INTO `users` VALUES ('7b023ee9-a64f-47f8-8ddb-f621b673ee5c', 'admin', 'admin@example.com', '$2b$12$W.FoBpg6qrtU5v79Tar52eTr23NqomEgncxgHQJF4mhW6u6WwYvx.', '管理员', '13918282671', 1, 1, 0, '2026-04-09 16:31:04.704094', '2026-04-03 15:51:49.000000', '2026-04-09 16:31:04.724990', NULL);
INSERT INTO `users` VALUES ('9945a367-2c08-48e2-b172-ae16deeabf00', 'xlh', '592235962@qq.com', '$2b$12$HOzPDRjUNedD/dgktwMPBu9twn0ev7kHwwO7.Gl3Ou4RCyLrTkK8m', 'xu', NULL, 4, 1, 0, '2026-04-09 16:33:47.708097', '2026-04-04 03:32:30.000000', '2026-04-09 16:33:47.708528', NULL);
INSERT INTO `users` VALUES ('a3ff98db-713d-47e4-bbfd-e466be173419', 'hxy', '592235965@qq.com', '$2b$12$km.ZhBLHSDyzI8j4wvSG.eALsT.XupPfSjJ5TrehkZ2Vt2TyUnj/W', 'hxy', NULL, 3, 1, 0, '2026-04-05 11:49:49.000000', '2026-04-04 03:45:39.000000', '2026-04-05 11:49:49.000000', NULL);

SET FOREIGN_KEY_CHECKS = 1;
