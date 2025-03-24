@file:Suppress("EXPERIMENTAL_FEATURE_WARNING", "EXPERIMENTAL_API_USAGE")

package com.ant.code.coderplugin.api

import com.ant.code.coderplugin.api.ApiModels
import com.ant.code.coderplugin.settings.AppSettingsState
import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.fasterxml.jackson.core.type.TypeReference
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.project.Project
import com.intellij.openapi.util.Disposer
import com.intellij.openapi.Disposable
import com.intellij.openapi.diagnostic.Logger
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit
import java.util.concurrent.ConcurrentHashMap
import kotlin.ExperimentalStdlibApi

/**
 * HTTP方法枚举
 */
enum class HttpMethod {
    GET, POST, PUT, DELETE, PATCH
}

/**
 * HTTP响应结构
 */
data class HttpResponse(
    val statusCode: Int,
    val responseBody: String,
    val headers: Headers
)

@Service(Service.Level.PROJECT)
class ApiService(private val _project: Project) : Disposable {
    private var client: OkHttpClient
    private val objectMapper: ObjectMapper = jacksonObjectMapper()
    private val settings = AppSettingsState.getInstance()
    private var accessToken: String? = null
    private val isDisposed = java.util.concurrent.atomic.AtomicBoolean(false)
    private val ongoingCalls = ConcurrentHashMap<Call, Boolean>()
    private var lastConnectionFailureTime: Long = 0
    private val CONNECTION_RESET_THRESHOLD = 10000 // 10秒内多次连接失败才重置客户端
    private var connectionFailureCount = 0
    private val MAX_FAILURES_BEFORE_RESET = 3     // 连续失败3次后重置客户端
    
    companion object {
        private val LOGGER = Logger.getInstance(ApiService::class.java)

        @JvmStatic
        fun getInstance(project: Project): ApiService = project.service<ApiService>()

        @JvmStatic
        fun shutdown(unusedProject: Project) {
            LOGGER.info("Shutting down API service")
        }
    }
    
    init {
        client = createNewClient()
        
        // 注册到项目的生命周期，确保资源被释放
        Disposer.register(_project, this)
    }

