-- 删除现有表（按依赖顺序）
DROP TABLE IF EXISTS issue_history;
DROP TABLE IF EXISTS review_comments;
DROP TABLE IF EXISTS issue_comments;
DROP TABLE IF EXISTS review_issues;
DROP TABLE IF EXISTS issues;
DROP TABLE IF EXISTS analysis_results;
DROP TABLE IF EXISTS code_commits;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS project_roles;
DROP TABLE IF EXISTS role_menus;
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS menus;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS roles;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS parameters;
-- 用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
    user_id VARCHAR(50) NOT NULL UNIQUE COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '电子邮箱',
    phone VARCHAR(20) COMMENT '手机号码',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希值',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT users_username_email_unique UNIQUE (username, email)
) COMMENT = '用户表';

-- 权限表（新增）
CREATE TABLE permissions (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '权限ID',
    code VARCHAR(50) NOT NULL UNIQUE COMMENT '权限代码',
    name VARCHAR(100) NOT NULL COMMENT '权限名称',
    description TEXT COMMENT '权限描述',
    module VARCHAR(50) NOT NULL COMMENT '所属模块',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT = '权限表';

-- 角色表
CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '角色ID',
    name VARCHAR(50) NOT NULL UNIQUE COMMENT '角色名称',
    description TEXT COMMENT '角色描述',
    role_type VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT '角色类型：project或user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT = '角色表';

-- 角色权限关联表（新增）
CREATE TABLE role_permissions (
    role_id INT NOT NULL COMMENT '角色ID',
    permission_id INT NOT NULL COMMENT '权限ID',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    PRIMARY KEY (role_id, permission_id)
) COMMENT = '角色权限关联表';

-- 用户角色关联表
CREATE TABLE user_roles (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role_id INT NOT NULL COMMENT '角色ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    CONSTRAINT user_role_unique UNIQUE (user_id, role_id)
) COMMENT = '用户角色关联表';

-- 项目表
CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '项目ID',
    name VARCHAR(255) NOT NULL COMMENT '项目名称',
    description TEXT COMMENT '项目描述',
    repository_url VARCHAR(500) NOT NULL COMMENT '仓库URL',
    repository_type VARCHAR(10) DEFAULT 'git' COMMENT '仓库类型',
    branch VARCHAR(100) DEFAULT 'main' COMMENT '默认分支',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_by INT COMMENT '创建人ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT = '项目表';

-- 项目角色关联表
CREATE TABLE project_roles (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '关联ID',
    project_id INT NOT NULL COMMENT '项目ID',
    user_id INT NOT NULL COMMENT '用户ID',
    role_id INT NOT NULL COMMENT '项目中的角色ID',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '加入时间',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    CONSTRAINT project_user_role_unique UNIQUE (project_id, user_id, role_id)
) COMMENT = '项目角色关联表';

-- 菜单表
CREATE TABLE menus (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '菜单ID',
    title VARCHAR(255) NOT NULL COMMENT '菜单标题',
    path VARCHAR(255) COMMENT '菜单路径',
    icon VARCHAR(255) COMMENT '菜单图标',
    parent_id INT COMMENT '父菜单ID',
    order_num INT DEFAULT 0 COMMENT '排序号',
    permission_id INT COMMENT '对应权限ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT = '菜单表';

-- 角色菜单关联表
CREATE TABLE role_menus (
    role_id INT NOT NULL COMMENT '角色ID',
    menu_id INT NOT NULL COMMENT '菜单ID',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '分配时间',
    PRIMARY KEY (role_id, menu_id)
) COMMENT = '角色菜单关联表';

-- 参数表
CREATE TABLE parameters (
    param_id VARCHAR(10) NOT NULL COMMENT '参数ID',
    param_name VARCHAR(10) NOT NULL COMMENT '参数名称',
    param_type VARCHAR(10) NOT NULL COMMENT '参数类型',
    PRIMARY KEY (param_id,param_type)
) COMMENT = '参数表';
-- 代码提交表
CREATE TABLE code_commits (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '提交ID',
    commit_id VARCHAR(50) NOT NULL UNIQUE COMMENT '提交哈希',
    project_id INT NOT NULL COMMENT '关联项目',
    repository VARCHAR(255) NOT NULL COMMENT '代码仓库',
    branch VARCHAR(100) NOT NULL COMMENT '代码分支',
    author_id INT COMMENT '提交作者',
    commit_message TEXT NOT NULL COMMENT '提交说明',
    commit_time DATETIME NOT NULL COMMENT '提交时间',
    files_changed INT DEFAULT 0 COMMENT '修改文件数',
    insertions INT DEFAULT 0 COMMENT '新增行数',
    deletions INT DEFAULT 0 COMMENT '删除行数',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '记录创建时间'
) COMMENT='代码提交记录表';

-- 合并后的问题表（整合issues和review_issues）
CREATE TABLE issues (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '问题ID',
    project_id INT NOT NULL COMMENT '关联项目ID',
    commit_id INT COMMENT '关联提交ID',
    title VARCHAR(255) NOT NULL COMMENT '问题标题',
    description TEXT COMMENT '问题描述',
    status VARCHAR(50) NOT NULL DEFAULT 'open' COMMENT '问题状态',
    priority VARCHAR(50) NOT NULL DEFAULT 'medium' COMMENT '问题优先级',
    issue_type VARCHAR(50) NOT NULL DEFAULT 'bug' COMMENT '问题类型',
    severity VARCHAR(20) DEFAULT NULL COMMENT '严重程度（代码检视问题特有）',
    creator_id INT COMMENT '创建者ID',
    assignee_id INT COMMENT '指派人ID',
    file_path VARCHAR(255) COMMENT '文件路径',
    line_start INT COMMENT '起始行号',
    line_end INT COMMENT '结束行号',
    resolution_time FLOAT COMMENT '解决时间(小时)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    closed_at TIMESTAMP NULL COMMENT '关闭时间',
    resolved_at TIMESTAMP NULL COMMENT '解决时间',
    CONSTRAINT check_issue_status CHECK (status IN ('open', 'in_progress', 'resolved', 'verified', 'closed', 'reopened','rejected')),
    CONSTRAINT check_issue_priority CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT check_issue_type CHECK (issue_type IN ('bug', 'feature', 'improvement', 'task', 'security', 'code_review')),
    CONSTRAINT check_issue_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))
) COMMENT = '问题跟踪表（包含一般问题和代码检视问题）';

