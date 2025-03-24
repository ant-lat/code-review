package com.ant.code.coderplugin.service

import com.ant.code.coderplugin.api.ApiModels
import com.ant.code.coderplugin.api.ApiService
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.psi.PsiFile
import com.intellij.psi.PsiManager
import git4idea.repo.GitRepositoryManager
import git4idea.history.GitHistoryUtils
import git4idea.history.GitLogParser
import com.intellij.openapi.Disposable
import com.intellij.openapi.util.Disposer
import com.intellij.openapi.util.TextRange
import kotlin.math.min
import com.ant.code.coderplugin.ProjectManager as CodeReviewProjectManager

@Service(Service.Level.PROJECT)
class IssueService(private val project: Project) : Disposable {
    private val apiService = ApiService.getInstance(project)
    // 添加缓存集合
    private val projectCache = mutableMapOf<Int, ApiModels.ProjectInfo>()
    private val issueCache = mutableMapOf<Int, ApiModels.IssueListItem>()
    
    private var isLoadingIssues = false
    private val issueListCache = mutableMapOf<String, Pair<List<ApiModels.IssueListItem>, Long>>() // 缓存的问题列表和时间戳
    
    // 获取项目列表
    private var isLoadingProjects = false
    private var projectListCache: Pair<List<ApiModels.ProjectInfo>, Long>? = null // 缓存的项目列表和时间戳
    
    // 添加用户列表缓存
    private var isLoadingUsers = false
    private val usersCache = mutableMapOf<Int, List<ApiModels.UserInfo>>() // 项目ID -> 用户列表
    private var globalUsersCache: Pair<List<ApiModels.UserInfo>, Long>? = null // 全局用户列表和时间戳
    
    // 添加项目成员缓存
    private var isLoadingMembers = false
    private val projectMembersCache = mutableMapOf<Int, List<ApiModels.ProjectMember>>() // 项目ID -> 成员列表
    
    init {
        // 注册到项目的生命周期
        Disposer.register(project, this)
    }
    
    // 确保资源在插件卸载时被释放
    override fun dispose() {
        try {
            // 释放所有可能的资源
            Runtime.getRuntime().removeShutdownHook(Thread.currentThread())
            
            // 清除对其他服务的引用
            // 不直接置空apiService，因为它是val，但会在ApiService自己的dispose中清理
            
            println("[DEBUG] IssueService resources released")
        } catch (e: Exception) {
            println("[ERROR] Error disposing IssueService: ${e.message}")
            e.printStackTrace()
        }
    }
    
    // 获取用户问题列表
    fun getUserIssues(page: Int = 1, pageSize: Int = 50): List<ApiModels.IssueListItem> {
        // 如果正在加载，则返回缓存的数据
        if (isLoadingIssues) {
            println("[INFO] 已有正在进行的问题列表请求，返回缓存数据")
            val cacheKey = "${page}_${pageSize}"
            val cachedData = issueListCache[cacheKey]
            if (cachedData != null) {
                val (items, timestamp) = cachedData
                // 检查缓存是否过期(5分钟)
                if (System.currentTimeMillis() - timestamp < 300000) {
                    println("[DEBUG] 返回缓存的问题列表，数量: ${items.size}")
                    return items
                }
            }
            return emptyList() // 没有可用缓存
        }

        try {
            isLoadingIssues = true
            println("[DEBUG] 获取用户问题列表，页码: $page, 每页数量: $pageSize")
            
            val cacheKey = "${page}_${pageSize}"
            
            // 检查缓存
            val cachedData = issueListCache[cacheKey]
            if (cachedData != null) {
                val (items, timestamp) = cachedData
                // 检查缓存是否过期(5分钟)
                if (System.currentTimeMillis() - timestamp < 300000) {
                    println("[DEBUG] 返回缓存的问题列表，数量: ${items.size}")
                    isLoadingIssues = false
                    return items
                }
            }
            
            // 调用API服务获取问题列表
            val response = apiService.getUserIssues(page, pageSize)
            
            if (response != null && response.code == 200 && response.data != null) {
                val items = response.data.items
                println("[DEBUG] 成功获取问题列表，数量: ${items.size}")
                
                // 更新缓存
                issueListCache[cacheKey] = Pair(items, System.currentTimeMillis())
                
                isLoadingIssues = false
                return items
            } else {
                val errorMessage = response?.message ?: "未知错误"
                println("[ERROR] 获取问题列表失败: $errorMessage")
            }
        } catch (e: Exception) {
            println("[ERROR] 获取问题列表时发生异常: ${e.message}")
            e.printStackTrace()
        } finally {
            isLoadingIssues = false
        }
        
        // 如果失败但有缓存，返回缓存的数据
        val cacheKey = "${page}_${pageSize}"
        val cachedData = issueListCache[cacheKey]
        if (cachedData != null) {
            val (items, _) = cachedData
            println("[WARN] 使用过期缓存的问题列表，数量: ${items.size}")
            return items
        }
        
        return emptyList()
    }
    
