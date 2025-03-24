package com.ant.code.coderplugin.service

import com.ant.code.coderplugin.api.ApiModels
import com.ant.code.coderplugin.api.ApiService
import com.ant.code.coderplugin.listeners.LoginStatusListener
import com.ant.code.coderplugin.settings.AppSettingsState
import com.intellij.credentialStore.CredentialAttributes
import com.intellij.credentialStore.generateServiceName
import com.intellij.ide.passwordSafe.PasswordSafe
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import com.intellij.openapi.util.Disposer
import com.intellij.openapi.Disposable
import java.util.concurrent.atomic.AtomicBoolean

@Service(Service.Level.PROJECT)
class AuthService(private val project: Project) : Disposable {
    private val LOG = Logger.getInstance(AuthService::class.java)
    private val apiService = ApiService.getInstance(project)
    private var currentUser: ApiModels.UserInfo? = null
    private val isDisposed = AtomicBoolean(false)
    private var loginError: String? = null
    
    init {
        // 注册到项目的生命周期
        Disposer.register(project, this)
        LOG.info("AuthService初始化: ${project.name}")
    }
    
    // 确保资源在插件卸载时被释放
    override fun dispose() {
        if (isDisposed.getAndSet(true)) return
        
        try {
            LOG.info("开始释放AuthService资源")
            
            // 清除当前登录用户
            currentUser = null
            
            // 清除保存的凭据，确保登录状态彻底重置
            clearCredentials()
            
            LOG.info("AuthService资源已释放")
        } catch (e: Exception) {
            LOG.error("释放AuthService资源时出错", e)
        }
    }
    
    /**
     * 用户登录
     * @param username 用户名
     * @param password 密码
     * @param rememberMe 是否记住登录状态
     * @return 登录结果
     */
    fun login(username: String, password: String, rememberMe: Boolean = false): Boolean {
        if (isDisposed.get()) {
            LOG.warn("AuthService已释放，无法执行登录操作")
            return false
        }
        
        LOG.info("服务层开始登录: $username")
        
        // 检查是否在EDT线程上执行
        if (ApplicationManager.getApplication().isDispatchThread) {
            LOG.warn("在EDT线程上调用登录方法，这可能导致UI卡顿。建议在后台线程中调用此方法。")
        }
        
        try {
            // 清除之前的错误信息
            loginError = null
            
            // 使用API服务调用登录接口
            val response = apiService.login(username, password, rememberMe)
            
            if (response != null && response.code == 200) {
                // 成功获取响应
                LOG.info("登录请求成功，响应码: ${response.code}")
                
                // 登录成功，先设置token
                // 我们不直接从data中提取token，而是通过API服务来处理
                
                // 再获取用户信息
                fetchCurrentUser()
                
                // 根据当前用户状态判断是否登录成功
                val success = currentUser != null
                
                if (success) {
                    LOG.info("登录成功，当前用户: ${currentUser?.username}")
                    
                    // 缓存登录用户名到设置中
                    val appSettings = AppSettingsState.getInstance()
                    appSettings.loggedInUsername = currentUser?.username ?: ""
                    
                    // 尝试立即获取项目列表并缓存
                    preloadProjectData()
                    
                    // 如果选择了"记住我"，保存用户名和密码
                    if (rememberMe) {
                        saveCredentials(username, password)
                        
                        // 在设置中保存用户名，但不保存密码明文
                        val settings = AppSettingsState.getInstance()
                        settings.savedUsername = username
                    } else {
                        // 否则清除保存的凭据
                        clearCredentials()
                    }
                    
                    // 通知监听器登录状态变化
                    ApplicationManager.getApplication().messageBus.syncPublisher(LoginStatusListener.TOPIC)
                            .onLogin()
                    
                    try {
                        // 刷新UI
                        refreshUI()
                    } catch (e: Exception) {
                        LOG.warn("刷新UI时出错", e)
                    }
                    
                    return true
                } else {
                    // 获取用户信息失败
                    loginError = "获取用户信息失败"
                    LOG.warn("登录失败: 获取用户信息失败")
                    return false
                }
            } else {
                // 登录失败，保存错误信息
                loginError = response?.message ?: "未知错误"
                LOG.warn("登录失败: $loginError")
            }
        } catch (e: Exception) {
            // 发生异常，保存错误信息
            loginError = e.message ?: "网络错误"
            LOG.error("登录时发生异常", e)
        }
        
        return false
    }
    