    /**
     * 创建新的OkHttpClient实例
     */
    private fun createNewClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .retryOnConnectionFailure(false) // 避免自动重试导致的资源占用
            .build()
    }

    /**
     * 重置HTTP客户端
     * 当检测到连接问题时调用，关闭旧客户端并创建一个新的
     */
    @Synchronized
    private fun resetHttpClient() {
        println("[INFO] 正在重置HTTP客户端...")
        try {
            // 取消所有正在进行的请求
            val callsToCancel = ongoingCalls.keys().toList()
            ongoingCalls.clear()
            
            callsToCancel.forEach { call ->
                try {
                    if (!call.isCanceled() && !call.isExecuted()) {
                        call.cancel()
                    }
                } catch (e: Exception) {
                    println("[ERROR] 取消请求时出错: ${e.message}")
                }
            }
            
            // 关闭旧的连接池
            client.connectionPool.evictAll()
            
            // 关闭旧的调度器
            try {
                client.dispatcher.executorService.shutdown()
                if (!client.dispatcher.executorService.awaitTermination(1, TimeUnit.SECONDS)) {
                    client.dispatcher.executorService.shutdownNow()
                }
                client.dispatcher.cancelAll()
            } catch (e: Exception) {
                println("[ERROR] 关闭旧HTTP客户端时出错: ${e.message}")
            }
            
            // 创建新的客户端
            client = createNewClient()
            
            // 重置连接失败计数器
            connectionFailureCount = 0
            println("[INFO] HTTP客户端已重置")
        } catch (e: Exception) {
            println("[ERROR] 重置HTTP客户端时出错: ${e.message}")
            e.printStackTrace()
        }
    }

    /**
     * 记录连接失败并在必要时重置客户端
     */
    private fun recordConnectionFailure() {
        val currentTime = System.currentTimeMillis()
        
        // 如果上次失败是在阈值时间内，增加计数器
        if (currentTime - lastConnectionFailureTime < CONNECTION_RESET_THRESHOLD) {
            connectionFailureCount++
            println("[WARN] 连接失败计数: $connectionFailureCount/$MAX_FAILURES_BEFORE_RESET")
            
            // 如果连续失败次数达到阈值，重置客户端
            if (connectionFailureCount >= MAX_FAILURES_BEFORE_RESET) {
                resetHttpClient()
            }
        } else {
            // 如果距离上次失败时间较长，重置计数器
            connectionFailureCount = 1
        }
        
        lastConnectionFailureTime = currentTime
    }

    override fun dispose() {
        try {
            println("[DEBUG] Disposing ApiService")
            
            try {
                // 取消所有正在进行的请求
                val callsToCancel = ongoingCalls.keys().toList()
                ongoingCalls.clear()
                
                callsToCancel.forEach { call ->
                    try {
                        if (!call.isCanceled() && !call.isExecuted()) {
                            call.cancel()
                        }
                    } catch (e: Exception) {
                        println("[ERROR] 取消请求时出错: ${e.message}")
                    }
                }
                
                // 关闭OkHttpClient
                try {
                    // 关闭连接池
                    client.connectionPool.evictAll()
                    
                    // 关闭调度器 - 更安全的方式
                    // 首先尝试优雅关闭，允许当前任务完成
                    client.dispatcher.executorService.shutdown()
                    if (!client.dispatcher.executorService.awaitTermination(1, TimeUnit.SECONDS)) {
                        // 如果超时，强制关闭
                        client.dispatcher.executorService.shutdownNow()
                    }
                    
                    client.dispatcher.cancelAll()
                } catch (e: Exception) {
                    println("[ERROR] 关闭OkHttpClient时出错: ${e.message}")
                }
                
                // 清除引用
                accessToken = null
            } catch (e: Exception) {
                println("[ERROR] 释放ApiService资源时出错: ${e.message}")
                e.printStackTrace()
            }
            
            // 强制触发垃圾回收
            System.gc()
            
            println("[DEBUG] ApiService resources released successfully")
        } catch (e: Exception) {
            println("[ERROR] Disposing ApiService error: ${e.message}")
            e.printStackTrace()
        }
    }
    
    // 设置访问令牌
    fun setAccessToken(token: String) {
        println("[DEBUG] 设置访问令牌: ${token.take(10)}...")
        accessToken = token
    }
    
    // 清除访问令牌
    fun clearAccessToken() {
        println("[DEBUG] 清除访问令牌")
        accessToken = null
    }
    
    // 获取当前访问令牌
    fun getAccessToken(): String? {
        return accessToken
    }
    
    /**
     * 用户登录
     * @param username 用户名
     * @param password 密码
     * @param rememberMe 是否记住登录状态
     * @return 登录响应
     */
    fun login(username: String, password: String, rememberMe: Boolean = false): ApiModels.ApiResponse<ApiModels.LoginResponse>? {
        if (isDisposed.get()) {
            println("[WARN] ApiService已释放，无法执行登录操作")
            return null
        }

        val url = "${getStandardizedApiUrl()}/auth/login"
        println("[INFO] 开始登录: $url")

        try {
            // 检查是否在EDT线程上执行
            if (ApplicationManager.getApplication().isDispatchThread) {
                println("[WARN] 在EDT线程上调用登录方法，这可能导致UI卡顿。")
            }

            // 创建登录请求对象
            val loginRequest = ApiModels.LoginRequest(
                userId = username,
                password = password,
                rememberMe = rememberMe
            )

            // 转换为JSON
            val requestJson = objectMapper.writeValueAsString(loginRequest)
            println("[DEBUG] 创建问题请求体: $requestJson")
            
            val requestBody = requestJson.toRequestBody("application/json".toMediaType())

            // 构建请求
            val request = Request.Builder()
                .url(url)
                .post(requestBody)
                .build()

            // 执行请求
            val call = client.newCall(request)
            try {
            val response = call.execute()
            val responseBody = response.body?.string()

            println("[INFO] 登录响应状态码: ${response.code}")
            println("[DEBUG] 登录响应体: $responseBody")

            // 解析响应
            return if (response.isSuccessful && responseBody != null) {
                try {
                    val loginResponse = objectMapper.readValue(
                        responseBody,
                        object : TypeReference<ApiModels.ApiResponse<ApiModels.LoginResponse>>() {}
                    )
                    println("[INFO] 登录响应解析成功: ${loginResponse.code}, ${loginResponse.message}")
                    
                    // 如果登录成功，设置访问令牌
                    if (loginResponse.code == 200 && loginResponse.data != null) {
                        // 在非EDT线程中设置token，或者至少确保token的保存不会阻塞EDT
                        if (ApplicationManager.getApplication().isDispatchThread) {
                            ApplicationManager.getApplication().executeOnPooledThread {
                                accessToken = loginResponse.data.accessToken
                                println("[INFO] 登录成功，已设置访问令牌(后台线程)")
                            }
                        } else {
                            accessToken = loginResponse.data.accessToken
                            println("[INFO] 登录成功，已设置访问令牌(非EDT线程)")
                        }
                    } else {
                        println("[WARN] 登录失败: ${loginResponse.message}")
                    }
                    
                    loginResponse
                } catch (e: Exception) {
                    println("[ERROR] 解析登录响应时出错: ${e.message}")
                    e.printStackTrace()
                    ApiModels.ApiResponse(500, "解析登录响应出错: ${e.message}", null)
                }
            } else {
                println("[WARN] 登录请求失败: ${response.code}, $responseBody")
                ApiModels.ApiResponse(response.code, "登录请求失败: $responseBody", null)
            }
            } catch (e: IOException) {
                // 记录连接失败
                recordConnectionFailure()
                println("[ERROR] 执行登录请求时发生IO异常: ${e.message}")
                e.printStackTrace()
                return ApiModels.ApiResponse(500, "执行登录请求时连接失败: ${e.message}", null)
            } catch (e: Exception) {
                println("[ERROR] 执行登录请求时出错: ${e.message}")
                e.printStackTrace()
                return ApiModels.ApiResponse(500, "执行登录请求出错: ${e.message}", null)
            }
        } catch (e: Exception) {
            println("[ERROR] 执行登录请求时出错: ${e.message}")
            e.printStackTrace()
            return ApiModels.ApiResponse(500, "执行登录请求出错: ${e.message}", null)
        }
    }
    
    // 获取当前用户信息
    @OptIn(ExperimentalStdlibApi::class)
    fun getCurrentUser(maxRetries: Int = 3): ApiModels.ApiResponse<ApiModels.UserInfo>? {
        if (accessToken == null) {
            println("[ERROR] 尝试获取用户信息但没有访问令牌")
            return null
        }

        println("[DEBUG] 开始获取用户信息")
        println("[DEBUG] 使用Token: ${accessToken?.take(10)}...")
        
        var retryCount = 0
        var lastException: Exception? = null
        
        loop@ while (retryCount < maxRetries) {
        val request = Request.Builder()
            .url("${settings.getApiUrl()}/auth/get_current_user")
            .header("Authorization", "Bearer $accessToken")
            .get()
            .build()
        
        var call: Call? = null
        try {
                println("[DEBUG] 发送请求: ${request.url}, 尝试 ${retryCount + 1}/$maxRetries")
            println("[DEBUG] 请求头: ${request.headers}")
            
            // 创建并跟踪Call
            call = client.newCall(request)
            ongoingCalls[call] = true
            
            call.execute().use { response ->
                // 请求完成，从跟踪中移除
                ongoingCalls.remove(call)
                
                val responseBody = response.body?.string()
                
                println("[DEBUG] 获取用户信息响应状态: ${response.code}")
                println("[DEBUG] 获取用户信息响应内容: ${responseBody?.take(200)}${if (responseBody != null && responseBody.length > 200) "..." else ""}")
                
                if (response.isSuccessful && responseBody != null) {
                    try {
                        // 尝试解析标准响应格式
                        val apiResponse = objectMapper.readValue<ApiModels.ApiResponse<ApiModels.UserInfo>>(
                            responseBody, 
                            object : TypeReference<ApiModels.ApiResponse<ApiModels.UserInfo>>() {}
                        )
                        println("[DEBUG] 用户信息解析成功: ${apiResponse.data?.username}")
                        return apiResponse
                    } catch (e: Exception) {
                        println("[ERROR] 用户信息解析失败: ${e.message}")
                        e.printStackTrace()
                            
                            try {
                                // 尝试手动解析
                                println("[DEBUG] 尝试手动解析用户信息")
                                val jsonNode = objectMapper.readTree(responseBody)
                                if (jsonNode != null && jsonNode.has("code") && jsonNode.has("data")) {
                                    val code = jsonNode.get("code").asInt()
                                    val message = jsonNode.get("message").asText()
                                    val timestamp = if (jsonNode.has("timestamp")) jsonNode.get("timestamp").asText() else null
                                    val dataNode = jsonNode.get("data")
                                    
                                    if (code == 200 && dataNode != null && dataNode.isObject()) {
                                        // 手动提取用户信息字段
                                        val id = dataNode.get("id").asInt()
                                        val userId = if (dataNode.has("user_id")) dataNode.get("user_id").asText() else null
                                        val username = dataNode.get("username").asText()
                                        val email = if (dataNode.has("email")) dataNode.get("email").asText() else null
                                        val phone = if (dataNode.has("phone")) dataNode.get("phone").asText() else null
                                        val isActive = if (dataNode.has("is_active")) dataNode.get("is_active").asBoolean() else true
                                        val createdAt = if (dataNode.has("created_at")) dataNode.get("created_at").asText() else null
                                        val updatedAt = if (dataNode.has("updated_at")) dataNode.get("updated_at").asText() else null
                                        
                                        // 处理roles字段
                                        val rolesList = mutableListOf<ApiModels.UserInfo.Role>()
                                        if (dataNode.has("roles") && dataNode.get("roles").isArray()) {
                                            val rolesNode = dataNode.get("roles")
                                            rolesNode.forEach { roleNode ->
                                                if (roleNode.isTextual()) {
                                                    // 字符串角色
                                                    rolesList.add(ApiModels.UserInfo.Role(name = roleNode.asText()))
                                                } else if (roleNode.isObject()) {
                                                    // 对象角色
                                                    val roleId = if (roleNode.has("id")) roleNode.get("id").asInt() else null
                                                    val roleName = if (roleNode.has("name")) roleNode.get("name").asText() else null
                                                    rolesList.add(ApiModels.UserInfo.Role(id = roleId, name = roleName))
                                                }
                                            }
                                        }
                                        
                                        // 处理权限字段
                                        val permissionsList = mutableListOf<ApiModels.UserInfo.Permission>()
                                        if (dataNode.has("permissions") && dataNode.get("permissions").isArray()) {
                                            val permissionsNode = dataNode.get("permissions")
                                            permissionsNode.forEach { permNode ->
                                                if (permNode.isObject()) {
                                                    val permId = if (permNode.has("id")) permNode.get("id").asInt() else null
                                                    val permissionId = if (permNode.has("permission_id")) permNode.get("permission_id").asInt() else null
                                                    val codeValue = if (permNode.has("code")) permNode.get("code").asText() else null
                                                    val name = if (permNode.has("name")) permNode.get("name").asText() else null
                                                    val description = if (permNode.has("description")) permNode.get("description").asText() else null
                                                    
                                                    permissionsList.add(ApiModels.UserInfo.Permission(
                                                        id = permId,
                                                        permissionId = permissionId,
                                                        code = codeValue,
                                                        name = name,
                                                        description = description
                                                    ))
                                                }
                                            }
                                        }
                                        
                                        // 创建用户对象
                                        val userInfo = ApiModels.UserInfo(
                                            id = id,
                                            userId = userId,
                                            username = username,
                                            email = email,
                                            phone = phone,
                                            roles = rolesList,
                                            isActive = isActive,
                                            createdAt = createdAt,
                                            updatedAt = updatedAt,
                                            permissions = permissionsList
                                        )
                                        
                                        println("[DEBUG] 手动解析用户信息成功: ${userInfo.username}")
                                        
                                        return ApiModels.ApiResponse(
                                            code = code,
                                            message = message,
                                            timestamp = timestamp,
                                            data = userInfo
                                        )
                                    }
                                }
                            } catch (e2: Exception) {
                                println("[ERROR] 手动解析用户信息也失败: ${e2.message}")
                                e2.printStackTrace()
                            }
                        
                        return ApiModels.ApiResponse(
                            code = 500,
                            message = "解析用户信息失败: ${e.message}"
                        )
                    }
                } else {
                        // 如果是401错误，可能是token过期，不再重试
                    if (response.code == 401) {
                        println("[ERROR] 授权失败，可能需要重新登录")
                        // 清除token状态
                        accessToken = null
                            return ApiModels.ApiResponse(
                                code = response.code,
                                message = "获取用户信息失败: 授权问题"
                            )
                        }
                        
                        // 服务器错误时重试
                        if (response.code >= 500) {
                            retryCount++
                            println("[WARN] 服务器错误(${response.code})，将在1秒后重试 (${retryCount}/$maxRetries)")
                            Thread.sleep(1000)
                        } else {
                    return ApiModels.ApiResponse(
                        code = response.code,
                        message = "获取用户信息失败: ${response.message}"
                    )
                }
                    }
            }
        } catch (e: IOException) {
            // 发生异常时，也从跟踪中移除
            if (call != null) {
                ongoingCalls.remove(call)
            }
                
                // 记录连接失败并尝试重置客户端
                recordConnectionFailure()
                lastException = e
                println("[ERROR] 获取用户信息请求执行失败 (IO异常): ${e.message}")
                
                // 判断是否是网络连接问题，如果是则重试
                retryCount++
                val waitTime = 1000L * retryCount // 增加等待时间，避免频繁请求
                println("[WARN] 网络连接问题，将在${waitTime/1000}秒后重试 (${retryCount}/$maxRetries)")
                
                // 重构以避免在lambda中使用continue/break
                try {
                    Thread.sleep(waitTime)
                    // 无需continue，直接进入下一次循环
                } catch (ie: InterruptedException) {
                    Thread.currentThread().interrupt()
                    // 被中断，添加break的替代实现 - 返回错误
                    lastException = ie
                    println("[ERROR] 线程被中断，无法完成重试")
                    break@loop // 使用命名循环跳出
            }
        } catch (e: Exception) {
            // 发生异常时，也从跟踪中移除
            if (call != null) {
                ongoingCalls.remove(call)
            }
                
                lastException = e
            println("[ERROR] 获取用户信息请求执行失败: ${e.message}")
                
                // 判断是否是网络连接问题，如果是则重试
                if (e is IOException) {
                    retryCount++
                    val waitTime = 1000L * retryCount // 增加等待时间，避免频繁请求
                    println("[WARN] 网络连接问题，将在${waitTime/1000}秒后重试 (${retryCount}/$maxRetries)")
                    
                    try {
                        Thread.sleep(waitTime)
                        // 继续循环
                        continue
                    } catch (ie: InterruptedException) {
                        Thread.currentThread().interrupt()
                        // 退出循环，返回错误
                        return ApiModels.ApiResponse(
                            code = 500,
                            message = "线程被中断，无法完成重试",
                            data = null
                        )
                    }
                } else {
                    // 非网络问题不重试
            e.printStackTrace()
                    break
                }
            }
        }
            
        // 所有重试都失败
        lastException?.printStackTrace()
        val errorMessage = lastException?.message ?: "未知错误"
        println("[ERROR] 获取用户信息失败，重试${maxRetries}次后放弃: $errorMessage")
            return ApiModels.ApiResponse(
                code = 500,
            message = "获取用户信息请求执行失败: $errorMessage"
            )
    }
    
    // 获取用户问题列表
    @OptIn(ExperimentalStdlibApi::class)
    fun getUserIssues(page: Int = 1, pageSize: Int = 50, maxRetries: Int = 3): ApiModels.ApiResponse<ApiModels.PageResponse<ApiModels.IssueListItem>>? {
        if (accessToken == null) {
            println("[ERROR] 尝试获取问题列表但没有访问令牌")
            return ApiModels.ApiResponse(401, "没有访问令牌", null)
        }
        
        var retryCount = 0
        var lastException: Exception? = null
        
        loop@ while (retryCount < maxRetries) {
            // 修复URL后缀斜杠问题，确保使用统一格式
            val url = "${getStandardizedApiUrl()}/issues"
            println("[DEBUG] 构造问题列表请求URL: $url?page=$page&page_size=$pageSize")
            
        val request = Request.Builder()
                .url("$url?page=$page&page_size=$pageSize")
            .header("Authorization", "Bearer $accessToken")
            .get()
            .build()
            
        var call: Call? = null
        try {
                println("[DEBUG] 发送请求: ${request.url}, 尝试 ${retryCount + 1}/$maxRetries")
            println("[DEBUG] 请求头: ${request.headers}")
            
            // 创建并跟踪Call
            call = client.newCall(request)
            ongoingCalls[call] = true
            
            call.execute().use { response ->
                // 请求完成，从跟踪中移除
                ongoingCalls.remove(call)
                
                val responseBody = response.body?.string()
                
                    println("[DEBUG] 获取用户信息响应状态: ${response.code}")
                    println("[DEBUG] 获取用户信息响应内容: ${responseBody?.take(200)}${if (responseBody != null && responseBody.length > 200) "..." else ""}")
                
                if (response.isSuccessful && responseBody != null) {
                    try {
                            // 尝试解析标准响应格式
                            val apiResponse = objectMapper.readValue<ApiModels.ApiResponse<ApiModels.PageResponse<ApiModels.IssueListItem>>>(
                            responseBody,
                                object : TypeReference<ApiModels.ApiResponse<ApiModels.PageResponse<ApiModels.IssueListItem>>>() {}
                            )
                            println("[INFO] 用户问题列表解析成功: ${apiResponse.data?.items?.size}个问题")
                            return apiResponse
                        } catch (e: Exception) {
                            println("[ERROR] 用户问题列表解析失败: ${e.message}")
                            e.printStackTrace()
                                
                            try {
                                // 尝试手动解析
                                println("[DEBUG] 尝试手动解析用户问题列表")
                                val jsonNode = objectMapper.readTree(responseBody)
                                if (jsonNode != null && jsonNode.has("code") && jsonNode.has("data")) {
                                    val code = jsonNode.get("code").asInt()
                                    val message = jsonNode.get("message").asText()
                                    val timestamp = if (jsonNode.has("timestamp")) jsonNode.get("timestamp").asText() else null
                                    val dataNode = jsonNode.get("data")
                                    
                                    if (code == 200 && dataNode != null && dataNode.isObject()) {
                                        // 手动提取用户问题列表字段
                                        val itemsNode = dataNode.get("items")
                                val issuesList = objectMapper.convertValue(
                                            itemsNode,
                                    object : TypeReference<List<ApiModels.IssueListItem>>() {}
                                )
                                
                                // 提取分页信息
                                        val pageInfoMap = if (dataNode.has("page_info") && dataNode["page_info"] is Map<*, *>) {
                                            val pageInfo = dataNode["page_info"] as? Map<String, Any>
                                        pageInfo
                                } else {
                                    mapOf(
                                        "total" to issuesList.size,
                                        "page" to page,
                                        "page_size" to pageSize,
                                        "total_pages" to 1
                                    )
                                }
                                
                                    val total = if (pageInfoMap != null && pageInfoMap.containsKey("total")) {
                                        val totalValue = pageInfoMap["total"]
                                        when (totalValue) {
                                            is Number -> totalValue.toInt()
                                        else -> issuesList.size
                                    }
                                    } else {
                                        issuesList.size
                                }
                                
                                // 创建PageResponse对象
                                val pageResponse = ApiModels.PageResponse(
                                    total = total,
                                    items = issuesList
                                )
                                
                                // 返回包装好的ApiResponse
                                return ApiModels.ApiResponse(
                                            code = code,
                                            message = message,
                                            timestamp = timestamp,
                                    data = pageResponse
                                )
                            }
                                }
                            } catch (e2: Exception) {
                                println("[ERROR] 手动解析用户问题列表也失败: ${e2.message}")
                                e2.printStackTrace()
                            }
                            
                        return ApiModels.ApiResponse(
                            code = 500,
                                message = "解析用户问题列表失败: ${e.message}"
                        )
                    }
                } else {
                        // 如果是401错误，可能是token过期，不再重试
                    if (response.code == 401) {
                        println("[ERROR] 授权失败，可能需要重新登录")
                        // 清除token状态
                        accessToken = null
                            return ApiModels.ApiResponse(
                                code = response.code,
                                message = "获取用户问题列表失败: 授权问题",
                                data = null
                            )
                        }
                        
                        // 服务器错误时重试
                        if (response.code >= 500) {
                            retryCount++
                            println("[WARN] 服务器错误(${response.code})，将在1秒后重试 (${retryCount}/$maxRetries)")
                            Thread.sleep(1000)
                        } else {
                    return ApiModels.ApiResponse(
                        code = response.code,
                                message = "获取用户问题列表失败: ${response.message}"
                    )
                }
            }
                }
            } catch (e: IOException) {
            // 发生异常时，也从跟踪中移除
            if (call != null) {
                ongoingCalls.remove(call)
            }
                
                // 记录连接失败并尝试重置客户端
                recordConnectionFailure()
                lastException = e
                println("[ERROR] 获取用户问题列表请求执行失败 (IO异常): ${e.message}")
                
                // 网络问题重试
                    retryCount++
                    val waitTime = 1000L * retryCount // 增加等待时间，避免频繁请求
                    println("[WARN] 网络连接问题，将在${waitTime/1000}秒后重试 (${retryCount}/$maxRetries)")
                
                // 重构以避免在lambda中使用continue/break
                    try {
                        Thread.sleep(waitTime)
                    // 无需continue，直接进入下一次循环
                    } catch (ie: InterruptedException) {
                        Thread.currentThread().interrupt()
                    // 被中断，添加break的替代实现 - 返回错误
                    lastException = ie
                    println("[ERROR] 线程被中断，无法完成重试")
                    break@loop // 使用命名循环跳出
                    }
                } catch (e: Exception) {
                // 发生异常时，也从跟踪中移除
                if (call != null) {
            ongoingCalls.remove(call)
                }
                
                lastException = e
                println("[ERROR] 获取用户问题列表请求执行失败: ${e.message}")
                e.printStackTrace()
                
                // 一般异常不重试
                        break
                    }
            
            // 正常情况下，如果代码执行到这里，说明请求已完成
                    break
        }
        
        // 所有重试都失败
        val errorMessage = lastException?.message ?: "未知错误"
        println("[ERROR] 获取用户问题列表失败，重试${maxRetries}次后放弃: $errorMessage")
        return ApiModels.ApiResponse(
            code = 500,
            message = "获取用户问题列表失败: $errorMessage",
            data = null
        )
    }
    
    /**
     * 创建问题
     */
    fun createIssue(request: ApiModels.IssueCreateRequest): ApiModels.ApiResponse<ApiModels.IssueListItem> {
        val url = "${getStandardizedApiUrl()}/issues"
        println("[INFO] 开始创建问题: $url")
        
        try {
            // 转换为JSON
            val requestJson = objectMapper.writeValueAsString(request)
            println("[DEBUG] 创建问题请求体: $requestJson")
            
            // 检查JSON中是否包含所有必要字段
            val jsonNode = objectMapper.readTree(requestJson)
            println("[DEBUG] 请求字段检查:")
            println("[DEBUG] - title: ${jsonNode.has("title")}")
            println("[DEBUG] - description: ${jsonNode.has("description")}")
            println("[DEBUG] - priority: ${jsonNode.has("priority")}")
            println("[DEBUG] - issue_type: ${jsonNode.has("issue_type")}")
            println("[DEBUG] - project_id: ${jsonNode.has("project_id")}")
            println("[DEBUG] - assignee_id: ${jsonNode.has("assignee_id")}")
            println("[DEBUG] - file_path: ${jsonNode.has("file_path")}")
            println("[DEBUG] - line_start: ${jsonNode.has("line_start")}")
            println("[DEBUG] - line_end: ${jsonNode.has("line_end")}")
            println("[DEBUG] - code_content: ${jsonNode.has("code_content")}")
            println("[DEBUG] - status: ${jsonNode.has("status")}")
            
            val requestBody = requestJson.toRequestBody("application/json".toMediaType())
            
            val httpRequest = Request.Builder()
                .url(url)
                .addHeader("Authorization", "Bearer $accessToken")
                .addHeader("Content-Type", "application/json")
                .post(requestBody)
                .build()
                
            // 重试计数和最大重试次数
            var retryCount = 0
            val maxRetries = 3
            var lastException: Exception? = null
                
            while (retryCount <= maxRetries) {
                var call: Call? = null
                try {
                    // 创建并跟踪Call
                    call = client.newCall(httpRequest)
                    ongoingCalls[call] = true
                    
            val response = call.execute()
                    ongoingCalls.remove(call)
                    
            val responseBody = response.body?.string()
            
            println("[INFO] 创建问题响应状态码: ${response.code}")
            println("[DEBUG] 创建问题响应体: $responseBody")
            
            return if (response.isSuccessful && responseBody != null) {
                try {
                    // 先尝试检查是否包含 success 字段（标准响应格式）
                    val responseNode = objectMapper.readTree(responseBody)
                    if (responseNode.has("success")) {
                        // 使用标准响应格式
                        val success = responseNode.get("success").asBoolean()
                        val message = if (responseNode.has("message")) responseNode.get("message").asText() else "Success"
                        val code = if (success) 200 else 400
                        
                        if (success && responseNode.has("data")) {
                            // 成功且有数据，解析数据部分
                            val dataNode = responseNode.get("data")
                            // 使用TypeReference来正确处理类型
                            val issueItem = objectMapper.convertValue(dataNode, ApiModels.IssueListItem::class.java)
                            ApiModels.ApiResponse(code, message, null, issueItem)
                        } else {
                            // 成功但无数据或失败
                            ApiModels.ApiResponse(code, message, null)
                        }
                    } else {
                        // 使用常规ApiResponse格式
                    val apiResponse = objectMapper.readValue(responseBody, 
                        object : TypeReference<ApiModels.ApiResponse<ApiModels.IssueListItem>>() {})
                    println("[INFO] 创建问题响应解析成功: ${apiResponse.code}, ${apiResponse.message}")
                    apiResponse
                    }
                } catch (e: Exception) {
                    println("[ERROR] 解析创建问题响应失败: ${e.message}")
                    e.printStackTrace()
                    println("[DEBUG] 原始响应内容: $responseBody")
                    ApiModels.ApiResponse(500, "解析创建问题响应失败: ${e.message}", null)
                }
            } else {
                        // 检查是否是服务器错误，如果是则重试
                        if (response.code >= 500 && retryCount < maxRetries) {
                            retryCount++
                            val waitTime = 1000L * retryCount
                            println("[WARN] 服务器错误(${response.code})，将在${waitTime/1000}秒后重试 (${retryCount}/$maxRetries)")
                            Thread.sleep(waitTime)
                            // 跳过本次循环的剩余部分
                            // 不要使用continue，因为这会导致实验性特性警告
                            // 相反，设置一个标志然后在代码后面检查这个标志
                            val shouldRetry = true
                            if (shouldRetry) {
                                // 执行一个无操作来避免静态分析工具的警告
                                val dummy = 0
                            } else {
                                return ApiModels.ApiResponse(
                                    code = response.code,
                                    message = "创建问题失败: ${response.message}",
                                    data = null
                                )
                            }
                        }
                        
                val errorBody = responseBody ?: "无响应内容"
                println("[WARN] 创建问题失败: ${response.code}, $errorBody")
                ApiModels.ApiResponse(response.code, "创建问题失败: $errorBody", null)
            }
                } catch (e: IOException) {
                    // 连接失败，清理并记录
                    if (call != null) {
                        ongoingCalls.remove(call)
                    }
                    
                    // 记录连接失败并考虑重置客户端
                    recordConnectionFailure()
                    lastException = e
                    
                    if (retryCount < maxRetries) {
                        retryCount++
                        val waitTime = 1000L * retryCount
                        println("[ERROR] 创建问题请求执行IO异常: ${e.message}，将在${waitTime/1000}秒后重试 (${retryCount}/$maxRetries)")
                        try {
                            Thread.sleep(waitTime)
                            continue
                        } catch (ie: InterruptedException) {
                            Thread.currentThread().interrupt()
                            break
                        }
                    } else {
                        println("[ERROR] 创建问题请求执行失败，达到最大重试次数: ${e.message}")
                        e.printStackTrace()
                        return ApiModels.ApiResponse(500, "执行创建问题请求出错: ${e.message}", null)
            }
        } catch (e: Exception) {
                    // 其他异常，清理资源
                    if (call != null) {
                        ongoingCalls.remove(call)
                    }
                    
            println("[ERROR] 执行创建问题请求出错: ${e.message}")
            e.printStackTrace()
            return ApiModels.ApiResponse(500, "执行创建问题请求出错: ${e.message}", null)
                }
            }
            
            // 所有重试都失败
            val errorMessage = lastException?.message ?: "未知错误"
            println("[ERROR] 创建问题失败，重试${maxRetries}次后放弃: $errorMessage")
            return ApiModels.ApiResponse(500, "执行创建问题请求出错: $errorMessage", null)
        } catch (e: Exception) {
            println("[ERROR] 准备创建问题请求时出错: ${e.message}")
            e.printStackTrace()
            return ApiModels.ApiResponse(500, "准备创建问题请求出错: ${e.message}", null)
        }
    }
    
    /**
     * 更新问题状态
     * @param issueId 问题ID
     * @param statusUpdateRequest 状态更新请求
     * @return API响应
     */
    fun updateIssueStatus(issueId: Int, statusUpdateRequest: ApiModels.StatusUpdateRequest): ApiModels.ApiResponse<Any>? {
        try {
            val url = "${getStandardizedApiUrl()}/issues/${issueId}/status"
            val requestBody = objectMapper.writeValueAsString(statusUpdateRequest)
            
            val response = executeHttpRequest(HttpMethod.PATCH, url, requestBody)
            
            if (response.statusCode == 200) {
                return objectMapper.readValue(response.responseBody, object : TypeReference<ApiModels.ApiResponse<Any>>() {})
            } else {
                println("[WARN] 更新问题状态失败: $response.statusCode - ${response.responseBody}")
                return ApiModels.ApiResponse(
                    code = response.statusCode,
                    message = "更新问题状态失败: ${response.responseBody}",
                    data = null
                )
            }
        } catch (e: Exception) {
            println("[ERROR] 更新问题状态时发生异常")
            e.printStackTrace()
            return ApiModels.ApiResponse(
                code = 500,
                message = "更新问题状态时发生异常: ${e.message}",
                data = null
            )
        }
    }
    
    /**
     * 更新问题字段
     * @param issueId 问题ID
     * @param updateRequest 更新请求
     * @return API响应
     */
    fun updateIssueField(issueId: Int, updateRequest: ApiModels.IssueUpdateRequest): ApiModels.ApiResponse<Any>? {
        try {
            val url = "${getStandardizedApiUrl()}/issues/${issueId}/fields"
            val requestBody = objectMapper.writeValueAsString(updateRequest)
            
            println("[DEBUG] 更新问题字段, URL: $url, 请求体: $requestBody")
            
            val response = executeHttpRequest(HttpMethod.PATCH, url, requestBody)
            
            if (response.statusCode == 200) {
                println("[DEBUG] 更新问题字段成功: ${response.responseBody}")
                return objectMapper.readValue(response.responseBody, object : TypeReference<ApiModels.ApiResponse<Any>>() {})
            } else {
                println("[WARN] 更新问题字段失败: ${response.statusCode} - ${response.responseBody}")
                return ApiModels.ApiResponse(
                    code = response.statusCode,
                    message = "更新问题字段失败: ${response.responseBody}",
                    data = null
                )
            }
        } catch (e: Exception) {
            println("[ERROR] 更新问题字段时发生异常")
            e.printStackTrace()
            return ApiModels.ApiResponse(
                code = 500,
                message = "更新问题字段时发生异常: ${e.message}",
                data = null
            )
        }
    }
    
    /**
     * 获取问题详情
     * @param issueId 问题ID
     * @return API响应
     */
    fun getIssueDetail(issueId: Int): ApiModels.ApiResponse<ApiModels.IssueDetail>? {
        if (accessToken == null) {
            println("[ERROR] 尝试获取问题详情但没有访问令牌")
            return null
        }
        
        try {
            val url = "${getStandardizedApiUrl()}/issues/$issueId"
            val response = executeHttpRequest(HttpMethod.GET, url)
            
            return if (response.statusCode == 200) {
                objectMapper.readValue(response.responseBody, 
                    object : TypeReference<ApiModels.ApiResponse<ApiModels.IssueDetail>>() {})
            } else {
                ApiModels.ApiResponse(
                    code = response.statusCode,
                    message = "获取问题详情失败: ${response.responseBody}",
                    data = null
                )
            }
                    } catch (e: Exception) {
            println("[ERROR] 获取问题详情时发生异常: ${e.message}")
                        e.printStackTrace()
            return ApiModels.ApiResponse(
                code = 500,
                message = "获取问题详情时发生异常: ${e.message}",
                data = null
            )
        }
    }

    /**
     * 获取项目问题列表
     * @param projectId 项目ID
     * @param page 页码
     * @param pageSize 每页数量
     * @param maxRetries 最大重试次数
     * @return 项目问题列表响应
     */
    fun getProjectIssues(projectId: Int, page: Int = 1, pageSize: Int = 50, maxRetries: Int = 3): Any {
        if (accessToken == null) {
            println("[ERROR] 尝试获取项目问题列表但没有访问令牌")
            return ApiModels.ApiResponse(401, "没有访问令牌", null, null)
        }
        
        var retryCount = 0
        var lastException: Exception? = null
        
        while (retryCount < maxRetries) {
            try {
                println("[DEBUG] 获取项目问题列表，尝试 ${retryCount + 1}/$maxRetries")
                
                // 构建URL
                val url = "${getStandardizedApiUrl()}/issues?project_id=$projectId&page=$page&page_size=$pageSize"
                
                // 执行请求
                val response = executeHttpRequest(HttpMethod.GET, url)
                
                if (response.statusCode == 200) {
                    val responseBody = response.responseBody
                    
                    try {
                        // 首先解析外层结构
                        val outerResponse = objectMapper.readValue<ApiModels.ApiResponse<Any>>(
                            responseBody,
                            object : TypeReference<ApiModels.ApiResponse<Any>>() {}
                        )
                        
                        // 如果外层data是一个对象，并且该对象有嵌套data字段，说明是双层结构
                        if (outerResponse.data is Map<*, *>) {
                            val innerData = outerResponse.data
                            
                            // 检查是否有嵌套的data字段
                            if (innerData.containsKey("data") && innerData["data"] is List<*>) {
                                val issuesList = objectMapper.convertValue(
                                    innerData["data"],
                                    object : TypeReference<List<ApiModels.IssueListItem>>() {}
                                )
                                
                                // 提取分页信息
                                val pageInfoMap = if (innerData.containsKey("page_info") && innerData["page_info"] is Map<*, *>) {
                                    val pageInfo = innerData["page_info"] as? Map<String, Any>
                                    pageInfo
                                } else {
                                    mapOf(
                                        "total" to issuesList.size,
                                        "page" to page,
                                        "page_size" to pageSize,
                                        "total_pages" to 1
                                    )
                                }
                                
                                val total = if (pageInfoMap != null && pageInfoMap.containsKey("total")) {
                                    val totalValue = pageInfoMap["total"]
                                    when (totalValue) {
                                        is Number -> totalValue.toInt()
                                        else -> issuesList.size
                    }
                } else {
                                    issuesList.size
                                }
                                
                                // 创建PageResponse对象
                                val pageResponse = ApiModels.PageResponse(
                                    total = total,
                                    items = issuesList
                                )
                                
                                // 返回包装好的ApiResponse
                                return ApiModels.ApiResponse(
                                    code = outerResponse.code,
                                    message = outerResponse.message,
                                    timestamp = outerResponse.timestamp,
                                    data = pageResponse
                                )
                            }
                        }
                        
                        // 尝试直接解析为PageResponse格式
                        try {
                            println("[DEBUG] 尝试将数据解析为PageResponse")
                            // 打印原始JSON结构用于调试
                            val dataString = objectMapper.writeValueAsString(outerResponse.data)
                            println("[DEBUG] 数据结构: $dataString")
                            
                            // 先解析为JsonNode，检查结构
                            val dataNode = objectMapper.readTree(dataString)
                            if (dataNode.has("items") && dataNode.get("items").isArray) {
                                // 正常的PageResponse结构
                                val pageResponse = objectMapper.readValue<ApiModels.PageResponse<ApiModels.ProjectInfo>>(
                                    dataString,
                                    object : TypeReference<ApiModels.PageResponse<ApiModels.ProjectInfo>>() {}
                                )
                                
                                println("[INFO] 成功解析项目列表，共${pageResponse.items.size}个项目")
                            return ApiModels.ApiResponse(
                                code = outerResponse.code,
                                message = outerResponse.message,
                                timestamp = outerResponse.timestamp,
                                data = pageResponse
                            )
                            } else {
                                println("[WARN] 数据结构不包含预期的items字段，尝试其他解析方法")
                            }
        } catch (e: Exception) {
                            println("[WARN] 无法解析为PageResponse: ${e.message}")
                        }
                        
                        // 尝试检查是否是一个问题列表
                        try {
                            val issuesList = objectMapper.convertValue(
                                outerResponse.data,
                                object : TypeReference<List<ApiModels.IssueListItem>>() {}
                            )
                            
                            val pageResponse = ApiModels.PageResponse(
                                total = issuesList.size,
                                items = issuesList
                            )
                            
                            return ApiModels.ApiResponse(
                                code = outerResponse.code,
                                message = outerResponse.message,
                                timestamp = outerResponse.timestamp,
                                data = pageResponse
                            )
                        } catch (e: Exception) {
                            println("[WARN] 无法解析为问题列表: ${e.message}")
            e.printStackTrace()
                        }
                        
                        // 返回错误信息
                        println("[ERROR] 无法解析项目问题列表响应")
                        return ApiModels.ApiResponse(
                            code = 500,
                            message = "无法解析项目问题列表响应",
                            data = null
                        )
                    } catch (e: Exception) {
                        println("[ERROR] 解析项目问题列表响应失败: ${e.message}")
                        e.printStackTrace()
                        return ApiModels.ApiResponse(
                            code = 500,
                            message = "解析项目问题列表响应失败: ${e.message}",
                            data = null
                        )
                    }
                } else {
                    // 如果是401错误，说明token过期，直接返回
                    if (response.statusCode == 401) {
                        println("[ERROR] 授权失败，需要重新登录")
                        return ApiModels.ApiResponse(
                            code = 401,
                            message = "授权失败，需要重新登录",
                            data = null
                        )
                    }
                    
                    println("[WARN] 获取项目问题列表失败: ${response.statusCode}")
                    return ApiModels.ApiResponse(
                        code = response.statusCode,
                        message = "获取项目问题列表失败: ${response.responseBody}",
                        data = null
                    )
                }
            } catch (e: Exception) {
                lastException = e
                println("[ERROR] 获取项目问题列表时发生异常 (尝试 ${retryCount + 1}/$maxRetries): ${e.message}")
                e.printStackTrace()
                retryCount++
                
                if (retryCount < maxRetries) {
                    // 指数退避重试
                    val sleepTime = (2 shl retryCount) * 100L
                    println("[INFO] 将在 $sleepTime 毫秒后重试")
                    Thread.sleep(sleepTime)
                }
            }
        }
        
        // 达到最大重试次数，返回错误
        return ApiModels.ApiResponse(
            code = 500,
            message = "获取项目问题列表失败，达到最大重试次数: ${lastException?.message ?: "未知错误"}",
            data = null
        )
    }

    /**
     * 添加评论
     * @param issueId 问题ID
     * @param request 评论内容请求
     * @return 添加评论响应
     */
    fun addComment(issueId: Int, request: ApiModels.CommentCreateRequest): ApiModels.ApiResponse<Any>? {
        if (accessToken == null) {
            println("[ERROR] 尝试添加评论但没有访问令牌")
            return null
        }
        
        try {
            val url = "${getStandardizedApiUrl()}/issues/$issueId/comments"
            println("[DEBUG] 添加评论: $url")
            
            val requestJson = objectMapper.writeValueAsString(request)
            val response = executeHttpRequest(HttpMethod.POST, url, requestJson)
            
            return if (response.statusCode == 200) {
                objectMapper.readValue(response.responseBody, 
                    object : TypeReference<ApiModels.ApiResponse<Any>>() {})
            } else {
                ApiModels.ApiResponse(
                    code = response.statusCode,
                    message = "添加评论失败: ${response.responseBody}",
                    data = null
                )
            }
        } catch (e: Exception) {
            println("[ERROR] 添加评论时发生异常: ${e.message}")
            e.printStackTrace()
            return ApiModels.ApiResponse(
                code = 500,
                message = "添加评论时发生异常: ${e.message}",
                data = null
            )
        }
    }
    
    /**
     * 获取项目成员列表
     * @param projectId 项目ID
     * @param page 页码，默认为1
     * @param pageSize 每页数量，默认为100
     * @return 项目成员列表
     */
    fun getProjectMembers(projectId: Int, page: Int = 1, pageSize: Int = 100): ApiModels.ApiResponse<List<ApiModels.ProjectMember>>? {
        if (accessToken == null) {
            println("[ERROR] 尝试获取项目成员列表但没有访问令牌")
            return null
        }
        
        val url = "${getStandardizedApiUrl()}/projects/$projectId/members?page=$page&page_size=$pageSize"
        println("[DEBUG] 获取项目成员列表: $url")
        
        val request = Request.Builder()
            .url(url)
            .header("Authorization", "Bearer $accessToken")
            .get()
            .build()
            
        try {
            client.newCall(request).execute().use { response ->
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    println("[DEBUG] 获取项目成员列表成功，开始解析数据")
                    println("[DEBUG] 响应数据: ${responseBody.take(500)}...")
                    
                    try {
                        // 解析JSON响应
                        val jsonNode = objectMapper.readTree(responseBody)
                        val code = jsonNode.get("code").asInt()
                        val message = jsonNode.get("message").asText()
                        val timestamp = if (jsonNode.has("timestamp")) jsonNode.get("timestamp").asText() else null
                        
                        if (code == 200 && jsonNode.has("data")) {
                            val dataNode = jsonNode.get("data")
                            
                            if (dataNode.isArray) {
                                // 手动解析成员列表
                                val members = mutableListOf<ApiModels.ProjectMember>()
                                
                                dataNode.forEach { memberNode ->
                                    try {
                                        val userId = memberNode.get("user_id").asInt()
                                        val username = memberNode.get("username").asText()
                                        val roleId = memberNode.get("role_id").asInt()
                                        val roleName = memberNode.get("role_name").asText()
                                        val isActive = memberNode.get("is_active").asBoolean()
                                        val joinedAt = memberNode.get("joined_at").asText()
                                        
                                        members.add(ApiModels.ProjectMember(
                                            userId = userId,
                                            username = username,
                                            roleId = roleId,
                                            roleName = roleName,
                                            isActive = isActive,
                                            joinedAt = joinedAt
                                        ))
                    } catch (e: Exception) {
                                        println("[ERROR] 解析项目成员信息失败: ${e.message}")
                        e.printStackTrace()
                                    }
                                }
                                
                                println("[DEBUG] 成功解析${members.size}个项目成员")
                                
                                return ApiModels.ApiResponse(
                                    code = code,
                                    message = message,
                                    timestamp = timestamp,
                                    data = members
                                )
                            }
                        }
                        
                        println("[WARN] 获取项目成员列表失败，格式不符: $code - $message")
                        return ApiModels.ApiResponse(
                            code = code,
                            message = message,
                            timestamp = timestamp,
                            data = null
                        )
                    } catch (e: Exception) {
                        println("[ERROR] 解析项目成员列表失败: ${e.message}")
                        e.printStackTrace()
                        return ApiModels.ApiResponse(
                            code = 500,
                            message = "解析项目成员列表失败: ${e.message}",
                            data = null
                        )
                    }
                } else {
                    val errorCode = response.code
                    val errorMessage = response.message
                    println("[ERROR] 获取项目成员列表HTTP错误: $errorCode - $errorMessage")
                    
                    return ApiModels.ApiResponse(
                        code = errorCode,
                        message = "获取项目成员列表失败: $errorMessage",
                        data = null
                    )
                }
            }
        } catch (e: Exception) {
            println("[ERROR] 获取项目成员列表异常: ${e.message}")
            e.printStackTrace()
            
            return ApiModels.ApiResponse(
                code = 500,
                message = "获取项目成员列表发生异常: ${e.message}",
                data = null
            )
        }
    }
    
    /**
     * 获取用户列表
     * @param page 页码，默认为1
     * @param pageSize 每页数量，默认为100
     * @param projectId 项目ID，如果指定则只返回该项目的用户
     * @return 用户列表响应
     */
    fun getUsers(page: Int = 1, pageSize: Int = 100, projectId: Int? = null): ApiModels.ApiResponse<ApiModels.UserListResponse>? {
        if (accessToken == null) {
            println("[ERROR] 尝试获取用户列表但没有访问令牌")
            return null
        }
        
        // 构建正确的URL，使用统一方法获取基础URL
        val baseUrl = getBaseServerUrl()
        val projectParam = if (projectId != null) "&project_id=$projectId" else ""
        val request = Request.Builder()
            .url("$baseUrl/api/v1/users?page=$page&page_size=$pageSize$projectParam")
            .header("Authorization", "Bearer $accessToken")
            .get()
            .build()
            
        println("[DEBUG] 发送获取用户列表请求: ${request.url}")
        
        try {
            client.newCall(request).execute().use { response ->
                val responseBody = response.body?.string()
                
                if (response.isSuccessful && responseBody != null) {
                    println("[DEBUG] 获取用户列表成功，开始解析数据")
                    println("[DEBUG] 响应数据: ${responseBody.take(500)}...")
                    
                    // 直接解析JSON并手动构建对象
                    val jsonNode = objectMapper.readTree(responseBody)
                    val code = jsonNode.get("code").asInt()
                    val message = jsonNode.get("message").asText()
                    val timestamp = if (jsonNode.has("timestamp")) jsonNode.get("timestamp").asText() else null
                    
                    if (code == 200 && jsonNode.has("data")) {
                        val dataNode = jsonNode.get("data")
                        
                        // 手动解析用户列表
                        val users = mutableListOf<ApiModels.UserInfo>()
                        val itemsNode = dataNode.get("items")
                        if (itemsNode != null && itemsNode.isArray) {
                            itemsNode.forEach { userNode ->
                                try {
                                    val id = userNode.get("id").asInt()
                                    val userId = if (userNode.has("user_id")) userNode.get("user_id").asText() else null
                                    val username = userNode.get("username").asText()
                                    val email = if (userNode.has("email")) userNode.get("email").asText() else null
                                    val phone = if (userNode.has("phone")) userNode.get("phone").asText() else null
                                    val isActive = if (userNode.has("is_active")) userNode.get("is_active").asBoolean() else true
                                    val createdAt = if (userNode.has("created_at")) userNode.get("created_at").asText() else null
                                    val updatedAt = if (userNode.has("updated_at")) userNode.get("updated_at").asText() else null
                                    
                                    // 处理roles字段 - 可能是字符串数组
                                    val rolesList = mutableListOf<ApiModels.UserInfo.Role>()
                                    if (userNode.has("roles") && userNode.get("roles").isArray) {
                                        val rolesNode = userNode.get("roles")
                                        rolesNode.forEach { roleNode ->
                                            if (roleNode.isTextual) {
                                                // 字符串角色
                                                rolesList.add(ApiModels.UserInfo.Role(name = roleNode.asText()))
                                            } else if (roleNode.isObject) {
                                                // 对象角色
                                                val roleId = if (roleNode.has("id")) roleNode.get("id").asInt() else null
                                                val roleName = if (roleNode.has("name")) roleNode.get("name").asText() else null
                                                rolesList.add(ApiModels.UserInfo.Role(id = roleId, name = roleName))
                                            }
                                        }
                                    }
                                    
                                    // 创建UserInfo对象并添加到列表
                                    users.add(ApiModels.UserInfo(
                                        id = id,
                                        userId = userId,
                                        username = username,
                                        email = email,
                                        phone = phone,
                                        isActive = isActive,
                                        createdAt = createdAt,
                                        updatedAt = updatedAt,
                                        roles = rolesList
                                    ))
                                } catch (e: Exception) {
                                    println("[ERROR] 解析用户信息失败: ${e.message}")
                                    e.printStackTrace()
                                }
                            }
                        }
                        
                        val total = if (dataNode.has("total")) dataNode.get("total").asInt() else users.size
                        val responsePage = if (dataNode.has("page")) dataNode.get("page").asInt() else page
                        val size = if (dataNode.has("size")) dataNode.get("size").asInt() else pageSize
                        val pages = if (dataNode.has("pages")) dataNode.get("pages").asInt() else 1
                        
                        val userListResponse = ApiModels.UserListResponse(
                            items = users,
                            total = total,
                            page = responsePage,
                            size = size,
                            pages = pages
                        )
                        
                        println("[DEBUG] 手动解析成功，共${users.size}个用户")
                        
                        return ApiModels.ApiResponse(
                            code = code,
                            message = message,
                            timestamp = timestamp,
                            data = userListResponse
                        )
                } else {
                        println("[WARN] 获取用户列表失败: $code - $message")
                        return ApiModels.ApiResponse(
                            code = code,
                            message = message,
                            timestamp = timestamp,
                            data = null
                        )
                    }
                } else {
                    val errorCode = response.code
                    val errorMessage = response.message
                    println("[ERROR] 获取用户列表HTTP错误: $errorCode - $errorMessage")
                    return ApiModels.ApiResponse(
                        code = errorCode, 
                        message = "获取用户列表失败: $errorMessage"
                    )
                }
            }
        } catch (e: Exception) {
            println("[ERROR] 获取用户列表异常: ${e.message}")
            e.printStackTrace()
            return ApiModels.ApiResponse(
                code = 500,
                message = "获取用户列表发生异常: ${e.message}"
            )
        }
    }

    /**
     * 执行HTTP请求
     * @param method HTTP方法
     * @param url 请求URL
     * @param requestBody 请求体
     * @param headers 额外的请求头
     * @return HTTP响应
     */
    private fun executeHttpRequest(
        method: HttpMethod,
        url: String,
        requestBody: String? = null,
        headers: Map<String, String> = emptyMap()
    ): HttpResponse {
        try {
            println("[DEBUG] 执行HTTP请求: $method $url")
            
            // 创建请求构建器
            val requestBuilder = Request.Builder().url(url)
            
            // 添加认证头
            if (accessToken != null) {
                requestBuilder.addHeader("Authorization", "Bearer $accessToken")
            }
            
            // 添加额外的请求头
            headers.forEach { (name, value) ->
                requestBuilder.addHeader(name, value)
            }
            
            // 根据HTTP方法设置请求体
            when (method) {
                HttpMethod.GET -> requestBuilder.get()
                HttpMethod.POST -> {
                    val body = requestBody?.toRequestBody("application/json".toMediaType())
                        ?: "{}".toRequestBody("application/json".toMediaType())
                    requestBuilder.post(body)
                }
                HttpMethod.PUT -> {
                    val body = requestBody?.toRequestBody("application/json".toMediaType())
                        ?: "{}".toRequestBody("application/json".toMediaType())
                    requestBuilder.put(body)
                }
                HttpMethod.DELETE -> {
                    if (requestBody != null) {
                        val body = requestBody.toRequestBody("application/json".toMediaType())
                        requestBuilder.delete(body)
                    } else {
                        requestBuilder.delete()
                    }
                }
                HttpMethod.PATCH -> {
                    val body = requestBody?.toRequestBody("application/json".toMediaType())
                        ?: "{}".toRequestBody("application/json".toMediaType())
                    requestBuilder.patch(body)
                }
            }
            
            // 创建请求
            val request = requestBuilder.build()
            println("[DEBUG] 请求头: ${request.headers}")
            if (requestBody != null) {
                println("[DEBUG] 请求体: $requestBody")
            }
            
            // 执行请求
            val call = client.newCall(request)
            ongoingCalls[call] = true
            
            try {
            val response = call.execute()
                ongoingCalls.remove(call)
            
            val responseBody = response.body?.string() ?: ""
            println("[DEBUG] 响应状态码: ${response.code}")
            println("[DEBUG] 响应体: ${responseBody.take(200)}${if (responseBody.length > 200) "..." else ""}")
            
            return HttpResponse(
                statusCode = response.code,
                responseBody = responseBody,
                headers = response.headers
            )
            } catch (e: IOException) {
                // 移除跟踪的调用
                ongoingCalls.remove(call)
                
                // 记录连接失败
                recordConnectionFailure()
                
                println("[ERROR] HTTP请求执行IO异常: ${e.message}")
                e.printStackTrace()
                throw e
            }
        } catch (e: Exception) {
            println("[ERROR] HTTP请求执行出错: ${e.message}")
            e.printStackTrace()
            throw e
        }
    }

    /**
     * 用户登出
     * 清除服务器端的登录状态并清空本地token
     * @return 登出响应
     */
    fun logout(): ApiModels.ApiResponse<Any>? {
        if (accessToken == null) {
            println("[INFO] 尝试登出但没有访问令牌，直接返回成功")
            return ApiModels.ApiResponse(200, "成功登出", null)
        }

        try {
            val url = "${getStandardizedApiUrl()}/auth/logout"
            println("[INFO] 用户登出: $url")
            
            val request = Request.Builder()
                .url(url)
                .header("Authorization", "Bearer $accessToken")
                .post("{}".toRequestBody("application/json".toMediaType()))
                .build()
            
            val call = client.newCall(request)
            val response = call.execute()
            val responseBody = response.body?.string()
            
            // 无论服务器响应如何，都清除本地token
            accessToken = null
            
            println("[INFO] 登出响应状态码: ${response.code}")
            println("[DEBUG] 登出响应体: $responseBody")
            
            return if (response.isSuccessful) {
                try {
                    objectMapper.readValue(responseBody, object : TypeReference<ApiModels.ApiResponse<Any>>() {})
                } catch (e: Exception) {
                    ApiModels.ApiResponse(200, "成功登出", null)
                }
            } else {
                ApiModels.ApiResponse(response.code, "登出请求返回错误: ${response.message}", null)
            }
        } catch (e: Exception) {
            println("[ERROR] 执行登出请求时出错: ${e.message}")
            e.printStackTrace()
            
            // 即使请求失败，也要清除本地token
            accessToken = null
            
            return ApiModels.ApiResponse(500, "执行登出请求出错: ${e.message}", null)
        }
    }

    /**
     * 更新整个问题
     * @param issueId 问题ID
     * @param updateData 更新数据
     * @return API响应
     */
    fun updateIssue(issueId: Int, updateData: Map<String, Any?>): ApiModels.ApiResponse<Any>? {
        try {
            val url = "${settings.getApiUrl()}/issues/${issueId}"
            val requestBody = objectMapper.writeValueAsString(updateData)
            
            println("[DEBUG] 更新问题, URL: $url, 请求体: $requestBody")
            
            val response = executeHttpRequest(HttpMethod.PUT, url, requestBody)
            
            if (response.statusCode == 200) {
                println("[DEBUG] 更新问题成功: ${response.responseBody}")
                return objectMapper.readValue(response.responseBody, object : TypeReference<ApiModels.ApiResponse<Any>>() {})
            } else {
                println("[WARN] 更新问题失败: ${response.statusCode} - ${response.responseBody}")
                return ApiModels.ApiResponse(
                    code = response.statusCode,
                    message = "更新问题失败: ${response.responseBody}",
                    data = null
                )
            }
        } catch (e: Exception) {
            println("[ERROR] 更新问题时发生异常")
            e.printStackTrace()
            return ApiModels.ApiResponse(
                code = 500,
                message = "更新问题时发生异常: ${e.message}",
                data = null
            )
        }
    }

    /**
     * 检测后端连接状态
     * 用于应用启动或从休眠恢复时调用，确保连接正常
     * @return 连接是否正常
     */
    fun checkBackendConnection(): Boolean {
        println("[INFO] 开始检测后端连接状态...")
        
        // 使用健康检查端点或任何轻量级API
        val url = "${settings.getApiUrl()}/health"
        
        val request = Request.Builder()
            .url(url)
            .get()
            .build()
            
        var call: Call? = null
        try {
            // 设置更短的超时时间，避免长时间等待
            val quickClient = OkHttpClient.Builder()
                .connectTimeout(5, TimeUnit.SECONDS)
                .readTimeout(5, TimeUnit.SECONDS)
                .writeTimeout(5, TimeUnit.SECONDS)
                .build()
                
            call = quickClient.newCall(request)
            val response = call.execute()
            
            val isSuccess = response.isSuccessful
            println("[INFO] 后端连接状态检测: ${if (isSuccess) "正常" else "异常 - ${response.code}"}")
            
            // 如果曾经有连接问题，重置连接计数
            if (isSuccess && connectionFailureCount > 0) {
                println("[INFO] 检测到后端已恢复，重置连接失败计数")
                connectionFailureCount = 0
            }
            
            return isSuccess
        } catch (e: IOException) {
            println("[WARN] 后端连接检测失败: ${e.message}")
            
            // 记录连接失败
            recordConnectionFailure()
            
            // 尝试重置客户端，让下一次正常请求能成功
            if (connectionFailureCount >= MAX_FAILURES_BEFORE_RESET) {
                println("[INFO] 由于检测连接失败，执行预防性HTTP客户端重置")
                resetHttpClient()
            }
            
            return false
        } catch (e: Exception) {
            println("[ERROR] 检测后端连接状态时发生错误: ${e.message}")
            e.printStackTrace()
            return false
        } finally {
            // 清理资源
            if (call != null && !call.isExecuted()) {
                call.cancel()
            }
        }
    }
    
    /**
     * 应用周期事件处理 - 当应用从休眠中恢复时调用
     * 此方法应在应用唤醒时被外部组件调用
     */
    fun onApplicationResume() {
        println("[INFO] 应用从休眠中恢复，检查后端连接状态")
        
        // 在后台线程中执行连接检测
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val isConnected = checkBackendConnection()
                
                if (!isConnected) {
                    // 如果检测失败，重置HTTP客户端
                    println("[INFO] 应用恢复后检测到连接问题，重置HTTP客户端")
                    resetHttpClient()
                }
            } catch (e: Exception) {
                println("[ERROR] 应用恢复检查时出错: ${e.message}")
            }
        }
    }

    /**
     * 获取项目列表
     */
    fun getProjects(page: Int = 1, pageSize: Int = 10, maxRetries: Int = 3): ApiModels.ApiResponse<ApiModels.PageResponse<ApiModels.ProjectInfo>>? {
        if (accessToken == null) {
            println("[ERROR] 尝试获取项目列表但没有访问令牌")
            return ApiModels.ApiResponse(401, "没有访问令牌", null)
        }
        
        var retryCount = 0
        var lastException: Exception? = null
        
        while (retryCount < maxRetries) {
            try {
                println("[DEBUG] 获取项目列表，尝试 ${retryCount + 1}/$maxRetries")
                
                // 构建URL
                val url = "${getStandardizedApiUrl()}/projects?page=$page&page_size=$pageSize"
                
                // 执行请求
                val response = executeHttpRequest(HttpMethod.GET, url)
                
                if (response.statusCode == 200) {
                    val responseBody = response.responseBody
                    
                    try {
                        // 首先解析外层结构
                        val outerResponse = objectMapper.readValue<ApiModels.ApiResponse<Any>>(
                            responseBody,
                            object : TypeReference<ApiModels.ApiResponse<Any>>() {}
                        )
                        
                        // 记录一下响应的数据结构，用于调试
                        val dataString = objectMapper.writeValueAsString(outerResponse.data)
                        println("[DEBUG] 项目响应数据结构: ${dataString.take(500)}...")
                        
                        // 尝试解析方法1: 直接尝试转换为PageResponse
                        try {
                            println("[DEBUG] 尝试解析方法1: 直接转换为PageResponse")
                            
                            // 先解析为JsonNode，检查结构
                            val dataNode = objectMapper.readTree(dataString)
                            println("[DEBUG] 数据节点类型: ${dataNode.nodeType}, 是对象: ${dataNode.isObject}, 是数组: ${dataNode.isArray}")
                            println("[DEBUG] 数据节点字段: ${dataNode.fieldNames().asSequence().toList()}")
                            
                            if (dataNode.has("items") && dataNode.get("items").isArray) {
                                // 正常的PageResponse结构
                                val pageResponse = objectMapper.readValue<ApiModels.PageResponse<ApiModels.ProjectInfo>>(
                                    dataString,
                                    object : TypeReference<ApiModels.PageResponse<ApiModels.ProjectInfo>>() {}
                                )
                                
                                println("[INFO] 成功解析项目列表，共${pageResponse.items.size}个项目")
                                return ApiModels.ApiResponse(
                                    code = outerResponse.code,
                                    message = outerResponse.message,
                                    timestamp = outerResponse.timestamp,
                                    data = pageResponse
                                )
                            }
                        } catch (e: Exception) {
                            println("[WARN] 解析方法1失败: ${e.message}")
                            e.printStackTrace()
                        }
                        
                        // 尝试解析方法2: 处理双层嵌套结构
                        if (outerResponse.data is Map<*, *>) {
                            try {
                                println("[DEBUG] 尝试解析方法2: 处理双层嵌套结构")
                                val innerData = outerResponse.data
                                println("[DEBUG] 内部数据结构类型: ${innerData?.javaClass?.name}")
                                println("[DEBUG] 内部数据字段: ${innerData?.let { (it as? Map<*, *>)?.keys }}") 
                                
                                // 检查是否有嵌套的data或items字段
                                val projectsList = if (innerData.containsKey("data") && innerData["data"] is List<*>) {
                                    println("[DEBUG] 发现内部data字段")
                                    objectMapper.convertValue(
                                        innerData["data"],
                                        object : TypeReference<List<ApiModels.ProjectInfo>>() {}
                                    )
                                } else if (innerData.containsKey("items") && innerData["items"] is List<*>) {
                                    println("[DEBUG] 发现内部items字段")
                                    objectMapper.convertValue(
                                        innerData["items"],
                                        object : TypeReference<List<ApiModels.ProjectInfo>>() {}
                                    )
                                } else {
                                    null
                                }
                                
                                if (projectsList != null) {
                                    // 提取分页信息
                                    val total = innerData["total"] as? Int ?: projectsList.size
                                    val responsePage = innerData["page"] as? Int ?: page
                                    val size = innerData["size"] as? Int ?: pageSize
                                    val pages = innerData["pages"] as? Int ?: 1
                                    
                                    // 创建PageResponse对象
                                    val pageResponse = ApiModels.PageResponse(
                                        total = total,
                                        items = projectsList,
                                        page = responsePage,
                                        size = size,
                                        pages = pages
                                    )
                                    
                                    println("[INFO] 成功解析项目列表(方法2)，共${projectsList.size}个项目")
                                    return ApiModels.ApiResponse(
                                        code = outerResponse.code,
                                        message = outerResponse.message,
                                        timestamp = outerResponse.timestamp,
                                        data = pageResponse
                                    )
                                }
                            } catch (e: Exception) {
                                println("[WARN] 解析方法2失败: ${e.message}")
                                e.printStackTrace()
                            }
                        }
                        
                        // 尝试解析方法3: 假设data直接是项目列表
                        try {
                            println("[DEBUG] 尝试解析方法3: 直接解析为项目列表")
                            println("[DEBUG] data类型: ${outerResponse.data?.javaClass?.name}")
                            val projectsList = objectMapper.convertValue(
                                outerResponse.data,
                                object : TypeReference<List<ApiModels.ProjectInfo>>() {}
                            )
                            
                            println("[DEBUG] 项目列表解析成功，大小: ${projectsList.size}")
                            val pageResponse = ApiModels.PageResponse(
                                total = projectsList.size,
                                items = projectsList
                            )
                            
                            println("[INFO] 成功解析项目列表(方法3)，共${projectsList.size}个项目")
                            return ApiModels.ApiResponse(
                                code = outerResponse.code,
                                message = outerResponse.message,
                                timestamp = outerResponse.timestamp,
                                data = pageResponse
                            )
                        } catch (e: Exception) {
                            println("[WARN] 解析方法3失败: ${e.message}")
                        }
                        
                        // 所有解析方法都失败，尝试手动构建最小可用数据
                        println("[WARN] 所有解析方法都失败，尝试构建空项目列表")
                        val emptyResponse = ApiModels.PageResponse<ApiModels.ProjectInfo>(
                            total = 0,
                            items = emptyList()
                        )
                        return ApiModels.ApiResponse(
                            code = outerResponse.code,
                            message = "无法解析项目列表，返回空列表",
                            timestamp = outerResponse.timestamp,
                            data = emptyResponse
                        )
                    } catch (e: Exception) {
                        println("[ERROR] 解析项目列表响应失败: ${e.message}")
                        e.printStackTrace()
                        return ApiModels.ApiResponse(
                            code = 500,
                            message = "解析项目列表响应失败: ${e.message}",
                            data = null
                        )
                    }
                } else {
                    // 如果是401错误，说明token过期，直接返回
                    if (response.statusCode == 401) {
                        println("[ERROR] 授权失败，需要重新登录")
                        return ApiModels.ApiResponse(
                            code = 401,
                            message = "授权失败，需要重新登录",
                            data = null
                        )
                    }
                    
                    println("[WARN] 获取项目列表失败: ${response.statusCode}")
                    return ApiModels.ApiResponse(
                        code = response.statusCode,
                        message = "获取项目列表失败: ${response.responseBody}",
                        data = null
                    )
                }
            } catch (e: Exception) {
                lastException = e
                println("[ERROR] 获取项目列表时发生异常 (尝试 ${retryCount + 1}/$maxRetries): ${e.message}")
                e.printStackTrace()
                retryCount++
                
                if (retryCount < maxRetries) {
                    // 指数退避重试
                    val sleepTime = (2 shl retryCount) * 100L
                    println("[INFO] 将在 $sleepTime 毫秒后重试")
                    Thread.sleep(sleepTime)
                }
            }
        }
        
        // 达到最大重试次数，返回错误
        return ApiModels.ApiResponse(
            code = 500,
            message = "获取项目列表失败，达到最大重试次数: ${lastException?.message ?: "未知错误"}",
            data = null
        )
    }

    /**
     * 获取和标准化 API URL
     * 处理不同格式的 URL 并返回一致的格式
     */
    private fun getStandardizedApiUrl(): String {
        val url = settings.getApiUrl().trim()
        
        // 移除结尾的斜杠以便后续添加路径时格式统一
        return url.removeSuffix("/")
    }

    /**
     * 获取 API 基础 URL
     * 如果 URL 包含 /api/v1，则移除这部分，返回基础URL
     */
    private fun getBaseServerUrl(): String {
        val url = settings.getApiUrl().trim()
        
        // 针对不同格式的 URL 进行处理，确保返回不包含 API 路径的服务器地址
        return url.replace(Regex("/api(/v1)?/?$"), "")
    }

    /**
     * 获取问题状态列表
     * @return 问题状态列表
     */
    fun getIssueStatuses(): ApiModels.ApiResponse<List<ApiModels.IssueStatus>>? {
        if (accessToken == null) {
            println("[ERROR] 尝试获取问题状态列表但没有访问令牌")
            return null
        }

        val url = "${getStandardizedApiUrl()}/issue-statuses"
        println("[DEBUG] 获取问题状态列表: $url")
        
        try {
            val response = executeHttpRequest(HttpMethod.GET, url)
            
            if (response.statusCode == 200) {
                val responseBody = response.responseBody
                
                try {
                    return objectMapper.readValue(
                        responseBody,
                        object : TypeReference<ApiModels.ApiResponse<List<ApiModels.IssueStatus>>>() {}
                    )
                } catch (e: Exception) {
                    println("[ERROR] 解析问题状态列表响应失败: ${e.message}")
                    e.printStackTrace()
                    return ApiModels.ApiResponse(response.statusCode, "解析问题状态列表响应失败", null)
                }
            } else {
                return ApiModels.ApiResponse(response.statusCode, response.responseBody, null)
            }
        } catch (e: Exception) {
            println("[ERROR] 获取问题状态列表失败: ${e.message}")
            e.printStackTrace()
            return ApiModels.ApiResponse(500, "获取问题状态列表失败", null)
        }
    }
    
    /**
     * 获取提交详情
     * @param commitId 提交ID
     * @return 提交详情
     */
    fun getCommitDetail(commitId: String): ApiModels.ApiResponse<ApiModels.CommitDetail>? {
        if (accessToken == null) {
            println("[ERROR] 尝试获取提交详情但没有访问令牌")
            return null
        }

        val url = "${getStandardizedApiUrl()}/commits/$commitId"
        println("[DEBUG] 获取提交详情: $url")
        
        try {
            val response = executeHttpRequest(HttpMethod.GET, url)
            
            if (response.statusCode == 200) {
                val responseBody = response.responseBody
                
                try {
                    return objectMapper.readValue(
                        responseBody,
                        object : TypeReference<ApiModels.ApiResponse<ApiModels.CommitDetail>>() {}
                    )
                } catch (e: Exception) {
                    println("[ERROR] 解析提交详情响应失败: ${e.message}")
                    e.printStackTrace()
                    return ApiModels.ApiResponse(response.statusCode, "解析提交详情响应失败", null)
                }
            } else {
                return ApiModels.ApiResponse(response.statusCode, response.responseBody, null)
            }
        } catch (e: Exception) {
            println("[ERROR] 获取提交详情失败: ${e.message}")
            e.printStackTrace()
            return ApiModels.ApiResponse(500, "获取提交详情失败", null)
        }
    }
} 