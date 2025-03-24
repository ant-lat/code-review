/**
 * API类型定义
 * @author Claude
 * @date 2023-07-15
 */

// API响应基础结构
export interface ResponseBase<T> {
  code: number;
  message?: string;
  data: T;
}

// 分页信息
export interface PageInfo {
  page: number;
  size: number;
  total: number;
  pages: number;
}

// 分页响应
export interface PageResponse<T> {
  code: number;
  message?: string;
  data: T[];
  total: number;
  page: number;
  page_size: number;
}

// 用户相关
export interface User {
  id: number;
  user_id: string;   // 用户登录ID
  username: string;  // 用户真实姓名
  email?: string;
  phone?: string;
  is_active: boolean;
  created_at: string;
  roles: string[];
}

export interface UserRole {
  id: number;
  name: string;
  description: string;
  permissions: string[];
}

export interface UserCreateParams {
  user_id: string;    // 用户登录ID
  username: string;   // 用户真实姓名
  email?: string;
  phone?: string;
  password?: string;
  role_id?: number;
  role_ids?: number[];
}

export interface UserUpdateParams {
  user_id?: string;
  username?: string;
  email?: string;
  phone?: string;
  is_active?: boolean;
  permissions?: string[];
}

export interface PasswordChangeParams {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetParams {
  user_id: number;
  new_password: string;
  confirm_password: string;
}

export interface PasswordResetRequestParams {
  user_id: string;
}

export interface PasswordResetVerifyParams {
  user_id: string;
  verification_type: string;
  answer: string;
}

export interface PasswordResetCompleteParams {
  user_id: string;
  verification_type: string;
  answer: string;
  new_password: string;
  confirm_password: string;
}

// 权限相关
export interface Permission {
  id: number;
  code: string;
  name: string;
  description: string;
  group: string;
}

export interface PermissionGroup {
  group: string;
  permissions: Permission[];
}

export interface RolePermissionParams {
  role_id: number;
  permission_ids: number[];
}

export interface UserPermissionParams {
  user_id: number;
  permission_ids: number[];
}

// 项目相关
export interface Project {
  id: number;
  name: string;
  description: string;
  repository_url: string;
  repository_type: string;
  branch: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  created_by: number;
  owner_id: number;
}

// 通用查询参数
export interface BaseQueryParams {
  page?: number;
  page_size?: number;
}

// 项目查询参数
export interface ProjectQueryParams extends BaseQueryParams {
  name?: string;
  repository_type?: 'git' | 'svn' | 'gitlab' | 'github';
  is_active?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

// 项目创建参数
export interface ProjectCreateParams {
  name: string;
  description?: string;
  repository_url: string;
  repository_type?: string;
  branch?: string;
  is_active?: boolean;
}

// 项目更新参数
export interface ProjectUpdateParams {
  name?: string;
  description?: string;
  repository_url?: string;
  repository_type?: string;
  branch?: string;
  is_active?: boolean;
}

// 项目响应数据
export interface ProjectResponse {
  id: number;
  name: string;
  description?: string;
  repository_url: string;
  repository_type: string;
  branch: string;
  is_active: boolean;
  created_by: number;
  creator_name?: string;
  created_at: string;
  updated_at?: string;
}

export interface ProjectMember {
  id: number;
  project_id: number;
  user_id: number;
  user: {
    id: number;
    username: string;
    email: string;
    avatar?: string;
  };
  role: string;
  created_at: string;
}

export interface ProjectPermission {
  id: number;
  code: string;
  name: string;
  description: string;
}

export interface ProjectRolePermissionParams {
  project_id: number;
  role: string;
  permission_ids: number[];
}

// 问题相关
export interface Issue {
  id: number;
  title: string;
  description?: string;
  severity: string;
  status: string;
  project_id: number;
  project_name?: string;
  assignee_id?: number;
  assignee_name?: string;
  reporter_id: number;
  reporter_name?: string;
  created_at: string;
  updated_at?: string;
  closed_at?: string;
  due_date?: string;
  priority?: string;
  labels?: string[];
  related_issues?: number[];
}

export interface IssueCreateParams {
  title: string;
  description: string;
  project_id: number;
  assignee_id?: number;
  status?: string;
  priority?: string;
  issue_type?: string;
  tags?: string[];
}

export interface IssueUpdateParams {
  title?: string;
  description?: string;
  assignee_id?: number;
  status?: string;
  priority?: string;
  issue_type?: string;
}

export interface IssueComment {
  id: number;
  issue_id: number;
  user_id: number;
  content: string;
  created_at: string;
  updated_at: string;
  user?: User;
}

export interface IssueCommentCreateParams {
  content: string;
}

// 代码分析相关
export interface CodeAnalysisParams {
  project_id: number;
  commit_id?: string;
  analysis_type?: string[];
  options?: Record<string, any>;
}

export interface CodeAnalysisResult {
  id: number;
  project_id: number;
  commit_id: string;
  started_at: string;
  completed_at: string;
  status: string;
  results: Record<string, any>;
  user_id: number;
}

// 代码审查相关
export interface CodeReview {
  id: number;
  project_id: number;
  project_name?: string;
  commit_id: string;
  review_notes?: string;
  status: string;
  reviewer_id: number;
  reviewer_name?: string;
  created_at: string;
  updated_at?: string;
}

export interface CodeReviewCreateParams {
  title: string;
  description: string;
  project_id: number;
  reviewer_id?: number;
  commit_id?: string;
  branch?: string;
}

export interface CodeReviewUpdateParams {
  title?: string;
  description?: string;
  reviewer_id?: number;
  status?: string;
  notes?: string;
}

export interface CodeReviewComment {
  id: number;
  review_id: number;
  user_id: number;
  file_path: string;
  line_number?: number;
  content: string;
  created_at: string;
  user?: User;
}

export interface CodeReviewCommentCreateParams {
  file_path: string;
  line_number?: number;
  content: string;
}

// 通知相关
export interface Notification {
  id: number;
  user_id: number;
  title: string;
  content: string;
  notification_type: string;
  is_read: boolean;
  created_at: string;
  issue_id?: number;
  source_id?: number;
  source_type?: string;
  link?: string;
}

export interface NotificationTypeInfo {
  value: string;
  label: string;
  description: string;
}

// 通知计数
export interface NotificationCount {
  count: number;
}

export interface NotificationUpdateRequest {
  notification_ids: number[];
}

export interface NotificationDeleteRequest {
  notification_ids: number[];
}

// 登录相关类型
export interface LoginParams {
  user_id: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  user?: User;
} 