    /**
     * 预加载项目数据
     */
    private fun preloadProjectData() {
        try {
            // 在后台线程中加载项目列表
            ApplicationManager.getApplication().executeOnPooledThread {
                try {
                    val issueService = project?.let { IssueService.getInstance(it) }
                    if (issueService != null) {
                        println("[DEBUG] 登录成功后预加载项目列表...")
                        val projects = issueService.getProjects(page = 1, pageSize = 100)
                        println("[DEBUG] 成功预加载${projects.size}个项目")
                        
                        // 这里项目数据已经被IssueService缓存，不需要额外存储
                    } else {
                        println("[WARN] 无法获取IssueService实例，跳过项目预加载")
                    }
                } catch (e: Exception) {
                    println("[ERROR] 预加载项目数据失败: ${e.message}")
                    e.printStackTrace()
                }
            }
        } catch (e: Exception) {
            println("[ERROR] 启动预加载任务失败: ${e.message}")
            e.printStackTrace()
        }
    }
    
    /**
     * 退出登录
     * 清空本地用户信息、项目信息、token等
     */
    fun logout() {
        println("[INFO] 用户退出登录")
        
        try {
            // 先调用后台退出登录接口
            val logoutResponse = apiService.logout()
            if (logoutResponse != null) {
                println("[INFO] 后台退出登录接口调用结果: ${logoutResponse.code} - ${logoutResponse.message}")
            } else {
                println("[WARN] 后台退出登录接口调用失败或未返回结果")
            }
            
            // 即使后台接口调用失败，也继续清理本地状态
            
            // 清空API访问令牌 (已在ApiService.logout方法中完成)
            
            // 清空本地用户信息缓存
            currentUser = null
            
            // 清除登录用户名缓存
            val appSettings = AppSettingsState.getInstance()
            appSettings.loggedInUsername = ""
            
            // 清空本地项目信息
            val issueService = IssueService.getInstance(project)
            if (issueService != null) {
                // 清除项目相关信息
                issueService.clearProjectData()
            }
            
            // 清空本地存储的凭证
            val settings = AppSettingsState.getInstance()
            settings.savedUsername = ""
            
            // 清除安全存储的凭据
            clearCredentials()
            
            // 触发登录状态变更通知
            ApplicationManager.getApplication().messageBus.syncPublisher(LoginStatusListener.TOPIC)
                .onLogout()
                
            println("[INFO] 用户登出完成，已清空所有本地数据")
        } catch (e: Exception) {
            println("[ERROR] 退出登录时发生错误: ${e.message}")
            e.printStackTrace()
        }
    }
    
    // 获取当前用户信息
    fun fetchCurrentUser() {
        if (isDisposed.get()) {
            LOG.warn("AuthService已释放，无法获取用户信息")
            return
        }
        
        try {
            LOG.info("开始获取当前用户信息")
            val token = apiService.getAccessToken()
            if (token == null) {
                LOG.warn("获取用户信息失败: 没有访问令牌")
                currentUser = null
                return
            }
            
            LOG.info("使用token获取用户信息: ${token.take(10)}...")
            // 使用重试机制获取用户信息
            val response = apiService.getCurrentUser(maxRetries = 3)
            
            if (response != null) {
                LOG.info("获取用户信息响应: code=${response.code}, message=${response.message}")
                
                if (response.code == 200 && response.data != null) {
                    currentUser = response.data
                    LOG.info("成功获取用户信息: ${currentUser?.username}, ID=${currentUser?.id}")
                } else {
                    LOG.warn("获取用户信息失败: ${response.message}")
                    
                    // 如果是401或其他授权问题，清除当前用户
                    if (response.code == 401) {
                        LOG.warn("授权失败，清除用户状态")
                        currentUser = null
                        apiService.clearAccessToken()
                    }
                }
            } else {
                LOG.warn("获取用户信息失败: API返回null")
                currentUser = null
            }
        } catch (e: Exception) {
            LOG.error("获取当前用户信息时出错", e)
            currentUser = null
        }
    }
    
    // 获取当前登录用户
    fun getCurrentUser(): ApiModels.UserInfo? {
        if (isDisposed.get()) return null
        return currentUser
    }
    
    // 检查是否已登录
    fun isLoggedIn(): Boolean {
        if (isDisposed.get()) return false
        return currentUser != null
    }
    
    /**
     * 尝试自动登录
     * 检查保存的凭据并尝试自动登录
     * @return 登录是否成功
     */
    fun tryAutoLogin(): Boolean {
        if (isLoggedIn()) {
            LOG.info("已登录，无需自动登录")
            return true
        }
        
        // 检查缓存的登录用户名
        val appSettings = AppSettingsState.getInstance()
        val cachedUsername = appSettings.loggedInUsername
        
        // 如果有缓存的用户名，先尝试获取用户信息
        if (cachedUsername.isNotBlank()) {
            LOG.info("发现缓存的登录用户名: $cachedUsername，尝试验证token有效性")
            
            // 尝试获取用户信息，验证缓存的token是否有效
            fetchCurrentUser()
            if (currentUser != null) {
                LOG.info("缓存的token有效，自动登录成功: ${currentUser?.username}")
                
                // 预加载项目信息
                preloadProjectData()
                
                // 触发登录成功事件
                ApplicationManager.getApplication().messageBus.syncPublisher(LoginStatusListener.TOPIC)
                    .onLogin()
                
                return true
            }
            
            // token无效，清除缓存的用户名
            appSettings.loggedInUsername = ""
        }
        
        // 检查保存的凭据
        val savedCredentials = getSavedCredentials()
        if (savedCredentials != null) {
            val (username, password) = savedCredentials
            LOG.info("发现保存的登录凭据，尝试自动登录: $username")
            
            // 尝试使用保存的凭据登录
            return login(username, password, true)
        }
        
        return false
    }
    