-- 合并后的评论表（整合issue_comments和review_comments）
CREATE TABLE issue_comments (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '评论ID',
    issue_id INT NOT NULL COMMENT '关联问题ID',
    user_id INT COMMENT '评论用户ID',
    content TEXT NOT NULL COMMENT '评论内容',
    file_path VARCHAR(255) COMMENT '相关文件路径',
    line_number INT COMMENT '相关行号',
    is_resolution BOOLEAN DEFAULT FALSE COMMENT '是否为解决方案',
    parent_id INT COMMENT '父评论ID，用于嵌套回复',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) COMMENT = '问题评论表';

-- 问题修改历史表
CREATE TABLE issue_history (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '历史记录ID',
    issue_id INT NOT NULL COMMENT '关联问题ID',
    user_id INT COMMENT '操作用户ID',
    field_name VARCHAR(50) NOT NULL COMMENT '修改字段名',
    old_value TEXT COMMENT '旧值',
    new_value TEXT COMMENT '新值',
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间'
) COMMENT = '问题修改历史表';

-- 通知表
CREATE TABLE notifications (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '通知ID',
    recipient_id INT NOT NULL COMMENT '接收用户ID',
    issue_id INT COMMENT '关联问题ID',
    type VARCHAR(50) NOT NULL COMMENT '通知类型',
    message TEXT NOT NULL COMMENT '通知内容',
    is_read BOOLEAN DEFAULT FALSE COMMENT '是否已读',
    read_at TIMESTAMP NULL COMMENT '阅读时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) COMMENT = '通知表';

-- 代码分析结果表
CREATE TABLE analysis_results (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分析结果ID',
    project_id INT NOT NULL COMMENT '关联项目ID',
    commit_id INT COMMENT '关联提交ID',
    analysis_type VARCHAR(50) NOT NULL COMMENT '分析类型',
    result_summary TEXT COMMENT '结果摘要',
    details JSON COMMENT '详细结果',
    code_quality_score FLOAT COMMENT '代码质量得分',
    complexity_score FLOAT COMMENT '复杂度得分',
    maintainability_score FLOAT COMMENT '可维护性得分',
    security_score FLOAT COMMENT '安全性得分',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) COMMENT = '代码分析结果表';

-- 添加外键约束
-- ALTER TABLE user_roles ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
-- ALTER TABLE user_roles ADD CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
-- ALTER TABLE role_permissions ADD CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
-- ALTER TABLE role_permissions ADD CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE;
-- ALTER TABLE projects ADD CONSTRAINT fk_projects_creator FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL;
-- ALTER TABLE project_roles ADD CONSTRAINT fk_project_roles_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
-- ALTER TABLE project_roles ADD CONSTRAINT fk_project_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
-- ALTER TABLE project_roles ADD CONSTRAINT fk_project_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
-- ALTER TABLE menus ADD CONSTRAINT fk_menus_parent FOREIGN KEY (parent_id) REFERENCES menus(id) ON DELETE SET NULL;
-- ALTER TABLE menus ADD CONSTRAINT fk_menus_permission FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE SET NULL;
-- ALTER TABLE role_menus ADD CONSTRAINT fk_role_menus_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE;
-- ALTER TABLE role_menus ADD CONSTRAINT fk_role_menus_menu FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE;
-- ALTER TABLE code_commits ADD CONSTRAINT fk_commits_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
-- ALTER TABLE code_commits ADD CONSTRAINT fk_commits_author FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL;
-- ALTER TABLE issues ADD CONSTRAINT fk_issues_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
-- ALTER TABLE issues ADD CONSTRAINT fk_issues_commit FOREIGN KEY (commit_id) REFERENCES code_commits(id) ON DELETE SET NULL;
-- ALTER TABLE issues ADD CONSTRAINT fk_issues_creator FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE SET NULL;
-- ALTER TABLE issues ADD CONSTRAINT fk_issues_assignee FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL;
-- ALTER TABLE issue_comments ADD CONSTRAINT fk_comments_issue FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE;
-- ALTER TABLE issue_comments ADD CONSTRAINT fk_comments_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
-- ALTER TABLE issue_comments ADD CONSTRAINT fk_comments_parent FOREIGN KEY (parent_id) REFERENCES issue_comments(id) ON DELETE SET NULL;
-- ALTER TABLE issue_history ADD CONSTRAINT fk_history_issue FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE CASCADE;
-- ALTER TABLE issue_history ADD CONSTRAINT fk_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
-- ALTER TABLE notifications ADD CONSTRAINT fk_notifications_recipient FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE;
-- ALTER TABLE notifications ADD CONSTRAINT fk_notifications_issue FOREIGN KEY (issue_id) REFERENCES issues(id) ON DELETE SET NULL;
-- ALTER TABLE analysis_results ADD CONSTRAINT fk_analysis_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
-- ALTER TABLE analysis_results ADD CONSTRAINT fk_analysis_commit FOREIGN KEY (commit_id) REFERENCES code_commits(id) ON DELETE SET NULL;

-- 初始化权限数据
INSERT INTO permissions (code, name, description, module) VALUES
-- 系统管理权限
('system:admin', '系统管理', '系统管理员权限', '系统'),
('system:config', '系统配置', '系统配置管理权限', '系统'),

-- 用户管理权限
('user:view', '查看用户', '查看用户列表和详情', '用户'),
('user:create', '创建用户', '创建新用户', '用户'),
('user:edit', '编辑用户', '编辑用户信息', '用户'),
('user:delete', '删除用户', '删除用户', '用户'),

-- 角色管理权限
('role:view', '查看角色', '查看角色列表和详情', '角色'),
('role:create', '创建角色', '创建新角色', '角色'),
('role:edit', '编辑角色', '编辑角色信息和权限', '角色'),
('role:delete', '删除角色', '删除角色', '角色'),

-- 项目管理权限
('project:view', '查看项目', '查看项目列表和详情', '项目'),
('project:create', '创建项目', '创建新项目', '项目'),
('project:edit', '编辑项目', '编辑项目信息', '项目'),
('project:delete', '删除项目', '删除项目', '项目'),
('project:manage', '项目管理', '管理项目配置和成员', '项目'),
('project:member:manage', '管理成员', '管理项目成员', '项目'),
('project:create:basic', '基础项目创建', '创建基础项目', '项目'),
('project:edit:basic', '基础项目编辑', '编辑基础项目信息', '项目'),
('project:list', '项目列表', '查看项目列表', '项目'),
('project:detail', '项目详情', '查看项目详情', '项目'),

-- 问题管理权限
('issue:view', '查看问题', '查看问题列表和详情', '问题'),
('issue:create', '创建问题', '创建新问题', '问题'),
('issue:edit', '编辑问题', '编辑问题信息', '问题'),
('issue:delete', '删除问题', '删除问题', '问题'),
('issue:assign', '分配问题', '分配问题给其他用户', '问题'),
('issue:comment', '评论问题', '对问题添加评论', '问题'),
('issue:manage', '问题管理', '管理所有问题', '问题'),

-- 代码审查权限
('code:review', '代码审查', '执行代码审查', '代码'),
('code:analyze', '代码分析', '执行代码分析', '代码'),
('code:review:manage', '管理代码审查', '管理代码审查流程', '代码'),

-- 团队管理权限
('team:view', '查看团队', '查看团队信息', '团队'),
('team:manage', '管理团队', '管理团队成员和配置', '团队'),

-- 菜单管理权限
('menu:view', '查看菜单', '查看菜单列表', '菜单'),
('menu:manage', '管理菜单', '管理系统菜单', '菜单');

-- 初始化用户数据
INSERT INTO users (user_id,username, email,phone, password_hash, created_at) VALUES
('admin','admin1', 'admin@codereview.com','15689789546', '$2a$12$LzV2DYssjcZGp.sS3uLA1OAVR5MhZ7VpSjCYo.8HRWJ5XQAxMzLlS', CURRENT_TIMESTAMP),
('pm', 'pm1','pm@codereview.com','15689789546', '$2a$12$LzV2DYssjcZGp.sS3uLA1OAVR5MhZ7VpSjCYo.8HRWJ5XQAxMzLlS', CURRENT_TIMESTAMP),
('developer','developer1', 'developer@codereview.com','15689789546', '$2a$12$LzV2DYssjcZGp.sS3uLA1OAVR5MhZ7VpSjCYo.8HRWJ5XQAxMzLlS', CURRENT_TIMESTAMP),
('reviewer','reviewer1', 'reviewer@codereview.com','15689789546', '$2a$12$LzV2DYssjcZGp.sS3uLA1OAVR5MhZ7VpSjCYo.8HRWJ5XQAxMzLlS', CURRENT_TIMESTAMP),
('tester', 'tester1', 'tester@codereview.com','15689789546', '$2a$12$LzV2DYssjcZGp.sS3uLA1OAVR5MhZ7VpSjCYo.8HRWJ5XQAxMzLlS', CURRENT_TIMESTAMP);

-- 初始化角色数据
INSERT INTO roles (name, description, role_type, created_at) VALUES
-- 用户角色
('admin', '系统管理员，拥有所有权限', 'user', CURRENT_TIMESTAMP),
('project_manager', '项目管理人员，管理多个项目', 'user', CURRENT_TIMESTAMP),
('developer', '开发人员，负责代码实现', 'user', CURRENT_TIMESTAMP),
('reviewer', '代码审查人员，对代码进行审查', 'user', CURRENT_TIMESTAMP),
('tester', '测试人员，负责测试和质量保证', 'user', CURRENT_TIMESTAMP),

-- 项目角色
('PM', '项目经理，负责项目管理和协调', 'project', CURRENT_TIMESTAMP),
('SE', '软件工程师，负责软件设计和开发', 'project', CURRENT_TIMESTAMP),
('DEV', '开发人员，负责代码实现', 'project', CURRENT_TIMESTAMP),
('QA', '质量专家，负责代码审查和质量控制', 'project', CURRENT_TIMESTAMP);

-- 角色权限关联
-- 管理员角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions;

-- 项目管理角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 2, id FROM permissions 
WHERE code IN ('project:view', 'project:create', 'project:edit', 'project:manage', 'project:member:manage',
              'issue:view', 'issue:create', 'issue:edit', 'issue:assign', 'issue:comment', 'issue:manage',
              'code:review', 'code:analyze', 'team:view', 'team:manage');

-- 开发人员角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 3, id FROM permissions 
WHERE code IN ('project:view', 'project:create:basic', 'project:edit:basic', 'project:list', 'project:detail', 'issue:view', 'issue:create', 'issue:comment', 'code:review');

-- 审查人员角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 4, id FROM permissions 
WHERE code IN ('project:view', 'issue:view', 'issue:create', 'issue:edit', 'issue:comment',
              'code:review', 'code:analyze');

-- 测试人员角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 5, id FROM permissions 
WHERE code IN ('project:view', 'issue:view', 'issue:create', 'issue:edit', 'issue:comment');

-- 项目PM角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 6, id FROM permissions 
WHERE code IN ('project:manage', 'project:edit', 'project:member:manage', 'issue:manage',
              'code:review:manage', 'team:manage');

-- 软件工程师角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 7, id FROM permissions 
WHERE code IN ('project:view', 'issue:view', 'issue:create', 'issue:edit', 'issue:comment',
              'code:review', 'code:analyze');

-- 开发人员项目角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 8, id FROM permissions 
WHERE code IN ('project:view', 'issue:view', 'issue:create', 'issue:comment', 'code:review');

-- 质量专家角色权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 9, id FROM permissions 
WHERE code IN ('project:view', 'issue:view', 'issue:create', 'issue:edit', 'issue:comment',
              'code:review', 'code:analyze');

-- 用户角色关联
INSERT INTO user_roles (user_id, role_id, created_at, is_active) VALUES
(1, 1, CURRENT_TIMESTAMP, TRUE), -- admin用户为管理员角色
(2, 2, CURRENT_TIMESTAMP, TRUE), -- pm用户为项目管理角色
(3, 3, CURRENT_TIMESTAMP, TRUE), -- developer用户为开发人员角色
(4, 4, CURRENT_TIMESTAMP, TRUE), -- reviewer用户为审查人员角色
(5, 5, CURRENT_TIMESTAMP, TRUE); -- tester用户为测试人员角色

-- 项目数据
INSERT INTO projects (name, description, repository_url, repository_type, branch, created_by, created_at) VALUES
('代码检视系统', '代码检视系统本身的源代码仓库', 'https://github.com/example/code-review-system.git', 'git', 'main', 1, CURRENT_TIMESTAMP),
('前端示例项目', '前端React+TypeScript项目示例', 'https://github.com/example/frontend-demo.git', 'git', 'main', 2, CURRENT_TIMESTAMP),
('后端API服务', 'FastAPI后端服务示例', 'https://github.com/example/backend-api.git', 'git', 'develop', 2, CURRENT_TIMESTAMP),
('移动应用', 'Flutter移动应用示例', 'https://github.com/example/mobile-app.git', 'git', 'main', 3, CURRENT_TIMESTAMP),
('数据分析工具', 'Python数据分析工具', 'https://github.com/example/data-analytics.git', 'git', 'master', 1, CURRENT_TIMESTAMP);

-- 项目角色关联
INSERT INTO project_roles (project_id, user_id, role_id, joined_at, is_active) VALUES
-- 代码检视系统项目
(1, 1, 6, CURRENT_TIMESTAMP, TRUE), -- admin用户在项目1中是PM
(1, 3, 8, CURRENT_TIMESTAMP, TRUE), -- developer用户在项目1中是DEV
(1, 4, 9, CURRENT_TIMESTAMP, TRUE), -- reviewer用户在项目1中是QA
(1, 5, 9, CURRENT_TIMESTAMP, TRUE), -- tester用户在项目1中是QA

-- 前端示例项目
(2, 2, 6, CURRENT_TIMESTAMP, TRUE), -- pm用户在项目2中是PM
(2, 3, 8, CURRENT_TIMESTAMP, TRUE), -- developer用户在项目2中是DEV
(2, 4, 9, CURRENT_TIMESTAMP, TRUE), -- reviewer用户在项目2中是QA
(2, 5, 9, CURRENT_TIMESTAMP, TRUE), -- tester用户在项目2中是QA

-- 后端API服务
(3, 2, 6, CURRENT_TIMESTAMP, TRUE), -- pm用户在项目3中是PM
(3, 3, 8, CURRENT_TIMESTAMP, TRUE), -- developer用户在项目3中是DEV
(3, 1, 7, CURRENT_TIMESTAMP, TRUE), -- admin用户在项目3中是SE
(3, 5, 9, CURRENT_TIMESTAMP, TRUE); -- tester用户在项目3中是QA

-- 初始化菜单数据（关联到权限）
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_id) VALUES
-- 顶级菜单
('仪表盘', '/dashboard', 'DashboardOutlined', NULL, 1, 
 (SELECT id FROM permissions WHERE code = 'project:view')),
