import axios from 'axios';
import qs from 'qs';
import { message } from 'antd';

// API响应类型定义
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page?: number;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  token_creation_time: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
  token_creation_time: string;
}

export interface PermissionCheckResponse {
  has_permission: boolean;
  required_role: string;
  current_roles: string[];
}

export interface UserInfo {
  id: number;
  username: string;
  role: string;
  email?: string;
}

export interface Project {
  id: number;
  name: string;
  repository_url: string;
  created_by: number;
  created_at: string;
}

export interface Repository {
  repo_type: 'git' | 'svn';
  url: string;
  branch?: string;
  commit_hash?: string;
  tag?: string;
}

export interface ProjectCreate {
  name: string;
  repository_url: string;
}

export interface UserCreate {
  username: string;
  email: string;
  password: string;
  role: string;
}

export interface Issue {
  id: number;
  project_id: number;
  title: string;
  severity: 'high' | 'medium' | 'low';
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  description: string;
  created_at: string;
  assignee?: number;
}

export interface IssueCreate {
  project_id: number;
  title: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
}

export interface CodeCheckRequest {
  project_id: number;
  scan_type: 'full' | 'incremental' | 'multi-repo' | 'cross-repo';
  repositories?: Repository[];
  comparison_strategy?: 'branch-diff' | 'cross-repo-diff';
  target_branch?: string;
}

export interface CodeCheckResponse {
  id: string;
  status: string;
  metrics: {
    cyclomatic_complexity: number;
    code_smells: number;
    security_vulnerabilities: number;
  };
  scan_duration: number;
  report_url: string;
}

export interface RolePermission {
  permission_id: number;
  expire_time?: string;
}

export interface DashboardStats {
  status_distribution: Array<{
    status: string;
    count: number;
  }>;
  type_distribution: Array<{
    issue_type: string;
    count: number;
  }>;
  avg_resolution_time: number;
  team_workload: Array<{
    username: string;
    open_count: number;
  }>;
  project_issue_distribution: Array<{
    project_name: string;
    total_issues: number;
  }>;
}

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    console.log('Request interceptor - Token:', token);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log('Request config:', config);
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    console.log('Response interceptor - Success:', response);
    return response.data;
  },
  (error) => {
    console.error('Response interceptor - Error:', error);
    if (error.response) {
      switch (error.response.status) {
        case 400:
          message.error('请求参数错误');
          break;
        case 401:
          // 尝试刷新token
          if (!error.config.url.includes('/auth/refresh')) {
            return authAPI.refreshToken().then(response => {
              localStorage.setItem('token', response.access_token);
              error.config.headers.Authorization = `Bearer ${response.access_token}`;
              return api.request(error.config);
            }).catch(() => {
              localStorage.removeItem('token');
              localStorage.removeItem('user');
              window.location.href = '/login';
            });
          }
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
          break;
        case 403:
          message.error('没有权限访问该资源');
          break;
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error('服务器错误');
          break;
        default:
          message.error('发生错误: ' + error.response.data?.message || '未知错误');
      }
    }
    return Promise.reject(error);
  }
);

// API接口
export const authAPI = {
  login: async (data: { username: string; password: string }): Promise<LoginResponse> => {
    return api.post('/auth/login', {
      user_id: data.username,
      password: data.password
    });
  },

  getCurrentUser: async (): Promise<UserInfo> => {
    const response = await api.get<UserInfo>('/auth/getUser');
    console.log('getCurrentUser response:', response);
    return response.data;
  },

  refreshToken: async (): Promise<RefreshTokenResponse> => {
    const response = await api.post('/auth/refresh');
    return response.data;
  },

  checkPermission: async (): Promise<UserInfo> => {
    const response = await api.get<UserInfo>('/auth/getUser');
    return response.data;
  }
};

export const usersAPI = {
  getList: (params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<UserInfo>> => 
    api.get('/users', { params }),
  
  create: (data: UserCreate): Promise<UserInfo> => 
    api.post('/users', data),
};

export const projectsAPI = {
  getList: (params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<Project>> => 
    api.get('/projects', { params }),
  
  getById: (id: number): Promise<Project> => 
    api.get(`/projects/${id}`),
  
  create: (data: ProjectCreate): Promise<Project> => 
    api.post('/projects', data),
  
  updateRepositories: (projectId: number, data: { repositories: Repository[] }) =>
    api.put(`/projects/${projectId}/repositories`, data),
  
  getMembers: (projectId: number): Promise<UserInfo[]> => 
    api.get(`/projects/${projectId}/users`),
  
  addMember: (projectId: number, data: { user_id: number; role: string }) =>
    api.post(`/projects/${projectId}/users`, data),
  
  removeMember: (projectId: number, userId: number) =>
    api.delete(`/projects/${projectId}/users/${userId}`),
  
  getStatistics: (projectId: number) =>
    api.get(`/projects/${projectId}/statistics`),
};

export const issuesAPI = {
  create: (data: IssueCreate): Promise<Issue> => 
    api.post('/issues', data),
  
  getList: (params?: { 
    project_id?: number;
    status?: string;
    severity?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Issue>> => 
    api.get('/issues', { params }),
  
  getById: (id: number): Promise<Issue> =>
    api.get(`/issues/${id}`),
  
  updateStatus: (issueId: number, status: string) =>
    api.put(`/issues/${issueId}`, { status }),
  
  assign: (issueId: number, userId: number) =>
    api.put(`/issues/${issueId}/assign`, { assignee: userId }),
};

export const codeAPI = {
  runCheck: (data: CodeCheckRequest): Promise<CodeCheckResponse> =>
    api.post('/code/check', data),
  
  getCheckStatus: (checkId: string): Promise<CodeCheckResponse> =>
    api.get(`/code/check/${checkId}`),
};

export const rolesAPI = {
  updatePermissions: (roleId: number, data: {
    permissions: RolePermission[];
    operation_type: 'append' | 'remove';
  }) => 
    api.post(`/roles/${roleId}/permissions`, data),
};

export const dashboardAPI = {
  getStats: async (): Promise<DashboardStats> => {
    return api.get('/dashboard/stats');
  },
};

// WebSocket通知服务
export class NotificationService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private heartbeatInterval: NodeJS.Timeout | null = null;

  connect() {
    if (!this.ws) {
      const token = localStorage.getItem('token');
      this.ws = new WebSocket(`ws://localhost:8000/api/v1/notifications?token=${token}`);
      
      this.ws.onopen = () => {
        console.log('WebSocket连接已建立');
        this.reconnectAttempts = 0;
        this.startHeartbeat();
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleNotification(data);
      };

      this.ws.onclose = () => {
        console.log('WebSocket连接已关闭');
        this.stopHeartbeat();
        this.reconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
      };
    }
  }

  private startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'heartbeat' }));
      }
    }, 30000);
  }

  private stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`尝试重新连接... 第${this.reconnectAttempts}次`);
        this.connect();
      }, 3000);
    }
  }

  private handleNotification(data: any) {
    switch (data.event_type) {
      case 'issue_update':
        message.info(`问题 #${data.issue_id} 状态已更新`);
        break;
      case 'scan_completed':
        message.success(`项目 #${data.project_id} 的代码扫描已完成`);
        break;
      case 'permission_changed':
        message.info('您的权限已更新，请刷新页面');
        break;
    }
  }

  disconnect() {
    if (this.ws) {
      this.stopHeartbeat();
      this.ws.close();
      this.ws = null;
    }
  }
}

export const notificationService = new NotificationService();

export default api; 