    // 保存凭据到密码安全存储
    private fun saveCredentials(userId: String, password: String) {
        if (isDisposed.get()) return
        
        // 使用后台线程执行密码存储操作，避免阻塞EDT
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val credentialAttributes = createCredentialAttributes()
                val credentials = com.intellij.credentialStore.Credentials(userId, password)
                
                PasswordSafe.instance.set(credentialAttributes, credentials)
                
                // 单独保存token
                val tokenAttributes = createTokenAttributes()
                val tokenCredentials = com.intellij.credentialStore.Credentials("token", apiService.getAccessToken() ?: "")
                
                PasswordSafe.instance.set(tokenAttributes, tokenCredentials)
                LOG.info("用户凭据已安全保存")
            } catch (e: Exception) {
                LOG.error("保存凭据时出错", e)
            }
        }
    }
    
    // 获取保存的凭据
    private fun getCredentials(): com.intellij.credentialStore.Credentials? {
        if (isDisposed.get()) return null
        
        try {
            val credentialAttributes = createCredentialAttributes()
            return PasswordSafe.instance.get(credentialAttributes)
        } catch (e: Exception) {
            LOG.error("获取凭据时出错", e)
            return null
        }
    }
    
    /**
     * 获取保存的用户凭据
     * @return 用户名和密码的Pair，如果没有保存凭据则返回null
     */
    fun getSavedCredentials(): Pair<String, String>? {
        if (isDisposed.get()) return null
        
        try {
            val credentials = getCredentials() ?: return null
            val username = credentials.userName ?: return null
            val password = credentials.getPasswordAsString() ?: return null
            
            // 只有当用户名和密码都不为空时才返回
            if (username.isNotBlank() && password.isNotBlank()) {
                return Pair(username, password)
            }
        } catch (e: Exception) {
            LOG.error("获取保存的用户凭据时出错", e)
        }
        
        return null
    }
    
    // 获取保存的token
    fun getSavedToken(): String? {
        if (isDisposed.get()) return null
        
        try {
            val tokenAttributes = createTokenAttributes()
            val credentials = PasswordSafe.instance.get(tokenAttributes)
            
            return credentials?.getPasswordAsString()
        } catch (e: Exception) {
            LOG.error("获取保存的token时出错", e)
            return null
        }
    }
    
    // 清除保存的凭据
    private fun clearCredentials() {
        // 使用后台线程执行密码操作，避免阻塞EDT
        ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val credentialAttributes = createCredentialAttributes()
                PasswordSafe.instance.set(credentialAttributes, null)
                
                val tokenAttributes = createTokenAttributes()
                PasswordSafe.instance.set(tokenAttributes, null)
                LOG.info("用户凭据已清除")
            } catch (e: Exception) {
                LOG.error("清除凭据时出错", e)
            }
        }
    }
    
    // 创建凭据属性
    private fun createCredentialAttributes(): CredentialAttributes {
        return CredentialAttributes(
            generateServiceName("CodeReviewPlugin", "LoginCredentials")
        )
    }
    
    // 创建token属性
    private fun createTokenAttributes(): CredentialAttributes {
        return CredentialAttributes(
            generateServiceName("CodeReviewPlugin", "AccessToken")
        )
    }
    
    // 刷新工具窗口UI
    private fun refreshUI() {
        if (isDisposed.get() || project.isDisposed) return
        
        try {
            // 检查应用是否完全初始化
            val application = ApplicationManager.getApplication()
            if (!application.isUnitTestMode && !application.isHeadlessEnvironment && application.isDispatchThread) {
                // 获取工具窗口并刷新
                val toolWindowManager = com.intellij.openapi.wm.ToolWindowManager.getInstance(project)
                toolWindowManager.getToolWindow("CodeReview")?.let { toolWindow ->
                    val contents = toolWindow.contentManager.contents
                    if (contents.isNotEmpty()) {
                        val content = contents[0]
                        val component = content.component
                        if (component is com.ant.code.coderplugin.ui.IssueListPanel) {
                            component.loadIssues()
                        }
                    }
                }
            }
        } catch (e: Exception) {
            // 记录异常，但不中断操作
            LOG.warn("刷新UI时出错", e)
        }
    }
    
    /**
     * 获取登录错误信息
     */
    fun getLoginError(): String? {
        return loginError
    }
    
    companion object {
        fun getInstance(project: Project): AuthService = project.service<AuthService>()
    }
} 