    // 清除问题列表缓存
    fun clearIssueListCache() {
        println("[DEBUG] 清除问题列表缓存")
        issueListCache.clear()
    }
    
    // 创建问题
    fun createIssue(request: ApiModels.IssueCreateRequest): ApiModels.ApiResponse<ApiModels.IssueListItem>? {
        try {
            return apiService.createIssue(request)
        } catch (e: Exception) {
            println("[ERROR] 创建问题异常: ${e.message}")
            e.printStackTrace()
            return ApiModels.ApiResponse(
                code = 500,
                message = "创建问题失败: ${e.message}",
                data = null
            )
        }
    }
    
    // 更新问题状态
    fun updateIssueStatus(issueId: Int, status: String, comment: String? = null, maxRetries: Int = 3): Boolean {
        var retryCount = 0
        var lastException: Exception? = null
        
        while (retryCount < maxRetries) {
            try {
                val statusUpdate = ApiModels.StatusUpdateRequest(status, comment)
                val response = apiService.updateIssueStatus(issueId, statusUpdate)
                
                if (response != null && response.code == 200) {
                    println("[DEBUG] 状态更新成功: $issueId => $status")
                    return true
                } else {
                    println("[ERROR] 状态更新失败 (尝试 ${retryCount + 1}/$maxRetries): " +
                            "状态码=${response?.code}, 消息=${response?.message}")
                    
                    // 如果是服务器错误，则进行重试
                    if (response != null && response.code >= 500) {
                        retryCount++
                        if (retryCount < maxRetries) {
                            // 等待一段时间后重试
                            Thread.sleep(1000L * retryCount)
                            continue
                        }
                    } else {
                        // 客户端错误，不需要重试
                        return false
                    }
                }
            } catch (e: Exception) {
                lastException = e
                println("[ERROR] 状态更新异常 (尝试 ${retryCount + 1}/$maxRetries): ${e.message}")
                e.printStackTrace()
                
                retryCount++
                if (retryCount < maxRetries) {
                    // 等待一段时间后重试
                    Thread.sleep(1000L * retryCount)
                    continue
                }
            }
            
            // 如果执行到这里，说明该次尝试失败
            retryCount++
        }
        
        // 所有重试都失败
        if (lastException != null) {
            println("[ERROR] 所有重试尝试都失败: ${lastException.message}")
        }
        return false
    }
    
