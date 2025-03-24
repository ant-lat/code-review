import { get, post } from './request';
import type { ResponseBase, CodeAnalysisParams, CodeAnalysisResult, PageResponse } from './types';

/**
 * 获取代码结构
 * @param projectId 项目ID
 */
export function getCodeStructure(projectId: number): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/code-analysis/structure', { project_id: projectId });
}

/**
 * 获取代码质量
 * @param projectId 项目ID
 */
export function getCodeQuality(projectId: number): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/code-analysis/quality', { project_id: projectId });
}

/**
 * 获取代码热点
 * @param projectId 项目ID
 */
export function getCodeHotspots(projectId: number): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/code-analysis/hotspots', { project_id: projectId });
}

/**
 * 运行代码分析
 * @param params 分析参数
 */
export function runCodeAnalysis(params: CodeAnalysisParams): Promise<ResponseBase<CodeAnalysisResult>> {
  return post<ResponseBase<CodeAnalysisResult>>('/code-analysis/analyze', params);
}

/**
 * 获取分析历史
 * @param projectId 项目ID
 * @param page 页码
 * @param pageSize 每页数量
 */
export function getAnalysisHistory(
  projectId: number, 
  page: number = 1, 
  pageSize: number = 10
): Promise<PageResponse<any>> {
  return get<PageResponse<any>>('/code-analysis/history', { 
    project_id: projectId, 
    page,
    page_size: pageSize
  });
}

/**
 * 获取分析详情
 * @param analysisId 分析ID
 */
export function getAnalysisDetail(analysisId: number): Promise<ResponseBase<CodeAnalysisResult>> {
  return get<ResponseBase<CodeAnalysisResult>>(`/code-analysis/${analysisId}`);
}

/**
 * 对比两次分析结果
 * @param analysisId1 第一次分析ID
 * @param analysisId2 第二次分析ID
 */
export function compareAnalysisResults(
  analysisId1: number,
  analysisId2: number
): Promise<ResponseBase<any>> {
  return get<ResponseBase<any>>('/code-analysis/compare', {
    analysis_id_1: analysisId1,
    analysis_id_2: analysisId2
  });
} 