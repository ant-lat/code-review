package com.ant.code.coderplugin.settings

import com.intellij.openapi.options.Configurable
import com.intellij.openapi.options.ConfigurationException
import javax.swing.JComponent
import javax.swing.JPanel
import javax.swing.JTextField
import javax.swing.JLabel
import javax.swing.JButton
import java.awt.GridBagLayout
import java.awt.GridBagConstraints
import java.awt.Insets
import java.awt.FlowLayout
import javax.swing.BorderFactory
import com.ant.code.coderplugin.settings.AppSettingsState

/**
 * 代码检视平台设置界面
 */
class CodeReviewConfigurable : Configurable {
    private var settingsPanel: JPanel? = null
    private var apiUrlField: JTextField? = null
    private var serverUrlField: JTextField? = null // 新增服务器URL字段
    private var settings: CodeReviewSettings = CodeReviewSettings.getInstance()
    private var appSettings: AppSettingsState = AppSettingsState.getInstance()

    override fun getDisplayName(): String {
        return "代码检视平台设置"
    }

    override fun getHelpTopic(): String? {
        return null
    }

    override fun createComponent(): JComponent {
        if (settingsPanel == null) {
            settingsPanel = JPanel(GridBagLayout())
            val constraints = GridBagConstraints()
            constraints.fill = GridBagConstraints.HORIZONTAL
            constraints.anchor = GridBagConstraints.WEST
            constraints.insets = Insets(5, 5, 5, 5)
            constraints.weightx = 0.0
            constraints.gridx = 0
            constraints.gridy = 0

            // 添加分组标题
            val serverGroupPanel = JPanel(GridBagLayout())
            serverGroupPanel.border = BorderFactory.createTitledBorder("服务器设置")
            
            val serverConstraints = GridBagConstraints()
            serverConstraints.fill = GridBagConstraints.HORIZONTAL
            serverConstraints.anchor = GridBagConstraints.WEST
            serverConstraints.insets = Insets(5, 5, 5, 5)
            serverConstraints.weightx = 0.0
            serverConstraints.gridx = 0
            serverConstraints.gridy = 0
            
            // 服务器URL设置
            serverGroupPanel.add(JLabel("服务器地址:"), serverConstraints)
            serverConstraints.gridx = 1
            serverConstraints.weightx = 1.0
            serverUrlField = JTextField(appSettings.getApiUrl(), 30)
            serverGroupPanel.add(serverUrlField, serverConstraints)
            
            serverConstraints.gridx = 0
            serverConstraints.gridy = 1
            serverConstraints.weightx = 0.0
            serverGroupPanel.add(JLabel("说明: 格式为 http://hostname:port/api/v1"), serverConstraints)
            
            // 添加服务器设置面板到主面板
            constraints.gridwidth = 2
            constraints.weightx = 1.0
            settingsPanel!!.add(serverGroupPanel, constraints)
            
            // 项目设置组
            constraints.gridy = 1
            val projectGroupPanel = JPanel(GridBagLayout())
            projectGroupPanel.border = BorderFactory.createTitledBorder("项目设置")
            
            val projectConstraints = GridBagConstraints()
            projectConstraints.fill = GridBagConstraints.HORIZONTAL
            projectConstraints.anchor = GridBagConstraints.WEST
            projectConstraints.insets = Insets(5, 5, 5, 5)
            
            // 旧的项目URL设置移到这里
            projectConstraints.gridx = 0
            projectConstraints.gridy = 0
            projectConstraints.weightx = 0.0
            projectGroupPanel.add(JLabel("项目URL:"), projectConstraints)
            
            projectConstraints.gridx = 1
            projectConstraints.weightx = 1.0
            apiUrlField = JTextField(settings.apiUrl, 30)
            projectGroupPanel.add(apiUrlField, projectConstraints)
            
            settingsPanel!!.add(projectGroupPanel, constraints)
        }
        return settingsPanel!!
    }

    override fun isModified(): Boolean {
        return apiUrlField?.text != settings.apiUrl || 
               serverUrlField?.text != appSettings.getApiUrl()
    }

    @Throws(ConfigurationException::class)
    override fun apply() {
        // 验证和保存项目URL
        val url = apiUrlField?.text ?: ""
        if (url.isBlank()) {
            throw ConfigurationException("项目URL不能为空")
        }
        
        // 验证和保存服务器URL
        val serverUrl = serverUrlField?.text ?: ""
        if (serverUrl.isBlank()) {
            throw ConfigurationException("服务器地址不能为空")
        }
        
        if (!serverUrl.startsWith("http://") && !serverUrl.startsWith("https://")) {
            throw ConfigurationException("服务器地址必须以http://或https://开头")
        }
        
        // 保存设置
        settings.apiUrl = url
        appSettings.setApiUrl(serverUrl)
    }

    override fun reset() {
        apiUrlField?.text = settings.apiUrl
        serverUrlField?.text = appSettings.getApiUrl()
    }

    override fun disposeUIResources() {
        settingsPanel = null
        apiUrlField = null
        serverUrlField = null
    }
} 