    // 从编辑器选中的代码获取代码选择信息
    fun getCodeSelectionInfo(editor: Editor, file: VirtualFile): ApiModels.CodeSelectionInfo? {
        // 获取选中的文本
        val selectionModel = editor.selectionModel
        val selectedText = selectionModel.selectedText ?: return null
        
        // 获取起始和结束行号
        val document = editor.document
        val startLine = document.getLineNumber(selectionModel.selectionStart) + 1 // 转为1-based
        val endLine = document.getLineNumber(selectionModel.selectionEnd) + 1 // 转为1-based
        
        // 获取类名
        val psiFile = PsiManager.getInstance(project).findFile(file)
        val className = psiFile?.name ?: file.name
        
        // 获取文件相对路径
        val filePath = file.path.removePrefix(project.basePath ?: "")
        
        // 获取提交信息
        val commitInfo = getLastCommitInfo(file)
        
        // 如果是代码块，获取前100个字符
        val displayCode = if (startLine == endLine) {
            selectedText
        } else {
            // 获取开始行的内容
            val lineStartOffset = document.getLineStartOffset(startLine - 1)
            val lineEndOffset = document.getLineEndOffset(startLine - 1)
            val startLineText = document.getText(
                TextRange(lineStartOffset, lineEndOffset)
            )
            
            // 获取结束行的内容
            val endLineStartOffset = document.getLineStartOffset(endLine - 1)
            val endLineEndOffset = document.getLineEndOffset(endLine - 1)
            val endLineText = document.getText(
                TextRange(endLineStartOffset, endLineEndOffset)
            )
            
            // 组合显示
            val startPreview = startLineText.take(100)
            val endPreview = endLineText.take(100)
            "$startPreview ...\n... $endPreview"
        }
        
        return ApiModels.CodeSelectionInfo(
            className = className,
            filePath = filePath,
            lineStart = startLine,
            lineEnd = endLine,
            selectedCode = displayCode,
            commitInfo = commitInfo
        )
    }
    
    // 获取文件最后提交信息
    private fun getLastCommitInfo(file: VirtualFile): ApiModels.CommitInfo? {
        try {
            val gitManager = GitRepositoryManager.getInstance(project)
            val repository = gitManager.getRepositoryForFile(file) ?: return null
            
            // 获取提交者信息
            val process = ProcessBuilder("git", "log", "-1", "--format=%an|%ad|%s|%h", "--", file.path)
                .directory(java.io.File(repository.root.path))
                .redirectErrorStream(true)
                .start()
                
            try {
                process.waitFor(5, java.util.concurrent.TimeUnit.SECONDS)
                
                val output = process.inputStream.bufferedReader().readText().trim()
                if (output.isNotEmpty()) {
                    val parts = output.split("|", limit = 4)
                    if (parts.size == 4) {
                        return ApiModels.CommitInfo(
                            author = parts[0],
                            date = parts[1],
                            message = parts[2],
                            hash = parts[3]
                        )
                    }
                }
                return null
            } finally {
                // 确保进程资源被释放
                process.destroy()
                if (process.isAlive) {
                    process.destroyForcibly()
                }
                process.inputStream.close()
                process.errorStream.close()
                process.outputStream.close()
            }
        } catch (e: Exception) {
            println("[ERROR] 获取提交信息时发生异常: ${e.message}")
            e.printStackTrace()
            return null
        }
    }
    
