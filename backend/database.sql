-- MySQL 数据库初始化脚本
-- 数据库: ticket_bot

CREATE DATABASE IF NOT EXISTS `ticket_bot` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `ticket_bot`;

-- 角色表
CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '角色ID',
    `name` VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名称: admin, agent, operator',
    `code` VARCHAR(50) NOT NULL UNIQUE COMMENT '角色代码',
    `description` VARCHAR(255) DEFAULT NULL COMMENT '角色描述',
    `permissions` JSON DEFAULT NULL COMMENT '权限列表',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色表';

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '用户ID (UUID)',
    `username` VARCHAR(100) NOT NULL UNIQUE COMMENT '用户名',
    `email` VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希',
    `full_name` VARCHAR(100) DEFAULT NULL COMMENT '全名',
    `phone` VARCHAR(20) DEFAULT NULL COMMENT '电话',
    `role_id` INT NOT NULL DEFAULT 1 COMMENT '角色ID (外键)',
    `is_active` TINYINT(1) DEFAULT 1 COMMENT '是否激活',
    `is_verified` TINYINT(1) DEFAULT 0 COMMENT '是否验证邮箱',
    `last_login_at` DATETIME DEFAULT NULL COMMENT '最后登录时间',
    `avatar_url` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_username` (`username`),
    INDEX `idx_email` (`email`),
    INDEX `idx_role_id` (`role_id`),
    CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 知识库表
CREATE TABLE IF NOT EXISTS `knowledge_bases` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '知识库ID (UUID)',
    `name` VARCHAR(100) NOT NULL COMMENT '知识库名称',
    `description` TEXT DEFAULT NULL COMMENT '知识库描述',
    `collection_name` VARCHAR(100) NOT NULL COMMENT 'Milvus Collection 名称',
    `owner_id` VARCHAR(36) NOT NULL COMMENT '所有者ID (用户ID)',
    `document_count` INT DEFAULT 0 COMMENT '文档数量',
    `status` VARCHAR(20) DEFAULT 'active' COMMENT '状态: active, inactive, building',
    `embedding_model` VARCHAR(100) DEFAULT 'sentence-transformers/all-MiniLM-L6-v2' COMMENT '嵌入模型',
    `meta_data` JSON DEFAULT NULL COMMENT '元数据',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_name` (`name`),
    INDEX `idx_owner_id` (`owner_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知识库表';

-- 文档表
CREATE TABLE IF NOT EXISTS `documents` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '文档ID (UUID)',
    `knowledge_base_id` VARCHAR(36) NOT NULL COMMENT '知识库ID',
    `title` VARCHAR(255) NOT NULL COMMENT '文档标题',
    `original_filename` VARCHAR(255) NOT NULL COMMENT '原始文件名',
    `file_path` VARCHAR(500) DEFAULT NULL COMMENT '文件存储路径',
    `file_type` VARCHAR(50) NOT NULL COMMENT '文件类型: txt, pdf, docx, md',
    `file_size` BIGINT DEFAULT 0 COMMENT '文件大小(字节)',
    `chunk_count` INT DEFAULT 0 COMMENT '分块数量',
    `status` VARCHAR(20) DEFAULT 'processing' COMMENT '状态: processing, indexed, failed',
    `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
    `meta_data` JSON DEFAULT NULL COMMENT '元数据',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_knowledge_base_id` (`knowledge_base_id`),
    INDEX `idx_status` (`status`),
    INDEX `idx_created_at` (`created_at`),
    CONSTRAINT `fk_documents_kb` FOREIGN KEY (`knowledge_base_id`) REFERENCES `knowledge_bases` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档表';

-- 工单表
CREATE TABLE IF NOT EXISTS `tickets` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '工单ID (UUID)',
    `ticket_no` VARCHAR(50) NOT NULL UNIQUE COMMENT '工单编号',
    `title` VARCHAR(255) NOT NULL COMMENT '工单标题',
    `content` TEXT NOT NULL COMMENT '工单内容',
    `priority` VARCHAR(20) DEFAULT 'normal' COMMENT '优先级: low, normal, high, urgent',
    `category` VARCHAR(50) DEFAULT 'general' COMMENT '分类: technical, billing, account, other',
    `status` VARCHAR(30) DEFAULT 'open' COMMENT '状态: open, pending, in_progress, resolved, closed',
    `customer_id` VARCHAR(36) NOT NULL COMMENT '客户ID (用户ID)',
    `assigned_agent_id` VARCHAR(36) DEFAULT NULL COMMENT '分配的客服ID',
    `customer_info` JSON DEFAULT NULL COMMENT '客户信息 (JSON: name, email, phone)',
    `meta_data` JSON DEFAULT NULL COMMENT '元数据 (JSON)',
    `resolved_at` DATETIME DEFAULT NULL COMMENT '解决时间',
    `closed_at` DATETIME DEFAULT NULL COMMENT '关闭时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_ticket_no` (`ticket_no`),
    INDEX `idx_status` (`status`),
    INDEX `idx_priority` (`priority`),
    INDEX `idx_category` (`category`),
    INDEX `idx_customer_id` (`customer_id`),
    INDEX `idx_assigned_agent_id` (`assigned_agent_id`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单表';

-- 工单消息表
CREATE TABLE IF NOT EXISTS `ticket_messages` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '消息ID (UUID)',
    `ticket_id` VARCHAR(36) NOT NULL COMMENT '工单ID',
    `sender_id` VARCHAR(36) NOT NULL COMMENT '发送者ID (用户ID或NULL表示系统)',
    `sender_type` VARCHAR(20) DEFAULT 'customer' COMMENT '发送者类型: customer, agent, system',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `message_type` VARCHAR(20) DEFAULT 'text' COMMENT '消息类型: text, image, file',
    `is_read` TINYINT(1) DEFAULT 0 COMMENT '是否已读',
    `read_at` DATETIME DEFAULT NULL COMMENT '阅读时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_ticket_id` (`ticket_id`),
    INDEX `idx_sender_id` (`sender_id`),
    INDEX `idx_created_at` (`created_at`),
    CONSTRAINT `fk_messages_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单消息表';

-- 工单状态变更记录表
CREATE TABLE IF NOT EXISTS `ticket_status_logs` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '日志ID (UUID)',
    `ticket_id` VARCHAR(36) NOT NULL COMMENT '工单ID',
    `from_status` VARCHAR(30) DEFAULT NULL COMMENT '原状态',
    `to_status` VARCHAR(30) NOT NULL COMMENT '新状态',
    `changed_by_id` VARCHAR(36) NOT NULL COMMENT '变更者ID',
    `note` TEXT DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_ticket_id` (`ticket_id`),
    INDEX `idx_changed_by_id` (`changed_by_id`),
    INDEX `idx_created_at` (`created_at`),
    CONSTRAINT `fk_status_logs_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单状态变更记录表';

-- 系统配置表
CREATE TABLE IF NOT EXISTS `system_configs` (
    `id` INT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    `key` VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
    `value` JSON NOT NULL COMMENT '配置值',
    `description` VARCHAR(255) DEFAULT NULL COMMENT '描述',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_key` (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 插入默认角色
INSERT INTO `roles` (`name`, `code`, `description`, `permissions`) VALUES
('管理员', 'admin', '系统管理员，拥有所有权限', '[]'),
('客服', 'agent', '客服人员，可以处理工单', '[]'),
('运营', 'operator', '运营人员，可以查看数据和报表', '[]'),
( '客户', 'customer', '普通客户', '[]');

-- 创建管理员用户 (密码: admin123)
-- 注意: 实际使用时需要通过 API 或脚本创建用户

-- ==========================================
-- 实时聊天系统表
-- ==========================================

-- 聊天会话表
CREATE TABLE IF NOT EXISTS `chat_sessions` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '会话ID (UUID)',
    `customer_id` VARCHAR(36) NOT NULL COMMENT '客户ID',
    `agent_id` VARCHAR(36) DEFAULT NULL COMMENT '接入客服ID',
    `ticket_id` VARCHAR(36) DEFAULT NULL COMMENT '关联工单ID',
    `status` VARCHAR(20) DEFAULT 'waiting' COMMENT '状态: waiting(排队中), connected(已接入), closed(已关闭)',
    `request_type` VARCHAR(50) DEFAULT NULL COMMENT '客户请求类型: order/payment/technical/other',
    `initial_message` TEXT DEFAULT NULL COMMENT '客户初始消息',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `connected_at` DATETIME DEFAULT NULL COMMENT '客服接入时间',
    `closed_at` DATETIME DEFAULT NULL COMMENT '会话关闭时间',
    `last_message_at` DATETIME DEFAULT NULL COMMENT '最后消息时间',
    INDEX `idx_status` (`status`),
    INDEX `idx_agent_id` (`agent_id`),
    INDEX `idx_customer_id` (`customer_id`),
    INDEX `idx_created_at` (`created_at`),
    CONSTRAINT `fk_chat_sessions_customer` FOREIGN KEY (`customer_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_chat_sessions_agent` FOREIGN KEY (`agent_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_chat_sessions_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `tickets` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天会话表';

-- 聊天记录表
-- sender_id 使用规则:
--   - AI 消息：sender_id = NULL
--   - 客户消息：sender_id = 客户ID
--   - 客服消息：sender_id = 客服ID
--   - 系统消息：sender_id = NULL
-- customer_id: 统一设置为该消息所属的客户ID，用于简化历史消息查询
CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '消息ID (UUID)',
    `session_id` VARCHAR(36) DEFAULT NULL COMMENT '会话ID (AI聊天时为NULL)',
    `sender_id` VARCHAR(36) DEFAULT NULL COMMENT '发送者ID (AI/系统消息为NULL)',
    `sender_type` VARCHAR(20) NOT NULL COMMENT '发送者类型: customer/agent/system/ai',
    `content` TEXT NOT NULL COMMENT '消息内容',
    `message_type` VARCHAR(20) DEFAULT 'text' COMMENT '消息类型: text/image/file/system',
    `customer_id` VARCHAR(36) DEFAULT NULL COMMENT '客户ID (用于简化历史消息查询)',
    `is_read` TINYINT(1) DEFAULT 0 COMMENT '是否已读',
    `read_at` DATETIME DEFAULT NULL COMMENT '阅读时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX `idx_session_id` (`session_id`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_sender_id` (`sender_id`),
    INDEX `idx_customer_id` (`customer_id`),
    INDEX `idx_sender_type` (`sender_type`),
    CONSTRAINT `fk_chat_messages_session` FOREIGN KEY (`session_id`) REFERENCES `chat_sessions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_chat_messages_sender` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_chat_messages_customer` FOREIGN KEY (`customer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='聊天记录表';

-- 客服在线状态表
CREATE TABLE IF NOT EXISTS `agent_status` (
    `agent_id` VARCHAR(36) PRIMARY KEY COMMENT '客服ID',
    `status` VARCHAR(20) DEFAULT 'offline' COMMENT '在线状态: online(在线), busy(忙碌), offline(离线)',
    `current_sessions` INT DEFAULT 0 COMMENT '当前会话数',
    `max_sessions` INT DEFAULT 5 COMMENT '最大并发会话数',
    `total_sessions_today` INT DEFAULT 0 COMMENT '今日总会话数',
    `total_messages_today` INT DEFAULT 0 COMMENT '今日总消息数',
    `last_heartbeat` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '最后心跳时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT `fk_agent_status_agent` FOREIGN KEY (`agent_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='客服在线状态表';

-- ==========================================
-- 监控指标统计表
-- ==========================================

-- 意图识别统计表 - 按天聚合
CREATE TABLE IF NOT EXISTS `intent_metrics` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '记录ID (UUID)',
    `metric_date` DATE NOT NULL COMMENT '统计日期',
    `intent` VARCHAR(50) NOT NULL COMMENT '意图类型: create_ticket/query_ticket/process_ticket/summary/general',
    `total` INT DEFAULT 0 NOT NULL COMMENT '总识别次数',
    `correct` INT DEFAULT 0 NOT NULL COMMENT '正确次数',
    `confidence_sum` FLOAT DEFAULT 0.0 COMMENT '置信度总和（用于计算平均置信度）',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_date_intent` (`metric_date`, `intent`),
    INDEX `idx_metric_date` (`metric_date`),
    INDEX `idx_intent` (`intent`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='意图识别统计表 - 按天聚合';

-- API 响应时间统计表 - 按天、端点、方法聚合
CREATE TABLE IF NOT EXISTS `api_metrics` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '记录ID (UUID)',
    `metric_date` DATE NOT NULL COMMENT '统计日期',
    `endpoint` VARCHAR(255) NOT NULL COMMENT 'API 端点路径',
    `method` VARCHAR(10) NOT NULL COMMENT 'HTTP 方法: GET/POST/PUT/DELETE',
    `request_count` INT DEFAULT 0 NOT NULL COMMENT '请求次数',
    `error_count` INT DEFAULT 0 NOT NULL COMMENT '错误次数（4xx/5xx）',
    `latency_sum_ms` FLOAT DEFAULT 0.0 COMMENT '总响应时间（毫秒）',
    `latency_min_ms` FLOAT DEFAULT 0.0 COMMENT '最小响应时间',
    `latency_max_ms` FLOAT DEFAULT 0.0 COMMENT '最大响应时间',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_date_endpoint_method` (`metric_date`, `endpoint`, `method`),
    INDEX `idx_metric_date` (`metric_date`),
    INDEX `idx_endpoint` (`endpoint`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='API 响应时间统计表 - 按天聚合';

-- 错误统计表 - 按天、错误类型聚合
CREATE TABLE IF NOT EXISTS `error_metrics` (
    `id` VARCHAR(36) PRIMARY KEY COMMENT '记录ID (UUID)',
    `metric_date` DATE NOT NULL COMMENT '统计日期',
    `error_type` VARCHAR(100) NOT NULL COMMENT '错误类型: HTTP404/HTTP500/ValidationError等',
    `endpoint` VARCHAR(255) DEFAULT NULL COMMENT '发生错误的端点（可选）',
    `count` INT DEFAULT 0 NOT NULL COMMENT '错误次数',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY `uk_date_type_endpoint` (`metric_date`, `error_type`, `endpoint`),
    INDEX `idx_metric_date` (`metric_date`),
    INDEX `idx_error_type` (`error_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='错误统计表 - 按天聚合';