-- 删除已存在的表
DROP TABLE IF EXISTS ci_cd_records;
DROP TABLE IF EXISTS code_hotspots;
DROP TABLE IF EXISTS notifications;
DROP TABLE IF EXISTS role_menus;
DROP TABLE IF EXISTS menus;
DROP TABLE IF EXISTS role_permissions;
DROP TABLE IF EXISTS permissions;
DROP TABLE IF EXISTS review_comments;
DROP TABLE IF EXISTS issue_history;
DROP TABLE IF EXISTS review_issues;
DROP TABLE IF EXISTS code_files;
DROP TABLE IF EXISTS code_commits;
DROP TABLE IF EXISTS project_roles;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS users;

-- 创建枚举类型
CREATE TYPE user_role AS ENUM ('admin', 'developer', 'reviewer');
CREATE TYPE project_role AS ENUM ('admin', 'developer', 'architect');
CREATE TYPE issue_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE issue_priority AS ENUM ('low', 'medium', 'high');
CREATE TYPE issue_status AS ENUM ('open', 'in_progress', 'resolved', 'verified', 'closed');
CREATE TYPE ci_cd_status AS ENUM ('success', 'failure', 'pending');

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role user_role,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目表
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    repository_url VARCHAR(500) NOT NULL,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- 项目用户角色表
CREATE TABLE project_roles (
    id SERIAL PRIMARY KEY,
    project_id INTEGER,
    user_id INTEGER,
    role project_role,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 代码提交信息表
CREATE TABLE code_commits (
    id SERIAL PRIMARY KEY,
    commit_id VARCHAR(50) UNIQUE NOT NULL,
    project_id INTEGER,
    repository VARCHAR(255) NOT NULL,
    branch VARCHAR(100) NOT NULL,
    author_id INTEGER,
    commit_message TEXT,
    commit_time TIMESTAMP NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 代码文件表
CREATE TABLE code_files (
    id SERIAL PRIMARY KEY,
    commit_id INTEGER,
    file_path VARCHAR(500) NOT NULL,
    content TEXT,
    FOREIGN KEY (commit_id) REFERENCES code_commits(id) ON DELETE CASCADE
);

-- 代码检视问题表
CREATE TABLE review_issues (
    id SERIAL PRIMARY KEY,
    project_id INTEGER,
    commit_id INTEGER,
    file_id INTEGER,
    line_start INTEGER,
    line_end INTEGER,
    issue_type VARCHAR(50),
    description TEXT NOT NULL,
    severity issue_severity,
    priority issue_priority,
    status issue_status DEFAULT 'open',
    assignee_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (commit_id) REFERENCES code_commits(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES code_files(id) ON DELETE CASCADE,
    FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 代码检视评论表
CREATE TABLE review_comments (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER,
    user_id INTEGER,
    comment TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (issue_id) REFERENCES review_issues(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 问题修改历史表
CREATE TABLE issue_history (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER,
    user_id INTEGER,
    change_type VARCHAR(50) NOT NULL,
    change_description TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (issue_id) REFERENCES review_issues(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 权限表
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    code VARCHAR(255) NOT NULL UNIQUE,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES project_roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- 菜单表
CREATE TABLE menus (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    path VARCHAR(255),
    icon VARCHAR(255),
    parent_id INTEGER,
    order_num INTEGER DEFAULT 0,
    permission_code VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES menus(id) ON DELETE SET NULL
);

-- 角色菜单关联表
CREATE TABLE role_menus (
    role_id INTEGER NOT NULL,
    menu_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, menu_id),
    FOREIGN KEY (role_id) REFERENCES project_roles(id) ON DELETE CASCADE,
    FOREIGN KEY (menu_id) REFERENCES menus(id) ON DELETE CASCADE
);

-- 通知表
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    recipient_id INTEGER,
    issue_id INTEGER,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (issue_id) REFERENCES review_issues(id) ON DELETE CASCADE
);

-- 代码热点分析表
CREATE TABLE code_hotspots (
    id SERIAL PRIMARY KEY,
    file_id INTEGER,
    issue_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (file_id) REFERENCES code_files(id) ON DELETE CASCADE
);

-- CI/CD 记录表
CREATE TABLE ci_cd_records (
    id SERIAL PRIMARY KEY,
    commit_id INTEGER,
    status ci_cd_status,
    log TEXT,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (commit_id) REFERENCES code_commits(id) ON DELETE CASCADE
);

-- 初始化角色数据
INSERT INTO users (username, email, password_hash, role, created_at) VALUES
('admin', 'admin@example.com', '$2b$12$5uVMWmGeeWMT2YPPs0jv.ebi6qvD.8Hp6eHu2SogY9d9Qo1cLm4qC', 'admin', CURRENT_TIMESTAMP),
('developer', 'developer@codereview.com', '$2b$12$rXKGH7W9JcC3Zq3vVjQ0DeN8q1TpO1sFwzLm2YhH5bRqA7nSvkPO', 'developer', CURRENT_TIMESTAMP),
('reviewer', 'reviewer@codereview.com', '$2b$12$tYhL8kqZdO7wS3eZvJn9BeY1qjz4WpQ2sXnM1rPcU6lVdA5qH7Dm', 'reviewer', CURRENT_TIMESTAMP); -- 使用bcrypt算法生成的统一密码哈希（测试密码：Admin@123）

-- 添加默认项目
INSERT INTO projects (name, repository_url, created_by, created_at) VALUES
('示例项目', 'https://github.com/example/code-review-project.git', 1, CURRENT_TIMESTAMP);

-- 添加项目角色
INSERT INTO project_roles (project_id, user_id, role, assigned_at) VALUES
(1, 1, 'admin', CURRENT_TIMESTAMP),
(1, 2, 'developer', CURRENT_TIMESTAMP),
(1, 3, 'architect', CURRENT_TIMESTAMP);

-- 初始化权限数据
INSERT INTO permissions (code, description) VALUES
('user:view', '查看用户'),
('user:create', '创建用户'),
('user:edit', '编辑用户'),
('user:delete', '删除用户'),
('user:transfer', '转移用户'),
('project:view', '查看项目'),
('project:create', '创建项目'),
('project:edit', '编辑项目'),
('project:delete', '删除项目'),
('issue:view', '查看问题'),
('issue:create', '创建问题'),
('issue:edit', '编辑问题'),
('issue:delete', '删除问题'),
('code:review', '代码审查'),
('code:analyze', '代码分析');

-- 初始化菜单数据
INSERT INTO menus (title, path, icon, parent_id, order_num, permission_code) VALUES
('系统管理', '/system', 'SettingOutlined', NULL, 1, NULL),
('权限管理', '/system/permission', 'LockOutlined', 1, 1, NULL),
('用户列表', '/system/permission/users', 'UserOutlined', 2, 1, 'user:view'),
('项目管理', '/projects', 'ProjectOutlined', NULL, 2, 'project:view'),
('问题管理', '/issues', 'BugOutlined', NULL, 3, 'issue:view'),
('代码审查', '/code-review', 'CodeOutlined', NULL, 4, 'code:review'),
('代码分析', '/code-analysis', 'BarChartOutlined', NULL, 5, 'code:analyze');

-- 为默认角色分配权限
INSERT INTO role_permissions (role_id, permission_id) 
SELECT 
    pr.id as role_id,
    p.id as permission_id
FROM project_roles pr
CROSS JOIN permissions p
WHERE 
    (pr.role = 'admin') -- 管理员拥有所有权限
    OR (pr.role = 'developer' AND p.code IN (
        'project:view', 'issue:view', 'issue:create', 'issue:edit',
        'code:review'
    ))
    OR (pr.role = 'architect' AND p.code IN (
        'project:view', 'project:edit', 'issue:view', 'issue:create',
        'issue:edit', 'code:review', 'code:analyze'
    ));

-- 为默认角色分配菜单
INSERT INTO role_menus (role_id, menu_id)
SELECT 
    pr.id as role_id,
    m.id as menu_id
FROM project_roles pr
CROSS JOIN menus m
WHERE 
    (pr.role = 'admin') -- 管理员拥有所有菜单
    OR (pr.role = 'developer' AND m.path IN (
        '/projects', '/issues', '/code-review'
    ))
    OR (pr.role = 'architect' AND m.path IN (
        '/projects', '/issues', '/code-review', '/code-analysis'
    ));

-- 添加示例代码提交记录
INSERT INTO code_commits (commit_id, project_id, repository, branch, author_id, commit_message, commit_time) VALUES
('a1b2c3d4', 1, 'https://github.com/example/code-review-project.git', 'main', 2, '初始化项目结构', CURRENT_TIMESTAMP),
('e5f6g7h8', 1, 'https://github.com/example/code-review-project.git', 'feature/user-management', 2, '添加用户管理功能', CURRENT_TIMESTAMP);

-- 添加示例代码文件
INSERT INTO code_files (commit_id, file_path, content) VALUES
(1, 'src/users/users.service.ts', 'export class UsersService {\n  // 用户服务实现\n}'),
(1, 'src/users/users.controller.ts', 'export class UsersController {\n  // 用户控制器实现\n}');

-- 添加示例问题
INSERT INTO review_issues (project_id, commit_id, file_id, line_start, line_end, issue_type, description, severity, priority, status, assignee_id) VALUES
(1, 1, 1, 10, 15, 'code_style', '建议使用接口定义服务方法', 'low', 'low', 'open', 2),
(1, 1, 2, 5, 8, 'security', '需要添加权限验证', 'high', 'high', 'open', 3);

-- 添加示例评论
INSERT INTO review_comments (issue_id, user_id, comment) VALUES
(1, 3, '请参考项目规范文档进行修改'),
(2, 1, '已添加TODO标记，下个迭代处理');

-- 添加示例问题历史
INSERT INTO issue_history (issue_id, user_id, change_type, change_description) VALUES
(1, 2, 'status_change', '问题状态从 new 变更为 open'),
(2, 1, 'assignee_change', '指派给 reviewer 用户');

-- 添加示例通知
INSERT INTO notifications (recipient_id, issue_id, message) VALUES
(2, 1, '您有一个新的代码审查任务'),
(3, 2, '您被指派了一个高优先级的安全问题');

-- 添加示例代码热点
INSERT INTO code_hotspots (file_id, issue_count) VALUES
(1, 2),
(2, 1);

-- 添加示例CI/CD记录
INSERT INTO ci_cd_records (commit_id, status, log) VALUES
(1, 'success', 'Build and tests passed successfully'),
(2, 'pending', 'Waiting for test execution');