    /**
     * 获取项目列表
     * @param page 页码
     * @param pageSize 每页数量
     * @return 项目列表
     */
    fun getProjects(page: Int = 1, pageSize: Int = 20): List<ApiModels.ProjectInfo> {
        // 如果正在加载，则返回缓存的数据
        if (isLoadingProjects) {
            println("[INFO] 已有正在进行的项目列表请求，返回缓存数据")
            val cachedData = projectListCache
            if (cachedData != null) {
                val (items, timestamp) = cachedData
                // 检查缓存是否过期(10分钟)
                if (System.currentTimeMillis() - timestamp < 600000) {
                    println("[DEBUG] 返回缓存的项目列表，数量: ${items.size}")
                    return items
                }
            }
            return emptyList() // 没有可用缓存
        }
        
        try {
            isLoadingProjects = true
            println("[DEBUG] 获取项目列表，页码: $page, 每页数量: $pageSize")
            
            // 检查缓存
            val cachedData = projectListCache
            if (cachedData != null) {
                val (items, timestamp) = cachedData
                // 检查缓存是否过期(10分钟)
                if (System.currentTimeMillis() - timestamp < 600000) {
                    println("[DEBUG] 返回缓存的项目列表，数量: ${items.size}")
                    isLoadingProjects = false
                    return items
                }
            }
            
            // 从登录后缓存的.idea目录中读取项目数据
            val projectManager = CodeReviewProjectManager.getInstance(project)
            val cachedProjects = projectManager.getProjectsFromCache()
            if (cachedProjects.isNotEmpty()) {
                println("[DEBUG] 使用.idea目录缓存的项目列表，数量: ${cachedProjects.size}")
                
                // 更新项目缓存
                projectListCache = Pair(cachedProjects, System.currentTimeMillis())
                
                // 更新单个项目缓存
                cachedProjects.forEach { projectInfo: ApiModels.ProjectInfo ->
                    projectCache[projectInfo.id] = projectInfo
                }
                
                isLoadingProjects = false
                return cachedProjects
            }
            
            // 调用API服务获取项目列表
            val response = apiService.getProjects(page, pageSize)
            
            if (response != null && response.code == 200 && response.data != null) {
                val items = response.data.items
                println("[DEBUG] 成功获取项目列表，数量: ${items.size}")
                
                // 更新缓存
                projectListCache = Pair(items, System.currentTimeMillis())
                
                // 更新项目缓存
                items.forEach { projectInfo ->
                    projectCache[projectInfo.id] = projectInfo
                }
                
                // 将项目列表保存到.idea目录中
                projectManager.saveProjectsToCache(items)
                
                isLoadingProjects = false
                return items
            } else {
                val errorMessage = response?.message ?: "未知错误"
                println("[ERROR] 获取项目列表失败: $errorMessage")
            }
        } catch (e: Exception) {
            println("[ERROR] 获取项目列表时发生异常: ${e.message}")
            e.printStackTrace()
        } finally {
            isLoadingProjects = false
        }
        
        // 如果失败但有缓存，返回缓存的数据
        val cachedData = projectListCache
        if (cachedData != null) {
            val (items, _) = cachedData
            println("[WARN] 使用过期缓存的项目列表，数量: ${items.size}")
            return items
        }
        
        return emptyList()
    }
    
    /**
     * 清除项目列表缓存
     */
    fun clearProjectListCache() {
        println("[DEBUG] 清除项目列表缓存")
        projectListCache = null
    }
    
    /**
     * 获取默认项目
     * 如果设置中有默认项目，则从项目列表中查找匹配ID的项目
     * 如果未找到，则返回项目列表中的第一个项目
     * 如果项目列表为空，则返回null
     */
    fun getDefaultProject(): ApiModels.ProjectInfo? {
        val settings = com.ant.code.coderplugin.settings.CodeReviewSettings.getInstance()
        val defaultProjectId = settings.defaultProjectId
        
        // 先检查缓存中是否有默认项目
        if (defaultProjectId > 0 && projectCache.containsKey(defaultProjectId)) {
            return projectCache[defaultProjectId]
        }
        
        // 获取所有项目 (使用较大的pageSize以确保能获取到所有项目)
        val projects = getProjects(page = 1, pageSize = 100)
        
        if (projects.isEmpty()) {
            return null
        }
        
        // 如果有默认项目ID，查找匹配的项目
        if (defaultProjectId > 0) {
            val defaultProject = projects.find { it.id == defaultProjectId }
            if (defaultProject != null) {
                return defaultProject
            }
        }
        
        // 如果没有默认项目或找不到匹配的项目，返回第一个项目
        return projects.firstOrNull()
    }
    
    /**
     * 清除项目相关数据
     * 在用户退出登录时调用此方法
     */
    fun clearProjectData() {
        println("[INFO] 清除项目相关数据")
        try {
            // 清除项目缓存
            projectCache.clear()
            
            // 清除项目列表缓存
            projectListCache = null
            
            // 清除问题列表缓存
            issueCache.clear()
            issueListCache.clear()
            
            // 清除用户和项目成员缓存
            usersCache.clear()
            projectMembersCache.clear()
            globalUsersCache = null
            
            // 清除.idea目录中的项目缓存
            val projectManager = CodeReviewProjectManager.getInstance(project)
            projectManager.clearProjectsCache()
            
            // 清除其他可能与用户相关的项目数据
            // ...
            
            println("[INFO] 项目相关数据已清除")
        } catch (e: Exception) {
            println("[ERROR] 清除项目数据时发生错误: ${e.message}")
            e.printStackTrace()
        }
    }
    
