package com.ant.code.coderplugin.api

import com.fasterxml.jackson.annotation.JsonProperty
import com.fasterxml.jackson.annotation.JsonIgnoreProperties

/**
 * API模型定义
 */
object ApiModels {
    /**
     * 用户信息
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class UserInfo(
        val id: Int,
        @JsonProperty("user_id") val userId: String? = null,
        val username: String,
        val email: String?,
        val phone: String? = null,
        val roles: List<Role>? = null,
        @JsonProperty("is_active") val isActive: Boolean? = true,
        @JsonProperty("created_at") val createdAt: String? = null,
        @JsonProperty("updated_at") val updatedAt: String? = null,
        val permissions: List<Permission>? = null
    ) {
        /**
         * 角色信息
         */
        @JsonIgnoreProperties(ignoreUnknown = true)
        data class Role(
            val id: Int? = null,
            val name: String? = null
        ) {
            companion object {
                @JvmStatic
                fun valueOf(value: String): Role {
                    return Role(name = value)
                }
                
                // Jackson反序列化用
                @JvmStatic
                fun from(value: Any): Role {
                    return when(value) {
                        is String -> Role(name = value)
                        is Map<*, *> -> {
                            val id = value["id"] as? Int
                            val name = value["name"] as? String
                            Role(id = id, name = name)
                        }
                        else -> Role(name = value.toString())
                    }
                }
            }
        }
        
