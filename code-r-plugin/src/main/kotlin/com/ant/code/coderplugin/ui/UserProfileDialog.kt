package com.ant.code.coderplugin.ui

import com.ant.code.coderplugin.model.UserInfo
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.ui.components.JBLabel
import com.intellij.util.ui.JBUI
import java.awt.Dimension
import java.awt.GridBagConstraints
import java.awt.GridBagLayout
import javax.swing.ImageIcon
import javax.swing.JComponent
import javax.swing.JPanel

/**
 * 用户详细信息对话框
 */
class UserProfileDialog(
    private val project: Project,
    private val userInfo: UserInfo
) : DialogWrapper(project) {
    
    init {
        title = "用户详细信息"
        init()
    }
    
    override fun createCenterPanel(): JComponent {
        val panel = JPanel(GridBagLayout())
        panel.preferredSize = Dimension(400, 300)
        panel.border = JBUI.Borders.empty(10)
        
        val gbc = GridBagConstraints()
        gbc.fill = GridBagConstraints.HORIZONTAL
        gbc.insets = JBUI.insets(5)
        
        // 用户头像
        val avatarIcon = ImageIcon(javaClass.getResource("/icons/avatar_icon.svg"))
        val resizedIcon = avatarIcon.getImage().getScaledInstance(64, 64, java.awt.Image.SCALE_SMOOTH)
        val avatarLabel = JBLabel(ImageIcon(resizedIcon))
        
        gbc.gridx = 0
        gbc.gridy = 0
        gbc.gridwidth = 2
        gbc.anchor = GridBagConstraints.CENTER
        panel.add(avatarLabel, gbc)
        
        // 用户名
        gbc.gridx = 0
        gbc.gridy = 1
        gbc.gridwidth = 2
        gbc.anchor = GridBagConstraints.CENTER
        panel.add(JBLabel("<html><b>${userInfo.username}</b></html>"), gbc)
        
        // 用户ID
        addField(panel, gbc, 2, "用户ID:", userInfo.userId)
        
        // 邮箱
        addField(panel, gbc, 3, "邮箱:", userInfo.email ?: "无")
        
        // 电话
        addField(panel, gbc, 4, "电话:", userInfo.phone ?: "无")
        
        // 状态
        addField(panel, gbc, 5, "状态:", if (userInfo.isActive) "激活" else "未激活")
        
        // 创建时间
        addField(panel, gbc, 6, "创建时间:", userInfo.createdAt)
        
        // 角色
        val roles = userInfo.roles.joinToString(", ") { it.name }
        addField(panel, gbc, 7, "角色:", roles)
        
        return panel
    }
    
    private fun addField(panel: JPanel, gbc: GridBagConstraints, row: Int, labelText: String, valueText: String) {
        gbc.gridx = 0
        gbc.gridy = row
        gbc.gridwidth = 1
        gbc.weightx = 0.3
        panel.add(JBLabel(labelText), gbc)
        
        gbc.gridx = 1
        gbc.weightx = 0.7
        panel.add(JBLabel(valueText), gbc)
    }
} 