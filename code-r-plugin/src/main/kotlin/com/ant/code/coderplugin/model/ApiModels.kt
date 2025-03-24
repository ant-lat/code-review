package com.ant.code.coderplugin.model

import com.fasterxml.jackson.annotation.JsonProperty
import java.time.LocalDateTime

// 通用响应模型
data class ApiResponse<T>(
    val code: Int,
    val message: String,
    val timestamp: String,
    val data: T
)

// 登录请求
data class LoginRequest(
    @JsonProperty("user_id") val userId: String,
    val password: String,
    @JsonProperty("remember_me") val rememberMe: Boolean = true
)

// 登录响应
data class LoginResponse(
    @JsonProperty("access_token") val accessToken: String,
    @JsonProperty("refresh_token") val refreshToken: String? = null,
    @JsonProperty("expires_in") val expiresIn: Int = 3600,
    @JsonProperty("token_type") val tokenType: String = "bearer"
)

// 用户信息
data class UserInfo(
    val id: Int,
    @JsonProperty("user_id") val userId: String,
    val username: String,
    val email: String?,
    val phone: String?,
    val roles: List<RoleInfo>,
    @JsonProperty("is_active") val isActive: Boolean,
    @JsonProperty("created_at") val createdAt: String
)

data class RoleInfo(
    val id: Int,
    val name: String,
    val description: String?
)

// 问题创建请求
data class IssueCreateRequest(
    @JsonProperty("project_id") val projectId: Int,
    val title: String,
    val description: String,
    val priority: String,
    @JsonProperty("issue_type") val issueType: String,
    @JsonProperty("assignee_id") val assigneeId: Int?,
    val severity: String?,
    @JsonProperty("file_path") val filePath: String?,
    @JsonProperty("line_start") val lineStart: Int?,
    @JsonProperty("line_end") val lineEnd: Int?,
    @JsonProperty("commit_id") val commitId: Int?
)

// 问题列表项
data class IssueListItem(
    val id: Int,
    @JsonProperty("project_id") val projectId: Int,
    @JsonProperty("project_name") val projectName: String,
    val title: String, 
    val status: String,
    val priority: String,
    @JsonProperty("issue_type") val issueType: String,
    val severity: String?,
    @JsonProperty("creator_id") val creatorId: Int,
    @JsonProperty("creator_name") val creatorName: String,
    @JsonProperty("assignee_id") val assigneeId: Int?,
    @JsonProperty("assignee_name") val assigneeName: String?,
    @JsonProperty("file_path") val filePath: String?,
    @JsonProperty("line_start") val lineStart: Int?,
    @JsonProperty("line_end") val lineEnd: Int?,
    @JsonProperty("resolution_time") val resolutionTime: Float?,
    @JsonProperty("created_at") val createdAt: String,
    @JsonProperty("updated_at") val updatedAt: String?
)

// 分页响应
data class PageResponse<T>(
    val items: List<T>,
    val total: Int,
    val page: Int,
    @JsonProperty("page_size") val pageSize: Int
)

// 问题状态更新请求
data class StatusUpdateRequest(
    val status: String,
    val comment: String?
)

// 提交信息
data class CommitInfo(
    val author: String,
    val date: String,
    val message: String,
    val hash: String
)

// 项目信息
data class ProjectInfo(
    val id: Int,
    val name: String,
    val description: String?,
    @JsonProperty("repository_url") val repositoryUrl: String?
)

// 用于问题创建界面的数据模型
data class CodeSelectionInfo(
    val className: String,
    val filePath: String,
    val lineStart: Int,
    val lineEnd: Int,
    val selectedCode: String,
    val commitInfo: CommitInfo?
) 