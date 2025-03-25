package com.ant.code.coderplugin.ui

import com.ant.code.coderplugin.service.AuthService
import com.ant.code.coderplugin.settings.AppSettingsState
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.openapi.ui.ValidationInfo
import com.intellij.ui.components.JBCheckBox
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBPasswordField
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.JBUI
import java.awt.BorderLayout
import java.awt.FlowLayout
import java.awt.Font
import java.awt.GridBagConstraints
import java.awt.GridBagLayout
import java.awt.event.ActionListener
import javax.swing.*
import javax.swing.event.DocumentEvent
import javax.swing.event.DocumentListener
import java.awt.Cursor
import java.awt.event.MouseAdapter
import java.awt.event.MouseEvent

/**
 * 登录对话框
 */
class LoginDialog(private val project: Project) : DialogWrapper(project) {

    private val userField = JBTextField(20)
    private val passwordField = JBPasswordField()
    private val rememberMeCheckBox = JBCheckBox("记住用户名和密码")
    private val autoLoginCheckBox = JBCheckBox("自动登录")
    private val loadingPanel = JPanel(BorderLayout())
    private val loadingLabel = JBLabel("正在登录，请稍候...", SwingConstants.CENTER)
    private val authService = AuthService.getInstance(project)
    private var isLoggedIn = false
    private val statusLabel = JLabel()
    
    init {
        title = "登录 Code-R"
        init()
        
        // 尝试自动登录
        val autoLoginResult = authService.tryAutoLogin()
        if (autoLoginResult) {
            isLoggedIn = true
            close(OK_EXIT_CODE)
        }
    }
    
    override fun createCenterPanel(): JComponent {
        val panel = JPanel(BorderLayout())
        panel.border = JBUI.Borders.empty(10)
        
        // 标题面板
        val titlePanel = JPanel(FlowLayout(FlowLayout.CENTER))
//        val titleLabel = JLabel("登录到Code Review")
//        titleLabel.font = titleLabel.font.deriveFont(Font.BOLD, 16f)
//        titlePanel.add(titleLabel)
        
        panel.add(titlePanel, BorderLayout.NORTH)
        
        val formPanel = JPanel(GridBagLayout())
        val constraints = GridBagConstraints()
        constraints.fill = GridBagConstraints.HORIZONTAL
        constraints.weightx = 1.0
        constraints.insets = JBUI.insets(5)
        
        // 用户名
        constraints.gridx = 0
        constraints.gridy = 0
        formPanel.add(JBLabel("用户ID:"), constraints)
        
        constraints.gridx = 1
        userField.toolTipText = "请输入用户ID"
        formPanel.add(userField, constraints)
        
        // 密码
        constraints.gridx = 0
        constraints.gridy = 1
        formPanel.add(JBLabel("密码:"), constraints)
        
        constraints.gridx = 1
        formPanel.add(passwordField, constraints)
        
        // 记住我
        constraints.gridx = 0
        constraints.gridy = 2
        constraints.gridwidth = 1
        formPanel.add(rememberMeCheckBox, constraints)
        
        // 自动登录
        constraints.gridx = 1
        constraints.gridy = 2
        formPanel.add(autoLoginCheckBox, constraints)
        
        // 添加记住密码和自动登录的联动
        rememberMeCheckBox.addActionListener {
            if (!rememberMeCheckBox.isSelected) {
                autoLoginCheckBox.isSelected = false
            }
        }
        
        autoLoginCheckBox.addActionListener {
            if (autoLoginCheckBox.isSelected) {
                rememberMeCheckBox.isSelected = true
            }
        }
        
        // 配置服务器链接
        constraints.gridx = 0
        constraints.gridy = 3
        constraints.gridwidth = 2
        val serverPanel = JPanel(FlowLayout(FlowLayout.LEFT))
        val configServerLink = JLabel("<html><a href=''>配置服务器</a></html>")
        configServerLink.cursor = Cursor.getPredefinedCursor(Cursor.HAND_CURSOR)
        configServerLink.addMouseListener(object : MouseAdapter() {
            override fun mouseClicked(e: MouseEvent) {
                openServerConfig()
            }
        })
        serverPanel.add(configServerLink)

        // 显示当前服务器地址
        val appSettings = AppSettingsState.getInstance()
        val serverInfo = JLabel("当前服务器: ${appSettings.getApiUrl()}")
        serverPanel.add(serverInfo)
        
        formPanel.add(serverPanel, constraints)
        
        // 添加登录状态面板
        constraints.gridx = 0
        constraints.gridy = 4
        constraints.gridwidth = 2
        constraints.weightx = 1.0
        
        val statusPanel = JPanel(BorderLayout())
        statusPanel.add(statusLabel, BorderLayout.CENTER)
        
        // 如果已登录，显示退出登录按钮
        val logoutButton = JButton("退出登录")
        logoutButton.addActionListener {
            handleLogout()
        }
        
        // 根据登录状态显示或隐藏退出按钮
        val currentUser = authService.getCurrentUser()
        if (currentUser != null) {
            statusPanel.add(logoutButton, BorderLayout.EAST)
            statusLabel.text = "当前登录用户: ${currentUser.username}"
        } else {
            statusLabel.text = "请登录"
        }
        
        formPanel.add(statusPanel, constraints)
        
        panel.add(formPanel, BorderLayout.CENTER)
        
        // 加载保存的凭据
        val savedCredentials = authService.getSavedCredentials()
        if (savedCredentials != null) {
            userField.text = savedCredentials.first
            passwordField.text = savedCredentials.second
            rememberMeCheckBox.isSelected = true
            
            // 检查是否设置了自动登录
            val appSettings = AppSettingsState.getInstance()
            if (appSettings.autoLogin) {
                autoLoginCheckBox.isSelected = true
            }
        } else {
            // 检查是否有缓存的用户ID
            val appSettings = AppSettingsState.getInstance()
            val cachedUserId = appSettings.savedUsername
            if (cachedUserId.isNotBlank()) {
                userField.text = cachedUserId
            }
        }
        
        return panel
    }

