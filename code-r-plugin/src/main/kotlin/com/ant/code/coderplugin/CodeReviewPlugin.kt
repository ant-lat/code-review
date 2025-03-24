package com.ant.code.coderplugin

import com.ant.code.coderplugin.listeners.LoginStatusListener
import com.ant.code.coderplugin.service.AuthService
import com.ant.code.coderplugin.settings.AppSettingsState
import com.intellij.ide.AppLifecycleListener
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.project.Project
import com.intellij.openapi.project.ProjectManager
import com.intellij.openapi.startup.StartupActivity

/**
 * 插件入口点
 */
class CodeReviewPlugin : StartupActivity {
    companion object {
        private val LOG = Logger.getInstance(CodeReviewPlugin::class.java)
    }

    override fun runActivity(project: Project) {
        try {
            LOG.info("Code Review 插件初始化...")
            
            // 注册消息总线主题
            val messageBus = ApplicationManager.getApplication().messageBus
            messageBus.simpleConnect().subscribe(LoginStatusListener.TOPIC, object : LoginStatusListener {
                override fun onLogin() {
                    LOG.info("用户已登录")
                }
                
                override fun onLogout() {
                    LOG.info("用户已登出")
                }
            })
            
            // 其他初始化代码
            
            LOG.info("Code Review 插件初始化完成")
        } catch (e: Exception) {
            LOG.error("Code Review 插件初始化失败", e)
        }
    }
} 