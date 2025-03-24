import { get } from './request';
import type { ResponseBase, PageResponse } from './types';

interface DashboardStats {
  status_distribution: {
    status: string;
    count: number;
  }[];
  type_distribution: {
    issue_type: string;
    count: number;
  }[];
  avg_resolution_time: number;
  team_workload: {
    username: string;
    open_count: number;
  }[];
  project_issue_distribution: {
    project_name: string;
    total_issues: number;
  }[];
  trend_analysis: {
    points: {
      date: string;
      new_issues: number;
      resolved_issues: number;
    }[];
  };
}

interface TeamWorkload {
  user_id: number;
  username: string;
  assigned_issues: number;
  completed_issues: number;
  pending_reviews: number;
}

interface ProjectStats {
  project_id: number;
  project_name: string;
  total_issues: number;
  open_issues: number;
  closed_issues: number;
  average_resolution_time: number;
}

interface TrendData {
  date: string;
  opened: number;
  closed: number;
}

interface UserPerformance {
  user_id: number;
  username: string;
  resolved_issues: number;
  created_issues: number;
  reviews_completed: number;
  average_resolution_time: number;
}

interface RecentActivity {
  id: number;
  user_id: number;
  username: string;
  action: string;
  entity_type: string;
  entity_id: number;
  entity_name: string;
  created_at: string;
}

interface StatusDistribution {
  status: string;
  count: number;
  percentage: number;
}

interface TypeDistribution {
  type: string;
  count: number;
  percentage: number;
}

/**
 * 获取仪表盘统计数据
 * @param dateFilters 可选的日期过滤条件
 */
export function getDashboardStats(dateFilters?: { 
  start_date?: string, 
  end_date?: string 
}): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/stats', dateFilters);
}

/**
 * 获取团队工作负载
 */
export function getTeamWorkload(): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/team-workload');
}

/**
 * 获取项目统计
 */
export function getProjectStats(): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/project-stats');
}

/**
 * 获取问题趋势
 * @param days 分析的天数
 */
export function getTrendAnalysis(days: number = 30): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/trend', { days });
}

/**
 * 获取所有用户性能
 * @param dateFilters 可选的日期过滤条件
 */
export function getAllUserPerformance(dateFilters?: { 
  start_date?: string, 
  end_date?: string 
}): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/user-performance', dateFilters);
}

/**
 * 获取单个用户性能
 * @param userId 用户ID
 */
export function getUserPerformance(userId: number): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>(`/dashboard/user-performance/${userId}`);
}

/**
 * 获取最近活动
 * @param page 页码
 * @param pageSize 每页数量
 */
export function getRecentActivity(
  page: number = 1, 
  pageSize: number = 10
): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/recent-activity', { 
    page, 
    page_size: pageSize 
  });
}

/**
 * 获取状态分布
 */
export function getStatusDistribution(): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/status-distribution');
}

/**
 * 获取类型分布
 */
export function getTypeDistribution(): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/type-distribution');
}

/**
 * 获取平均解决时间（小时）
 */
export function getResolutionTime(): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/dashboard/resolution-time');
} 