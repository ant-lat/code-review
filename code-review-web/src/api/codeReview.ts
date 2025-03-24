import { get, post, put, del } from './request';
import type { 
  ResponseBase, 
  CodeReview, 
  CodeReviewComment, 
  CodeReviewCommentCreateParams,
  PageResponse
} from './types';

export interface CodeReviewQueryParams {
  page?: number;
  page_size?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
  project_id?: number;
}

/**
 * 获取代码审查列表
 * @param params 查询参数
 */
export function getCodeReviews(params: CodeReviewQueryParams = {}): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/code-reviews', params);
}

/**
 * 获取单个代码审查
 * @param id 代码审查ID
 */
export function getCodeReviewById(id: number): Promise<ResponseBase<CodeReview>> {
  return get<ResponseBase<CodeReview>>(`/code-reviews/issues/${id}`);
}

/**
 * 创建代码审查
 * @param data 代码审查数据
 */
export function createCodeReview(data: Partial<CodeReview>): Promise<ResponseBase<CodeReview>> {
  return post<ResponseBase<CodeReview>>('/code-reviews/issues', data);
}

/**
 * 更新代码审查
 * @param id 代码审查ID
 * @param data 更新数据
 */
export function updateCodeReview(id: number, data: Partial<CodeReview>): Promise<ResponseBase<CodeReview>> {
  return put<ResponseBase<CodeReview>>(`/code-reviews/issues/${id}`, data);
}

/**
 * 删除代码审查
 * @param id 代码审查ID
 */
export function deleteCodeReview(id: number): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/code-reviews/issues/${id}`);
}

/**
 * 提交代码审查结果
 * @param id 代码审查ID
 * @param data 审查结果数据
 */
export function submitCodeReviewResult(
  id: number, 
  data: { status: string; review_notes: string }
): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>(`/code-reviews/issues/${id}/submit`, data);
}

/**
 * 获取代码审查评论
 * @param reviewId 代码审查ID
 */
export function getCodeReviewComments(reviewId: number): Promise<ResponseBase<any[]>> {
  return get<ResponseBase<any[]>>(`/code-reviews/issues/${reviewId}/comments`);
}

/**
 * 添加代码审查评论
 * @param reviewId 代码审查ID
 * @param data 评论数据
 */
export function addCodeReviewComment(
  reviewId: number,
  data: { content: string; file_path?: string; line_number?: number }
): Promise<ResponseBase<any>> {
  return post<ResponseBase<any>>(`/code-reviews/issues/${reviewId}/comments`, data);
}

/**
 * 添加审查评论
 * @param reviewId 审查ID
 * @param params 评论参数
 */
export function addReviewComment(
  reviewId: number, 
  params: CodeReviewCommentCreateParams
): Promise<ResponseBase<CodeReviewComment>> {
  return post<ResponseBase<CodeReviewComment>>(`/code-reviews/issues/${reviewId}/comments`, {
    content: params.content,
    file_path: params.file_path,
    line_number: params.line_number
  });
}

/**
 * 获取审查详情
 * @param reviewId 审查ID
 */
export function getReviewDetail(reviewId: number): Promise<ResponseBase<CodeReview>> {
  return get<ResponseBase<CodeReview>>(`/code-reviews/issues/${reviewId}`);
}

/**
 * 获取审查评论列表
 * @param reviewId 审查ID
 * @param params 查询参数
 */
export function getReviewComments(
  reviewId: number,
  params: { page?: number; page_size?: number } = {}
): Promise<PageResponse<CodeReviewComment>> {
  return get<PageResponse<CodeReviewComment>>(`/code-reviews/issues/${reviewId}/comments`, params);
}

/**
 * 更新审查状态
 * @param reviewId 审查ID
 * @param status 状态
 */
export function updateReviewStatus(reviewId: number, status: string): Promise<ResponseBase<CodeReview>> {
  return put<ResponseBase<CodeReview>>(`/code-reviews/issues/${reviewId}/status`, { status });
}

/**
 * 分配审查人
 * @param reviewId 审查ID
 * @param reviewerId 审查人ID
 */
export function assignReviewer(reviewId: number, reviewerId: number): Promise<ResponseBase<CodeReview>> {
  return put<ResponseBase<CodeReview>>(`/code-reviews/issues/${reviewId}/assign`, { reviewer_id: reviewerId });
}

/**
 * 更新审查备注
 * @param reviewId 审查ID
 * @param notes 备注内容
 */
export function updateReviewNotes(reviewId: number, notes: string): Promise<ResponseBase<CodeReview>> {
  return put<ResponseBase<CodeReview>>(`/code-reviews/issues/${reviewId}/notes`, { notes });
}

/**
 * 删除审查评论
 * @param reviewId 审查ID
 * @param commentId 评论ID
 */
export function deleteReviewComment(reviewId: number, commentId: number): Promise<ResponseBase<any>> {
  return del<ResponseBase<any>>(`/code-reviews/issues/${reviewId}/comments/${commentId}`);
} 