    override fun doOKAction() {
        // 获取输入的用户ID和密码
        val userId = userField.text.trim()
        val password = String(passwordField.password)
        val rememberMe = rememberMeCheckBox.isSelected
        val autoLogin = autoLoginCheckBox.isSelected
        
        if (userId.isEmpty() || password.isEmpty()) {
            com.intellij.openapi.ui.Messages.showErrorDialog(
                contentPanel,
                "用户ID和密码不能为空",
                "登录错误"
            )
            return
        }
        
        // 禁用登录按钮并显示加载中...
        val okButton = getButton(okAction)
        val originalText = okButton?.text ?: "确定"
        okButton?.isEnabled = false
        okButton?.text = "登录中..."
        
        // 在后台线程中执行登录操作
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val authService = AuthService.getInstance(project)
                val success = authService.login(userId, password, rememberMe)
                
                // 在EDT线程中更新UI
                SwingUtilities.invokeLater {
                    try {
                        if (success) {
                            // 登录成功，尝试加载项目列表
                            println("[DEBUG] 登录成功，自动加载项目列表")
                            
                            // 保存自动登录设置
                            val appSettings = AppSettingsState.getInstance()
                            appSettings.savedUsername = userId  // 保存用户ID而不是用户名
                            appSettings.autoLogin = autoLogin
                            
                            // 关闭对话框
                            close(OK_EXIT_CODE)
                        } else {
                            // 登录失败，显示错误消息
                            com.intellij.openapi.ui.Messages.showErrorDialog(
                                contentPanel,
                                "登录失败: ${authService.getLoginError() ?: "用户名或密码错误"}",
                                "登录错误"
                            )
                            
                            // 恢复按钮状态
                            okButton?.isEnabled = true
                            okButton?.text = originalText
                        }
                    } catch (e: Exception) {
                        com.intellij.openapi.diagnostic.Logger.getInstance(LoginDialog::class.java)
                            .error("登录后更新UI时出错", e)
                        
                        // 恢复按钮状态
                        okButton?.isEnabled = true
                        okButton?.text = originalText
                    }
                }
            } catch (e: Exception) {
                com.intellij.openapi.diagnostic.Logger.getInstance(LoginDialog::class.java)
                    .error("执行登录操作时出错", e)
                
                // 在EDT线程中更新UI
                SwingUtilities.invokeLater {
                    // 显示错误消息
                    com.intellij.openapi.ui.Messages.showErrorDialog(
                        contentPanel,
                        "登录过程中发生错误: ${e.message}",
                        "登录错误"
                    )
                    
                    // 恢复按钮状态
                    okButton?.isEnabled = true
                    okButton?.text = originalText
                }
            }
        }
    }

    override fun doValidate(): ValidationInfo? {
        // 未登录状态验证用户名和密码
        if (!isLoggedIn) {
            if (userField.text.isBlank()) {
                return ValidationInfo("请输入用户ID", userField)
            }
            
            if (passwordField.password.isEmpty()) {
                return ValidationInfo("请输入密码", passwordField)
            }
        }
        
        return null
    }

    /**
     * 处理退出登录
     */
    private fun handleLogout() {
        // 更新状态文本
        statusLabel.text = "正在退出登录..."
        
        // 禁用退出登录按钮
        val logoutButton = findLogoutButton()
        logoutButton?.isEnabled = false
        
        // 执行退出登录操作（在后台线程执行，避免阻塞UI）
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val authService = AuthService.getInstance(project)
                authService.logout()
                
                // 切换回EDT线程更新UI
                SwingUtilities.invokeLater {
                    // 更新UI状态
                    statusLabel.text = "已成功退出登录"
                    userField.text = ""
                    passwordField.text = ""
                    rememberMeCheckBox.isSelected = false
                    autoLoginCheckBox.isSelected = false
                    
                    // 在短暂延迟后关闭对话框并重新打开
                    Timer(1500, ActionListener {
                        try {
                            close(DialogWrapper.OK_EXIT_CODE)
                            // 稍微延迟一下重新打开
                            Timer(200, ActionListener {
                                SwingUtilities.invokeLater {
                                    try {
                                        val newDialog = LoginDialog(project)
                                        newDialog.show()
                                    } catch (e: Exception) {
                                        println("[ERROR] 重新打开登录对话框失败: ${e.message}")
                                        e.printStackTrace()
                                    }
                                } 
                            }).apply {
                                isRepeats = false
                                start()
                            }
                        } catch (e: Exception) {
                            println("[ERROR] 关闭对话框失败: ${e.message}")
                            e.printStackTrace()
                        }
                    }).apply {
                        isRepeats = false
                        start()
                    }
                }
            } catch (e: Exception) {
                // 切换回EDT线程更新UI
                SwingUtilities.invokeLater {
                    statusLabel.text = "退出登录失败: ${e.message}"
                    logoutButton?.isEnabled = true
                }
            }
        }
    }
    
    /**
     * 安全地查找退出登录按钮
     */
    private fun findLogoutButton(): JButton? {
        try {
            // 查找退出登录按钮
            for (comp in statusLabel.parent.components) {
                if (comp is JButton && comp.text == "退出登录") {
                    return comp
                }
            }
        } catch (e: Exception) {
            println("[ERROR] 查找退出登录按钮失败: ${e.message}")
        }
        return null
    }

    /**
     * 打开服务器配置
     */
    private fun openServerConfig() {
        // 关闭当前对话框
        close(CANCEL_EXIT_CODE)
        
        // 延迟打开设置对话框，避免UI冲突
        Timer(300, ActionListener {
            SwingUtilities.invokeLater {
                // 打开设置对话框
                com.intellij.openapi.options.ShowSettingsUtil.getInstance().showSettingsDialog(
                    project,
                    "com.ant.code.coderplugin.settings.CodeReviewConfigurable"
                )
            }
        }).apply {
            isRepeats = false
            start()
        }
    }
} 