    /**
     * 获取问题详情
     * @param issueId 问题ID
     * @return 问题详情的API响应
     */
    fun getIssueDetail(issueId: Int): ApiModels.ApiResponse<ApiModels.IssueDetail>? {
        try {
            println("[DEBUG] 获取问题详情，ID: $issueId")
            return apiService.getIssueDetail(issueId)
        } catch (e: Exception) {
            println("[ERROR] 获取问题详情时发生异常: ${e.message}")
            e.printStackTrace()
            return null
        }
    }
    
    /**
     * 添加评论
     * @param issueId 问题ID
     * @param content 评论内容
     * @return 是否添加成功
     */
    fun addComment(issueId: Int, content: String): Boolean {
        try {
            println("[DEBUG] 添加评论，问题ID: $issueId")
            val request = ApiModels.CommentCreateRequest(content)
            val response = apiService.addComment(issueId, request)
            return response != null && response.code == 200
        } catch (e: Exception) {
            println("[ERROR] 添加评论时发生异常: ${e.message}")
            e.printStackTrace()
            return false
        }
    }
    
    /**
     * 获取特定项目的问题列表
     * @param projectId 项目ID
     * @param page 页码，默认为1
     * @param pageSize 每页数量，默认为50
     * @return 项目问题列表
     */
    fun getProjectIssues(projectId: Int, page: Int = 1, pageSize: Int = 50): List<ApiModels.IssueListItem> {
        try {
            println("[DEBUG] 获取项目问题列表，项目ID: $projectId, 页码: $page, 每页数量: $pageSize")
            val response = apiService.getProjectIssues(projectId, page, pageSize)
            
            // 根据response的实际类型进行处理
            when (response) {
                is ApiModels.ApiResponse<*> -> {
                    if (response.code == 200 && response.data != null) {
                        // 尝试从data中提取items
                        val data = response.data
                        if (data is ApiModels.PageResponse<*>) {
                            val items = data.items as? List<ApiModels.IssueListItem>
                            if (items != null) {
                                println("[DEBUG] 成功获取项目问题列表，数量: ${items.size}")
                                return items
                            }
                        } else if (data is List<*>) {
                            val items = data.filterIsInstance<ApiModels.IssueListItem>()
                            println("[DEBUG] 成功获取项目问题列表(List类型)，数量: ${items.size}")
                            return items
                        } else if (data is Map<*, *> && data.containsKey("items")) {
                            val items = (data["items"] as? List<*>)?.filterIsInstance<ApiModels.IssueListItem>()
                            if (items != null) {
                                println("[DEBUG] 成功获取项目问题列表(Map类型)，数量: ${items.size}")
                                return items
                            }
                        }
                    }
                    // 如果无法解析items，记录错误信息
                    val errorMessage = response.message ?: "未知错误"
                    println("[ERROR] 获取项目问题列表失败: $errorMessage")
                }
                is Map<*, *> -> {
                    // 尝试从Map中提取项目列表
                    val code = response["code"] as? Int
                    val items = if (response.containsKey("items")) {
                        (response["items"] as? List<*>)?.filterIsInstance<ApiModels.IssueListItem>()
                    } else if (response.containsKey("data")) {
                        val data = response["data"]
                        if (data is List<*>) {
                            data.filterIsInstance<ApiModels.IssueListItem>()
                        } else if (data is Map<*, *> && data.containsKey("items")) {
                            (data["items"] as? List<*>)?.filterIsInstance<ApiModels.IssueListItem>()
                        } else null
                    } else null
                    
                    if (items != null) {
                        println("[DEBUG] 成功获取项目问题列表(Map原始类型)，数量: ${items.size}")
                        return items
                    }
                    println("[ERROR] 无法从Map类型响应中提取项目问题列表")
                }
                else -> {
                    println("[ERROR] 未知响应类型: ${response?.javaClass?.name}")
                }
            }
        } catch (e: Exception) {
            println("[ERROR] 获取项目问题列表时发生异常: ${e.message}")
            e.printStackTrace()
        }
        
        return emptyList()
    }
    