        /**
         * 权限信息
         */
        @JsonIgnoreProperties(ignoreUnknown = true)
        data class Permission(
            val id: Int? = null,
            @JsonProperty("permission_id") val permissionId: Int? = null,
            val code: String? = null,
            val name: String? = null,
            val description: String? = null
        )
    }
    
    /**
     * 用户列表响应
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class UserListResponse(
        val items: List<UserInfo>,
        val total: Int,
        val page: Int,
        val size: Int,
        val pages: Int
    )
    
    /**
     * 登录请求
     */
    data class LoginRequest(
        @JsonProperty("user_id") val userId: String,
        val password: String,
        @JsonProperty("remember_me") val rememberMe: Boolean = false
    )
    
    /**
     * 登录响应
     */
    data class LoginResponse(
        @JsonProperty("access_token") val accessToken: String,
        @JsonProperty("refresh_token") val refreshToken: String?,
        @JsonProperty("expires_in") val expiresIn: Int,
        @JsonProperty("token_type") val tokenType: String = "bearer"
    )
    
    /**
     * API响应封装
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class ApiResponse<T>(
        val code: Int,
        val message: String,
        val timestamp: String? = null,
        val data: T? = null
    )
    
    /**
     * 分页响应
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class PageResponse<T>(
        val total: Int,
        val items: List<T>,
        val page: Int? = null,
        @JsonProperty("page_size") val size: Int? = null,
        @JsonProperty("total_pages") val pages: Int? = null
    )
    
    /**
     * 问题API特殊响应结构
     */
    data class IssueApiResponse<T>(
        val code: Int,
        val message: String,
        val timestamp: String? = null,
        val data: List<T>,
        @JsonProperty("page_info") val pageInfo: PageInfo
    ) {
        data class PageInfo(
            val page: Int,
            @JsonProperty("page_size") val pageSize: Int,
            val total: Int,
            @JsonProperty("total_pages") val totalPages: Int
        )
    }
    
    /**
     * 问题列表项
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class IssueListItem(
        val id: Int,
        val title: String,
        @JsonProperty("description") val description: String?,
        val status: String,
        val priority: String,
        @JsonProperty("issue_type") val issueType: String,
        val severity: String?,
        @JsonProperty("project_id") val projectId: Int,
        @JsonProperty("project_name") val projectName: String,
        @JsonProperty("creator_id") val creatorId: Int,
        @JsonProperty("creator_name") val creatorName: String,
        @JsonProperty("assignee_id") val assigneeId: Int?,
        @JsonProperty("assignee_name") val assigneeName: String?,
        @JsonProperty("file_path") val filePath: String?,
        @JsonProperty("line_start") val lineStart: Int?,
        @JsonProperty("line_end") val lineEnd: Int?,
        @JsonProperty("code_content") val codeContent: String?,
        @JsonProperty("commit_id") val commitId: Int?,
        @JsonProperty("resolution_time") val resolutionTime: Float?,
        @JsonProperty("created_at") val createdAt: String,
        @JsonProperty("updated_at") val updatedAt: String?,
        @JsonProperty("resolved_at") val resolvedAt: String?,
        @JsonProperty("closed_at") val closedAt: String?
    )
    
    /**
     * 项目信息
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class ProjectInfo(
        val id: Int,
        val name: String,
        val description: String,
        @JsonProperty("created_at") val createdAt: String,
        @JsonProperty("repository_url") val repositoryUrl: String? = null,
        @JsonProperty("repository_type") val repositoryType: String? = null,
        val branch: String? = null,
        val status: Boolean? = null,
        @JsonProperty("member_count") val memberCount: Int? = null,
        val creator: Creator? = null
    ) {
        data class Creator(
            val id: Int,
            val username: String,
            val email: String?
        )
    }
    
    /**
     * 问题创建请求
     */
    data class IssueCreateRequest(
        val title: String,
        val description: String,
        val priority: String,
        @JsonProperty("issue_type") val issueType: String,
        @JsonProperty("project_id") val projectId: Int,
        val severity: String? = null,
        @JsonProperty("assignee_id") val assigneeId: Int? = null,
        @JsonProperty("file_path") val filePath: String? = null,
        @JsonProperty("line_start") val lineStart: Int? = null,
        @JsonProperty("line_end") val lineEnd: Int? = null,
        @JsonProperty("code_content") val codeContent: String? = null,
        @JsonProperty("creator_id") val creatorId: Int? = null,
        val status: String = "open"
    )
    
    /**
     * 代码选择信息
     */
    data class CodeSelectionInfo(
        val className: String,
        val filePath: String,
        val lineStart: Int,
        val lineEnd: Int,
        val selectedCode: String,
        val commitInfo: CommitInfo? = null
    )
    
    /**
     * 提交信息
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class CommitInfo(
        val author: String,
        val date: String,
        val message: String,
        val hash: String
    )
    
    /**
     * 状态更新请求
     */
    data class StatusUpdateRequest(
        val status: String,
        val comment: String?
    )
    
    /**
     * 问题详细信息
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class IssueDetail(
        val id: Int,
        val title: String,
        val description: String?,
        val status: String,
        val priority: String?,
        val type: String?,
        @JsonProperty("file_path") val filePath: String?,
        @JsonProperty("line_start") val startLine: Int?,
        @JsonProperty("line_end") val endLine: Int?,
        @JsonProperty("code_snippet") val codeSnippet: String?,
        val creator: UserBrief?,
        val assignee: UserBrief?,
        @JsonProperty("created_at") val createdAt: String?,
        @JsonProperty("updated_at") val updatedAt: String?,
        @JsonProperty("resolved_at") val resolvedAt: String?,
        @JsonProperty("closed_at") val closedAt: String?,
        val comments: List<Comment>?
    ) {
        @JsonIgnoreProperties(ignoreUnknown = true)
        data class UserBrief(
            val id: Int,
            val username: String,
            val email: String?
        )
    }
    
    /**
     * 评论
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class Comment(
        val id: Int,
        val content: String?,
        val author: IssueDetail.UserBrief?,
        @JsonProperty("created_at") val createdAt: String?,
        @JsonProperty("updated_at") val updatedAt: String?
    )
    
    /**
     * 评论创建请求
     */
    data class CommentCreateRequest(
        val content: String
    )
    
    /**
     * 项目成员信息
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class ProjectMember(
        @JsonProperty("user_id") val userId: Int,
        val username: String,
        @JsonProperty("role_id") val roleId: Int,
        @JsonProperty("role_name") val roleName: String,
        @JsonProperty("is_active") val isActive: Boolean,
        @JsonProperty("joined_at") val joinedAt: String
    )
    
    /**
     * 问题字段更新请求
     */
    data class IssueUpdateRequest(
        val id: Int,
        val title: String?,
        val description: String?,
        val priority: String?,
        @JsonProperty("issue_type") val issueType: String?,
        val severity: String?,
        val status: String?,
        @JsonProperty("assignee_id") val assigneeId: Int?,
        @JsonProperty("project_id") val projectId: Int?
    )
    
    /**
     * 问题状态
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class IssueStatus(
        val id: String,
        val name: String,
        val description: String? = null,
        val color: String? = null,
        @JsonProperty("is_default") val isDefault: Boolean = false,
        @JsonProperty("is_closed") val isClosed: Boolean = false,
        @JsonProperty("sort_order") val sortOrder: Int = 0
    )
    
    /**
     * 提交详情
     */
    @JsonIgnoreProperties(ignoreUnknown = true)
    data class CommitDetail(
        val hash: String,
        val author: String,
        @JsonProperty("author_email") val authorEmail: String? = null,
        val message: String,
        val date: String,
        val files: List<CommitFile>? = null,
        val stats: CommitStats? = null
    ) {
        @JsonIgnoreProperties(ignoreUnknown = true)
        data class CommitFile(
            val filename: String,
            val status: String,
            val additions: Int = 0,
            val deletions: Int = 0,
            val changes: Int = 0
        )
        
        @JsonIgnoreProperties(ignoreUnknown = true)
        data class CommitStats(
            val additions: Int = 0,
            val deletions: Int = 0,
            val total: Int = 0
        )
    }
} 