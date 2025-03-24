package com.ant.code.coderplugin.ui

import com.ant.code.coderplugin.model.IssueListItem
import com.ant.code.coderplugin.service.IssueService
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.ComboBox
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.JBUI
import java.awt.BorderLayout
import java.awt.Dimension
import java.awt.GridBagConstraints
import java.awt.GridBagLayout
import javax.swing.*

class IssueStatusDialog(
    private val project: Project,
    private val issue: IssueListItem
) : DialogWrapper(project) {
    private val statusComboBox = ComboBox<StatusItem>()
    private val commentField = JBTextField()
    private val issueService = IssueService.getInstance(project)
    
    // 状态映射
    private val statusMap = mapOf(
        "open" to "待处理",
        "in_progress" to "处理中",
        "resolved" to "已解决",
        "verified" to "已验证", 
        "closed" to "已关闭",
        "reopened" to "重新打开",
        "rejected" to "已拒绝"
    )
    
    init {
        title = "修改问题状态：#${issue.id} ${issue.title}"
        init()
        
        // 添加可选状态
        addStatusOptions()
    }
    
    private fun addStatusOptions() {
        // 根据当前状态确定可选的新状态
        when (issue.status) {
            "open" -> {
                statusComboBox.addItem(StatusItem("in_progress", "处理中"))
                statusComboBox.addItem(StatusItem("closed", "已关闭"))
                statusComboBox.addItem(StatusItem("rejected", "已拒绝"))
            }
            "in_progress" -> {
                statusComboBox.addItem(StatusItem("resolved", "已解决"))
                statusComboBox.addItem(StatusItem("closed", "已关闭"))
                statusComboBox.addItem(StatusItem("rejected", "已拒绝"))
            }
            "resolved" -> {
                statusComboBox.addItem(StatusItem("verified", "已验证"))
                statusComboBox.addItem(StatusItem("in_progress", "重新处理"))
                statusComboBox.addItem(StatusItem("rejected", "已拒绝"))
            }
            "verified" -> {
                statusComboBox.addItem(StatusItem("closed", "已关闭"))
                statusComboBox.addItem(StatusItem("in_progress", "重新处理"))
                statusComboBox.addItem(StatusItem("rejected", "已拒绝"))
            }
            "closed" -> {
                statusComboBox.addItem(StatusItem("reopened", "重新打开"))
            }
            "reopened" -> {
                statusComboBox.addItem(StatusItem("in_progress", "处理中"))
                statusComboBox.addItem(StatusItem("rejected", "已拒绝"))
            }
            "rejected" -> {
                statusComboBox.addItem(StatusItem("reopened", "重新打开"))
            }
            else -> {
                statusComboBox.addItem(StatusItem("open", "待处理"))
                statusComboBox.addItem(StatusItem("in_progress", "处理中"))
                statusComboBox.addItem(StatusItem("resolved", "已解决"))
                statusComboBox.addItem(StatusItem("verified", "已验证"))
                statusComboBox.addItem(StatusItem("closed", "已关闭"))
                statusComboBox.addItem(StatusItem("reopened", "重新打开"))
                statusComboBox.addItem(StatusItem("rejected", "已拒绝"))
            }
        }
    }
    
    override fun createCenterPanel(): JComponent {
        val panel = JPanel(GridBagLayout())
        panel.preferredSize = Dimension(400, 200)
        panel.border = JBUI.Borders.empty(10)
        
        val gbc = GridBagConstraints()
        gbc.fill = GridBagConstraints.HORIZONTAL
        gbc.insets = JBUI.insets(5)
        
        // 问题信息
        gbc.gridx = 0
        gbc.gridy = 0
        gbc.gridwidth = 2
        panel.add(JBLabel("问题：#${issue.id} ${issue.title}"), gbc)
        
        // 当前状态
        gbc.gridx = 0
        gbc.gridy = 1
        gbc.gridwidth = 1
        panel.add(JBLabel("当前状态："), gbc)
        
        gbc.gridx = 1
        panel.add(JBLabel(statusMap[issue.status] ?: issue.status), gbc)
        
        // 新状态标签
        gbc.gridx = 0
        gbc.gridy = 2
        panel.add(JBLabel("新状态："), gbc)
        
        // 新状态下拉框
        gbc.gridx = 1
        panel.add(statusComboBox, gbc)
        
        // 备注标签
        gbc.gridx = 0
        gbc.gridy = 3
        panel.add(JBLabel("备注："), gbc)
        
        // 备注输入框
        gbc.gridx = 1
        panel.add(commentField, gbc)
        
        return panel
    }
    
    override fun doOKAction() {
        val selectedStatus = (statusComboBox.selectedItem as? StatusItem)?.value
        
        if (selectedStatus == null) {
            JOptionPane.showMessageDialog(
                contentPanel,
                "请选择新状态！",
                "错误",
                JOptionPane.ERROR_MESSAGE
            )
            return
        }
        
        val success = issueService.updateIssueStatus(
            issueId = issue.id,
            status = selectedStatus,
            comment = commentField.text.takeIf { it.isNotBlank() }
        )
        
        if (success) {
            // 记录日志，确保状态更新成功
            println("[INFO] 问题状态更新成功：ID=${issue.id}, 新状态=${selectedStatus}, 中文状态=${statusMap[selectedStatus] ?: selectedStatus}")
            
            // 关闭对话框
            super.doOKAction()
        } else {
            JOptionPane.showMessageDialog(
                contentPanel,
                "更新状态失败，请稍后重试！",
                "错误",
                JOptionPane.ERROR_MESSAGE
            )
        }
    }
    
    // 状态项，用于ComboBox
    data class StatusItem(val value: String, val label: String) {
        override fun toString(): String = label
    }
} 