    /**
     * 获取用户列表，用于指派问题
     * @param page 页码，默认为1
     * @param pageSize 每页数量，默认为100
     * @param projectId 项目ID，如果指定则只返回该项目的用户
     * @return 用户列表
     */
    fun getUsers(page: Int = 1, pageSize: Int = 100, projectId: Int? = null): List<ApiModels.UserInfo> {
        // 先检查缓存
        if (projectId != null && usersCache.containsKey(projectId)) {
            println("[DEBUG] 从缓存获取项目用户列表，项目ID: $projectId")
            return usersCache[projectId] ?: emptyList()
        } else if (projectId == null && globalUsersCache != null) {
            val (users, timestamp) = globalUsersCache!!
            // 检查缓存是否过期(30分钟)
            if (System.currentTimeMillis() - timestamp < 1800000) {
                println("[DEBUG] 从缓存获取全局用户列表")
                return users
            }
        }
        
        // 如果正在加载，避免重复请求
        if (isLoadingUsers) {
            println("[INFO] 已有正在进行的用户列表请求，返回缓存数据")
            return projectId?.let { usersCache[it] } ?: (globalUsersCache?.first ?: emptyList())
        }
        
        try {
            isLoadingUsers = true
            println("[DEBUG] 获取用户列表，页码: $page, 每页数量: $pageSize" + 
                    if (projectId != null) ", 项目ID: $projectId" else "")
            
            val response = apiService.getUsers(page, pageSize, projectId)
            
            if (response != null && response.code == 200 && response.data != null) {
                val items = response.data.items
                println("[DEBUG] 成功获取用户列表，数量: ${items.size}")
                
                // 更新缓存
                if (projectId != null) {
                    usersCache[projectId] = items
                } else {
                    globalUsersCache = Pair(items, System.currentTimeMillis())
                }
                
                isLoadingUsers = false
                return items
            } else {
                val errorMessage = response?.message ?: "未知错误"
                println("[ERROR] 获取用户列表失败: $errorMessage")
            }
        } catch (e: Exception) {
            println("[ERROR] 获取用户列表时发生异常: ${e.message}")
            e.printStackTrace()
        } finally {
            isLoadingUsers = false
        }
        
        // 如果API请求失败，使用缓存
        return projectId?.let { usersCache[it] } ?: (globalUsersCache?.first ?: emptyList())
    }
    
    /**
     * 获取项目成员列表
     * @param projectId 项目ID
     * @param page 页码，默认为1
     * @param pageSize 每页数量，默认为100
     * @return 项目成员列表
     */
    fun getProjectMembers(projectId: Int, page: Int = 1, pageSize: Int = 100): List<ApiModels.ProjectMember> {
        // 检查缓存
        if (projectMembersCache.containsKey(projectId)) {
            println("[DEBUG] 从缓存获取项目成员列表，项目ID: $projectId")
            return projectMembersCache[projectId] ?: emptyList()
        }
        
        // 如果正在加载，避免重复请求
        if (isLoadingMembers) {
            println("[INFO] 已有正在进行的项目成员列表请求，返回缓存数据")
            return projectMembersCache[projectId] ?: emptyList()
        }
        
        try {
            isLoadingMembers = true
            println("[DEBUG] 获取项目成员列表，项目ID: $projectId, 页码: $page, 每页数量: $pageSize")
            
            val response = apiService.getProjectMembers(projectId, page, pageSize)
            
            if (response != null && response.code == 200 && response.data != null) {
                val members = response.data
                println("[DEBUG] 成功获取项目成员列表，数量: ${members.size}")
                
                // 更新缓存
                projectMembersCache[projectId] = members
                
                isLoadingMembers = false
                return members
            } else {
                val errorMessage = response?.message ?: "未知错误"
                println("[ERROR] 获取项目成员列表失败: $errorMessage")
            }
        } catch (e: Exception) {
            println("[ERROR] 获取项目成员列表时发生异常: ${e.message}")
            e.printStackTrace()
        } finally {
            isLoadingMembers = false
        }
        
        // 如果请求失败，返回缓存数据
        return projectMembersCache[projectId] ?: emptyList()
    }
    
