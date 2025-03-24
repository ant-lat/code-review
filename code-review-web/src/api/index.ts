/**
 * API模块导出
 */
import { get, post, put, del, cancelAllRequests } from './request';
import useApi from '../hooks/useApi';

// 直接导出请求方法和钩子
export {
  get,
  post,
  put,
  del,
  useApi,
  cancelAllRequests
};

// 命名空间导出各个模块API
export * as authApi from './auth';
export * as usersApi from './users';
export * as projectsApi from './projects';
export * as issuesApi from './issues';
export * as codeReviewApi from './codeReview';
export * as codeAnalysisApi from './codeAnalysis';
export * as dashboardApi from './dashboard';
export * as notificationsApi from './notifications';
export * as permissionApi from './permission';

// 导出类型定义
export * from './types'; 