('项目管理', '/projects', 'ProjectOutlined', NULL, 2, 
 (SELECT id FROM permissions WHERE code = 'project:view')),
('代码审查', '/code-review', 'CodeOutlined', NULL, 3, 
 (SELECT id FROM permissions WHERE code = 'code:review')),
('问题追踪', '/issues', 'BugOutlined', NULL, 4, 
 (SELECT id FROM permissions WHERE code = 'issue:view')),
('代码分析', '/code-analysis', 'BarChartOutlined', NULL, 5, 
 (SELECT id FROM permissions WHERE code = 'code:analyze')),
('系统管理', '/system', 'SettingOutlined', NULL, 6, 
 (SELECT id FROM permissions WHERE code = 'system:admin'));

-- 获取上面插入的菜单ID
SET @dashboard_id = LAST_INSERT_ID();
SET @projects_id = @dashboard_id + 1;
SET @code_review_id = @dashboard_id + 2;
SET @issues_id = @dashboard_id + 3;
SET @code_analysis_id = @dashboard_id + 4;
SET @system_id = @dashboard_id + 5;

-- 系统管理子菜单
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_id) VALUES
('用户管理', '/system/users', 'UserOutlined', @system_id, 1, 
 (SELECT id FROM permissions WHERE code = 'user:view')),