    /**
     * 从内存中获取指派人列表
     * 首先尝试从项目成员缓存获取，如果没有则从用户缓存获取
     * @param projectId 项目ID
     * @return 可指派的用户列表
     */
    fun getAssigneesFromMemory(projectId: Int): List<ApiModels.UserInfo> {
        println("[DEBUG] 从内存获取指派人列表，项目ID: $projectId")
        
        // 先尝试从项目成员缓存获取
        val cachedMembers = projectMembersCache[projectId]
        if (cachedMembers != null && cachedMembers.isNotEmpty()) {
            println("[DEBUG] 从项目成员缓存获取到${cachedMembers.size}个指派人")
            // 从项目成员转换为用户信息
            return cachedMembers.mapNotNull { member -> 
                // 创建简单的UserInfo对象
                ApiModels.UserInfo(
                    id = member.userId,
                    username = member.username,
                    email = "", // ProjectMember可能没有email字段，使用空字符串
                    roles = listOf(ApiModels.UserInfo.Role(name = member.roleName))
                )
            }
        }
        
        // 如果项目成员缓存为空，尝试从项目用户缓存获取
        val cachedUsers = usersCache[projectId]
        if (cachedUsers != null && cachedUsers.isNotEmpty()) {
            println("[DEBUG] 从项目用户缓存获取到${cachedUsers.size}个指派人")
            return cachedUsers
        }
        
        // 最后尝试全局用户缓存
        val globalUsers = globalUsersCache?.first
        if (globalUsers != null && globalUsers.isNotEmpty()) {
            println("[DEBUG] 从全局用户缓存获取到${globalUsers.size}个指派人")
            return globalUsers
        }
        
        println("[DEBUG] 内存中没有找到可用的指派人列表")
        return emptyList()
    }
    
