import { get, post, put, del } from './request';
import type { 
  ResponseBase,
  Issue,
  IssueCreateParams, 
  IssueUpdateParams, 
  IssueComment, 
  IssueCommentCreateParams,
  PageResponse 
} from './types';

export interface IssueQueryParams {
  page?: number;
  page_size?: number;
  keyword?: string;
  priority?: string;
  status?: string;
  assignee_id?: number;
  creator_id?: number;
  project_id?: number;
  tag_id?: number;
  issue_type?: string;
  created_after?: string;
  created_before?: string;
  sort_by?: string;
  sort_order?: string;
}

/**
 * 获取问题列表
 * @param params 查询参数
 * @returns 分页问题列表
 */
export function getIssues(params: IssueQueryParams = {}): Promise<PageResponse<Issue>> {
  return get<PageResponse<Issue>>('/issues', params);
}

/**
 * 获取问题详情
 * @param id 问题ID
 * @param silent 是否静默处理错误（不显示错误提示）
 * @returns 问题详情
 */
export function getIssueById(id: number, silent: boolean = true): Promise<ResponseBase<Issue>> {
  return get<ResponseBase<Issue>>(`/issues/${id}`, {}, { headers: { silent: String(silent) } });
}

/**
 * 创建问题
 * @param data 问题数据
 * @returns 创建的问题
 */
export function createIssue(data: Partial<Issue>): Promise<ResponseBase<Issue>> {
  return post<ResponseBase<Issue>>('/issues', data);
}

/**
 * 更新问题
 * @param id 问题ID
 * @param data 更新数据
 * @returns 更新后的问题
 */
export function updateIssue(id: number, data: Partial<Issue>): Promise<ResponseBase<Issue>> {
  return put<ResponseBase<Issue>>(`/issues/${id}`, data);
}

/**
 * 删除问题
 * @param id 问题ID
 * @returns 删除结果
 */
export function deleteIssue(id: number): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/issues/${id}`);
}

/**
 * 更新问题状态
 * @param id 问题ID
 * @param status 新状态
 * @returns 更新结果
 */
export function updateIssueStatus(id: number, status: string): Promise<ResponseBase<Issue>> {
  return put<ResponseBase<Issue>>(`/issues/${id}/status`, { status });
}

/**
 * 分配问题
 * @param id 问题ID
 * @param assigneeId 分配给用户的ID
 * @returns 更新结果
 */
export function assignIssue(id: number, assigneeId: number): Promise<ResponseBase<Issue>> {
  return put<ResponseBase<Issue>>(`/issues/${id}/assign`, { assignee_id: assigneeId });
}

/**
 * 获取问题评论
 * @param issueId 问题ID
 * @param silent 是否静默处理错误（不显示错误提示）
 * @returns 评论列表
 */
export function getIssueComments(issueId: number, silent: boolean = true): Promise<ResponseBase<any[]>> {
  return get<ResponseBase<any[]>>(`/issues/${issueId}/comments`, {}, { headers: { silent: String(silent) } });
}

/**
 * 添加问题评论
 * @param issueId 问题ID
 * @param content 评论内容
 * @param filePath 文件路径（可选）
 * @param lineNumber 行号（可选）
 * @returns 添加结果
 */
export function addIssueComment(issueId: number, content: string, filePath?: string, lineNumber?: number): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>(`/issues/${issueId}/comments`, { 
    content,
    file_path: filePath,
    line_number: lineNumber
  });
}

/**
 * 获取问题历史记录
 * @param issueId 问题ID
 * @param params 分页参数
 * @param silent 是否静默处理错误（不显示错误提示）
 */
export function getIssueHistory(
  issueId: number, 
  params: { page?: number; page_size?: number } = {},
  silent: boolean = true
): Promise<PageResponse<any>> {
  return get<PageResponse<any>>(`/issues/${issueId}/history`, params, { headers: { silent: String(silent) } });
}

/**
 * 关联问题到代码提交
 * @param issueId 问题ID
 * @param commitId 提交ID
 */
export function linkIssueToCommit(issueId: number, commitId: number): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>(`/issues/${issueId}/commits`, { commit_id: commitId });
}

/**
 * 获取问题关联的代码提交
 * @param issueId 问题ID
 * @param silent 是否静默处理错误（不显示错误提示）
 */
export function getIssueCommits(issueId: number, silent: boolean = true): Promise<ResponseBase<any[]>> {
  return get<ResponseBase<any[]>>(`/issues/${issueId}/commits`, {}, { headers: { silent: String(silent) } });
}

/**
 * 为问题添加标签
 * @param issueId 问题ID
 * @param tag 标签名
 */
export function addIssueTag(issueId: number, tag: string): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>(`/issues/${issueId}/tags`, { tag });
}

/**
 * 移除问题标签
 * @param issueId 问题ID
 * @param tag 标签名
 */
export function removeIssueTag(issueId: number, tag: string): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/issues/${issueId}/tags/${encodeURIComponent(tag)}`);
}

/**
 * 创建问题标签
 * @param name 标签名
 * @param color 标签颜色
 * @param description 标签描述
 */
export function createTag(name: string, color: string, description?: string): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>('/issues/tags', {
    name,
    color,
    description
  });
}

/**
 * 批量更新问题
 * @param issueIds 问题ID数组
 * @param data 更新数据
 */
export function batchUpdateIssues(issueIds: number[], data: {
  status?: string;
  priority?: string;
  assignee_id?: number;
  tags?: number[];
  project_id?: number;
}): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>('/issues/batch-update', {
    issue_ids: issueIds,
    ...data
  });
} 