('角色管理', '/system/roles', 'TeamOutlined', @system_id, 2, 
 (SELECT id FROM permissions WHERE code = 'role:view')),
('菜单管理', '/system/menus', 'MenuOutlined', @system_id, 3, 
 (SELECT id FROM permissions WHERE code = 'menu:manage')),

-- 项目管理子菜单
('我的项目', '/projects/my', 'FolderOutlined', @projects_id, 1, 
 (SELECT id FROM permissions WHERE code = 'project:list')),
('全部项目', '/projects/all', 'AppstoreOutlined', @projects_id, 2, 
 (SELECT id FROM permissions WHERE code = 'project:list')),
('创建项目', '/projects/create', 'PlusOutlined', @projects_id, 3, 
 (SELECT id FROM permissions WHERE code = 'project:create:basic')),
('编辑项目', '/projects/edit', 'EditOutlined', @projects_id, 4, 
 (SELECT id FROM permissions WHERE code = 'project:edit:basic')),
('项目详情', '/projects/detail', 'ProfileOutlined', @projects_id, 5, 
 (SELECT id FROM permissions WHERE code = 'project:detail'));

-- 角色菜单关联
INSERT INTO role_menus (role_id, menu_id)
SELECT r.id, m.id
FROM roles r, menus m, role_permissions rp, permissions p
WHERE r.id = rp.role_id 
  AND rp.permission_id = p.id
  AND m.permission_id = p.id;