    /**
     * 预加载指派人列表
     * 同时加载项目成员和用户列表，确保内存中有可用的指派人数据
     * @param projectId 项目ID
     */
    fun preloadAssignees(projectId: Int) {
        println("[DEBUG] 预加载指派人列表，项目ID: $projectId")
        
        // 在后台线程中执行
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                // 加载项目成员
                val members = getProjectMembers(projectId)
                println("[DEBUG] 预加载项目成员完成，数量: ${members.size}")
                
                // 加载项目用户
                val users = getUsers(projectId = projectId)
                println("[DEBUG] 预加载项目用户完成，数量: ${users.size}")
                
                // 如果两者都为空，尝试加载全局用户
                if (members.isEmpty() && users.isEmpty()) {
                    val globalUsers = getUsers()
                    println("[DEBUG] 预加载全局用户完成，数量: ${globalUsers.size}")
                }
            } catch (e: Exception) {
                println("[ERROR] 预加载指派人列表时出错: ${e.message}")
                e.printStackTrace()
            }
        }
    }
    
    /**
     * 使用PUT接口更新整个问题
     * @param issueId 问题ID
     * @param updateData 更新数据
     * @return 是否更新成功
     */
    fun updateIssue(issueId: Int, updateData: Map<String, Any?>, maxRetries: Int = 3): Boolean {
        var retryCount = 0
        var lastException: Exception? = null
        
        while (retryCount < maxRetries) {
            try {
                println("[DEBUG] 使用PUT接口更新问题，问题ID: $issueId, 更新数据: $updateData")
                
                // 调用API更新问题
                val response = apiService.updateIssue(issueId, updateData)
                
                if (response != null && response.code == 200) {
                    println("[DEBUG] 成功更新问题")
                    
                    // 更新成功后刷新缓存
                    if (issueCache.containsKey(issueId)) {
                        issueCache.remove(issueId)
                    }
                    
                    return true
                } else {
                    println("[ERROR] 更新问题失败 (尝试 ${retryCount + 1}/$maxRetries): " +
                            "状态码=${response?.code}, 消息=${response?.message}")
                    
                    // 如果是服务器错误，则进行重试
                    if (response != null && response.code >= 500) {
                        retryCount++
                        if (retryCount < maxRetries) {
                            // 等待一段时间后重试
                            Thread.sleep(1000L * retryCount)
                            continue
                        }
                    } else {
                        // 客户端错误，不需要重试
                        return false
                    }
                }
            } catch (e: Exception) {
                lastException = e
                println("[ERROR] 更新问题时发生异常 (尝试 ${retryCount + 1}/$maxRetries): ${e.message}")
                e.printStackTrace()
                
                retryCount++
                if (retryCount < maxRetries) {
                    // 等待一段时间后重试
                    Thread.sleep(1000L * retryCount)
                    continue
                }
            }
            
            // 如果执行到这里，说明该次尝试失败
            retryCount++
        }
        
        // 所有重试都失败
        if (lastException != null) {
            println("[ERROR] 所有重试尝试都失败: ${lastException.message}")
        }
        return false
    }
    
    /**
     * 更新问题字段
     * @param issueId 问题ID
     * @param field 字段名称（如：status, priority, issue_type, assignee_id, severity等）
     * @param value 字段值
     * @return 是否更新成功
     */
    fun updateIssueField(issueId: Int, field: String, value: String): Boolean {
        try {
            println("[DEBUG] 更新问题字段，问题ID: $issueId, 字段: $field, 值: $value")
            
            // 对于指派人字段，使用PUT接口
            if (field == "assignee_id") {
                val updateData = mutableMapOf<String, Any?>()
                updateData[field] = if (value.isEmpty()) null else value.toInt()
                return updateIssue(issueId, updateData)
            }
            
            // 根据字段类型调用不同的API方法
            if (field == "status") {
                // 调用状态更新API
                val statusRequest = ApiModels.StatusUpdateRequest(status = value, comment = null)
                val response = apiService.updateIssueStatus(issueId, statusRequest)
                
                if (response != null && response.code == 200) {
                    println("[DEBUG] 成功更新问题状态")
                    
                    // 更新成功后刷新缓存
                    if (issueCache.containsKey(issueId)) {
                        issueCache.remove(issueId)
                    }
                    
                    return true
                } else {
                    val errorMessage = response?.message ?: "未知错误"
                    println("[ERROR] 更新问题状态失败: $errorMessage")
                    return false
                }
            } else {
                // 对于其他字段，使用PUT接口更新
                val updateData = mutableMapOf<String, Any?>()
                updateData[field] = value
                return updateIssue(issueId, updateData)
            }
        } catch (e: Exception) {
            println("[ERROR] 更新问题字段时发生异常: ${e.message}")
            e.printStackTrace()
            return false
        }
    }
    
    /**
     * 更新整个问题
     * @param request 问题更新请求
     * @return 是否更新成功
     */
    fun updateIssue(request: ApiModels.IssueUpdateRequest, maxRetries: Int = 3): Boolean {
        try {
            println("[DEBUG] 更新问题，问题ID: ${request.id}")
            
            // 转换为Map
            val updateData = mutableMapOf<String, Any?>()
            request.title?.let { updateData["title"] = it }
            request.description?.let { updateData["description"] = it }
            request.priority?.let { updateData["priority"] = it }
            request.issueType?.let { updateData["issue_type"] = it }
            request.severity?.let { updateData["severity"] = it }
            request.status?.let { updateData["status"] = it }
            request.assigneeId?.let { updateData["assignee_id"] = it }
            request.projectId?.let { updateData["project_id"] = it }
            
            // 调用现有的updateIssue方法
            return updateIssue(request.id, updateData, maxRetries)
        } catch (e: Exception) {
            println("[ERROR] 更新问题时发生异常: ${e.message}")
            e.printStackTrace()
            return false
        }
    }
    
    companion object {
        fun getInstance(project: Project): IssueService = project.service<IssueService>()
    }
} 