-- 代码提交记录
INSERT INTO code_commits (commit_id, project_id, repository, branch, author_id, commit_message, commit_time, files_changed, insertions, deletions) VALUES
('a1b2c3d4e5f6', 1, 'https://github.com/example/code-review-system.git', 'main', 3, '初始化项目结构', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 10 DAY), 15, 500, 0),
('b2c3d4e5f6g7', 1, 'https://github.com/example/code-review-system.git', 'main', 3, '实现用户认证模块', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 9 DAY), 5, 200, 10),
('c3d4e5f6g7h8', 2, 'https://github.com/example/frontend-demo.git', 'main', 3, '添加用户界面组件', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 5 DAY), 8, 350, 25),
('d4e5f6g7h8i9', 3, 'https://github.com/example/backend-api.git', 'develop', 3, '修复数据库连接泄漏问题', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 4 DAY), 3, 25, 15);

-- 问题数据
INSERT INTO issues (project_id, commit_id, title, description, status, priority, issue_type, severity, creator_id, assignee_id, file_path, line_start, line_end, created_at) VALUES
-- 一般问题
(1, 1, '登录页面响应慢', '登录页面在低网速环境下加载非常慢，需要优化', 'open', 'medium', 'improvement', NULL, 2, 3, 'src/pages/login/index.tsx', NULL, NULL, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 8 DAY)),
(1, 2, '用户认证没有做密码强度校验', '需要添加密码强度校验功能', 'in_progress', 'high', 'security', NULL, 4, 3, 'src/services/auth.ts', NULL, NULL, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)),
(2, 3, 'UI组件未做响应式适配', '在移动设备上显示异常，需要添加响应式设计', 'open', 'medium', 'bug', NULL, 5, 3, 'src/components/Header.tsx', NULL, NULL, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 5 DAY)),

-- 代码检视问题
(1, 1, '身份验证逻辑需要重构', '这部分代码需要重构，存在重复逻辑', 'open', 'low', 'code_review', 'low', 4, 3, 'src/utils/auth.ts', 45, 52, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 8 DAY)),
(1, 2, '密码比较存在安全隐患', '这里的密码比较存在潜在的timing attack风险', 'open', 'high', 'code_review', 'high', 4, 3, 'src/services/auth.ts', 112, 125, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY));

-- 问题评论
INSERT INTO issue_comments (issue_id, user_id, content, file_path, line_number, is_resolution, created_at) VALUES
-- 一般问题评论
(1, 4, '这个问题比较关键，建议尽快处理', NULL, NULL, FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 8 DAY)),
(1, 3, '我已经开始调查这个问题，初步看是资源加载顺序问题', NULL, NULL, FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)),
(2, 2, '这是一个安全性问题，需要高优先级处理', NULL, NULL, FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)),

-- 代码检视问题评论
(4, 4, '建议将此处逻辑提取为单独的函数，减少代码重复', 'src/utils/auth.ts', 48, FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 8 DAY)),
(4, 3, '同意这个建议，我会进行重构', NULL, NULL, FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)),
(5, 3, '我会使用恒定时间的比较函数来解决这个问题', 'src/services/auth.ts', 118, TRUE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 6 DAY));

-- 问题历史
INSERT INTO issue_history (issue_id, user_id, field_name, old_value, new_value, changed_at) VALUES
(1, 2, 'priority', 'low', 'medium', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 8 DAY)),
(2, 4, 'status', 'open', 'in_progress', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 6 DAY)),
(2, 4, 'assignee_id', NULL, '3', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 6 DAY)),
(4, 4, 'description', '代码需要重构', '这部分代码需要重构，存在重复逻辑', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)),
(5, 3, 'assignee_id', NULL, '3', DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 6 DAY));

-- 通知
INSERT INTO notifications (recipient_id, issue_id, type, message, is_read, created_at) VALUES
(3, 1, 'issue_assigned', '您被分配了一个新的问题：登录页面响应慢', FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 8 DAY)),
(3, 2, 'issue_assigned', '您被分配了一个新的问题：用户认证没有做密码强度校验', FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY)),
(3, 3, 'issue_assigned', '您被分配了一个新的问题：UI组件未做响应式适配', FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 5 DAY)),
(4, 1, 'issue_assigned', '您被分配了一个新的问题：身份验证逻辑需要重构', FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 8 DAY)),
(4, 2, 'issue_assigned', '您被分配了一个新的问题：密码比较存在安全隐患', FALSE, DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 7 DAY));
