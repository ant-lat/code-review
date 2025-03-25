package com.ant.code.coderplugin.ui

import com.ant.code.coderplugin.api.ApiModels
import com.ant.code.coderplugin.service.IssueService
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.ComboBox
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.openapi.ui.ValidationInfo
import com.intellij.openapi.ui.Messages
import com.intellij.ui.ColoredListCellRenderer
import com.intellij.ui.components.JBLabel
import com.intellij.ui.components.JBScrollPane
import com.intellij.ui.components.JBTextArea
import com.intellij.ui.components.JBTextField
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import java.awt.BorderLayout
import java.awt.GridBagConstraints
import java.awt.GridBagLayout
import javax.swing.*
import javax.swing.event.DocumentEvent
import javax.swing.event.DocumentListener
import java.awt.Font
import com.intellij.ui.JBColor
import java.awt.Dimension
import java.awt.Component

/**
 * 创建问题对话框
 */
class CreateIssueDialog(
    private val project: Project,
    private val codeSelection: ApiModels.CodeSelectionInfo? = null,
    private val existingIssue: ApiModels.IssueListItem? = null,
    private val isEditMode: Boolean = false  // 增加编辑模式参数
) : DialogWrapper(project) {

    private val issueService = IssueService.getInstance(project)
    private val titleField = JBTextField(40)
    private val descriptionArea = JBTextArea(6, 40)
    private val priorityCombo = ComboBox<String>()
    private val issueTypeCombo = ComboBox<String>()
    private val severityCombo = ComboBox<String>()
    private val statusCombo = ComboBox<String>()
    private val projectCombo = ComboBox<ApiModels.ProjectInfo>()
    private val assigneeCombo = ComboBox<ApiModels.UserInfo>()
    private val codeInfoPanel = JPanel(BorderLayout())
    private val titleLengthLabel = JBLabel()
    private var selectedProject: ApiModels.ProjectInfo? = null
    private var selectedAssignee: ApiModels.UserInfo? = null
    private val isViewMode: Boolean = existingIssue != null && !isEditMode  // 根据已有问题和编辑模式判断是否为查看模式
    private var projectsLoaded = false
    
    // 增加更多显示字段
    private val creatorField = JBTextField()
    private val createdAtField = JBTextField()
    private val updatedAtField = JBTextField()
    private val resolvedAtField = JBTextField()
    private val closedAtField = JBTextField()
    private val resolutionTimeField = JBTextField()
    
    private val priorityMap = mapOf(
        "低" to "low",
        "中" to "medium", 
        "高" to "high",
        "紧急" to "critical"
    )
    
    private val reversePriorityMap = mapOf(
        "low" to "低",
        "medium" to "中", 
        "high" to "高",
        "critical" to "紧急"
    )
    
    private val issueTypeMap = mapOf(
        "缺陷" to "bug",
        "功能" to "feature",
        "改进" to "improvement",
        "任务" to "task",
        "代码审查" to "code_review",
        "安全问题" to "security"
    )
    
    private val reverseIssueTypeMap = mapOf(
        "bug" to "缺陷",
        "feature" to "功能",
        "improvement" to "改进",
        "task" to "任务",
        "code_review" to "代码审查",
        "security" to "安全问题"
    )
    
    private val statusMap = mapOf(
        "待处理" to "open",
        "进行中" to "in_progress",
        "已解决" to "resolved",
        "已验证" to "verified",
        "已关闭" to "closed",
        "重新打开" to "reopened",
        "已拒绝" to "rejected"
    )
    
    private val reverseStatusMap = mapOf(
        "open" to "待处理",
        "in_progress" to "进行中",
        "resolved" to "已解决",
        "verified" to "已验证",
        "closed" to "已关闭",
        "reopened" to "重新打开",
        "rejected" to "已拒绝"
    )
    
    private val severityMap = mapOf(
        "低" to "low",
        "中" to "medium", 
        "高" to "high",
        "紧急" to "critical"
    )
    
    private val reverseSeverityMap = mapOf(
        "low" to "低",
        "medium" to "中", 
        "high" to "高",
        "critical" to "紧急"
    )
    
    init {
        title = if (isViewMode) "问题详情 - #${existingIssue?.id} ${existingIssue?.title}" 
                else if (isEditMode) "修改问题 - #${existingIssue?.id} ${existingIssue?.title}" 
                else "创建问题"
        
        // 如果是查看模式，设置对话框为禁止修改状态
        // 如果是编辑模式，则允许编辑字段
        if (isViewMode) {
            setOKButtonText("")
            setCancelButtonText("关闭")
        } else if (isEditMode) {
            setOKButtonText("更新")
            setCancelButtonText("取消")
        } else {
            setOKButtonText("创建")
            setCancelButtonText("取消")
        }
        
        // 如果存在已有问题，预加载其所属项目的指派人列表
        if (existingIssue != null && existingIssue.projectId > 0) {
            com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
                try {
                    issueService.preloadAssignees(existingIssue.projectId)
                } catch (e: Exception) {
                    println("[ERROR] 预加载指派人失败: ${e.message}")
                }
            }
        }
        
        init()
        setSize(700, 700) // 增加高度
        
        // 设置项目下拉框的渲染器，只显示项目名称
        projectCombo.renderer = object : DefaultListCellRenderer() {
            override fun getListCellRendererComponent(
                list: JList<*>?,
                value: Any?,
                index: Int,
                isSelected: Boolean,
                cellHasFocus: Boolean
            ): Component {
                val component = super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus)
                if (value is ApiModels.ProjectInfo) {
                    text = value.name
                } else if (value == null) {
                    text = "请选择项目"
                }
                return component
            }
        }
        
        // 默认禁用确定按钮，直到选择了项目
        if (!isViewMode && existingIssue == null) {
            setOKActionEnabled(false)
        }
        
        // 如果是查看模式或编辑模式，加载现有问题数据
        if (existingIssue != null) {
            loadExistingIssue()
            
            if (isViewMode) {
                setOKButtonText("关闭")
            } else if (isEditMode) {
                setOKButtonText("保存")
            }
        } else {
            setOKButtonText("创建")
        }
    }
    
    private fun loadExistingIssue() {
        existingIssue?.let { issue ->
            // 设置标题
            titleField.text = issue.title
            titleField.isEditable = !isViewMode // 编辑模式下允许修改标题
            
            descriptionArea.text = issue.description ?: ""
            descriptionArea.isEditable = !isViewMode // 编辑模式下允许修改描述
            
            // 设置创建者、时间等信息
            creatorField.text = issue.creatorName
            creatorField.isEditable = false
            
            createdAtField.text = issue.createdAt
            createdAtField.isEditable = false
            
            updatedAtField.text = issue.updatedAt ?: "未更新"
            updatedAtField.isEditable = false
            
            resolvedAtField.text = issue.resolvedAt ?: "未解决"
            resolvedAtField.isEditable = false
            
            closedAtField.text = issue.closedAt ?: "未关闭"
            closedAtField.isEditable = false
            
            if (issue.resolutionTime != null) {
                resolutionTimeField.text = "${issue.resolutionTime} 小时"
            } else {
                resolutionTimeField.text = "未计算"
            }
            resolutionTimeField.isEditable = false
            
            // 设置优先级
            val priorityDisplay = reversePriorityMap[issue.priority] ?: issue.priority
            priorityCombo.removeAllItems()
            priorityMap.keys.forEach { priorityCombo.addItem(it) }
            for (i in 0 until priorityCombo.itemCount) {
                if (priorityCombo.getItemAt(i) == priorityDisplay) {
                    priorityCombo.selectedIndex = i
                    break
                }
            }
            priorityCombo.isEnabled = !isViewMode // 编辑模式下允许修改优先级
            
            // 设置问题类型
            val typeDisplay = reverseIssueTypeMap[issue.issueType] ?: issue.issueType
            issueTypeCombo.removeAllItems()
            issueTypeMap.keys.forEach { issueTypeCombo.addItem(it) }
            for (i in 0 until issueTypeCombo.itemCount) {
                if (issueTypeCombo.getItemAt(i) == typeDisplay) {
                    issueTypeCombo.selectedIndex = i
                    break
                }
            }
            issueTypeCombo.isEnabled = !isViewMode // 编辑模式下允许修改问题类型
            
            // 设置状态 - 编辑模式可修改
            val statusDisplay = reverseStatusMap[issue.status] ?: issue.status
            statusCombo.removeAllItems()
            statusMap.keys.forEach { statusCombo.addItem(it) }
            for (i in 0 until statusCombo.itemCount) {
                if (statusCombo.getItemAt(i) == statusDisplay) {
                    statusCombo.selectedIndex = i
                    break
                }
            }
            statusCombo.isEnabled = !isViewMode // 编辑模式可以修改状态
            
            // 设置严重程度（如果有）
            severityCombo.removeAllItems()
            severityMap.keys.forEach { severityCombo.addItem(it) }
            if (issue.severity != null) {
                val severityDisplay = reverseSeverityMap[issue.severity] ?: issue.severity
                for (i in 0 until severityCombo.itemCount) {
                    if (severityCombo.getItemAt(i) == severityDisplay) {
                        severityCombo.selectedIndex = i
                        break
                    }
                }
            }
            severityCombo.isEnabled = !isViewMode // 编辑模式下允许修改严重程度
            
            // 设置项目
            projectCombo.removeAllItems()
            val projectInfo = ApiModels.ProjectInfo(
                id = issue.projectId,
                name = issue.projectName,
                description = "",
                createdAt = ""
            )
            projectCombo.addItem(projectInfo)
            projectCombo.isEnabled = !isViewMode // 编辑模式下允许修改项目
            selectedProject = projectInfo
            
            // 加载指派人（如果是编辑模式可以修改指派人）
            if (isViewMode) {
                // 在查看模式下，不需要加载指派人列表，只显示当前指派人
                assigneeCombo.removeAllItems()
                if (issue.assigneeId != null && issue.assigneeName != null) {
                    val assignee = ApiModels.UserInfo(
                        id = issue.assigneeId,
                        username = issue.assigneeName,
                        email = null,
                        roles = null
                    )
                    assigneeCombo.addItem(assignee)
                } else {
                    assigneeCombo.addItem(null) // 不指派
                }
                assigneeCombo.isEnabled = false
            } else {
                // 编辑模式，需要加载指派人列表
                loadProjectMembers(issue.projectId)
            }
        }
    }
    
    override fun createCenterPanel(): JComponent {
        val panel = JPanel(BorderLayout())
        panel.border = JBUI.Borders.empty(10)
        
        val formPanel = JPanel(GridBagLayout())
        formPanel.background = UIUtil.getPanelBackground()
        
        val constraints = GridBagConstraints()
        constraints.fill = GridBagConstraints.HORIZONTAL
        constraints.weightx = 1.0
        constraints.insets = JBUI.insets(8)
        
        var gridy = 0
        
        // 标题
        constraints.gridx = 0
        constraints.gridy = gridy
        constraints.gridwidth = 1
        val titleLabel = JBLabel("标题:")
        titleLabel.font = titleLabel.font.deriveFont(Font.BOLD)
        formPanel.add(titleLabel, constraints)
        
        constraints.gridx = 1
        constraints.gridwidth = 2
        val titlePanel = JPanel(BorderLayout())
        titlePanel.border = BorderFactory.createCompoundBorder(
            BorderFactory.createLineBorder(JBColor.border()),
            BorderFactory.createEmptyBorder(5, 8, 5, 8)
        )
        titlePanel.background = UIUtil.getTextFieldBackground()
        titleField.border = BorderFactory.createEmptyBorder()
        titleField.isEditable = !isViewMode
        titlePanel.add(titleField, BorderLayout.CENTER)
        titleLengthLabel.text = "0/100"
        titleLengthLabel.foreground = UIUtil.getLabelForeground()
        titlePanel.add(titleLengthLabel, BorderLayout.EAST)
        formPanel.add(titlePanel, constraints)
        gridy++
        
        // 项目
        constraints.gridx = 0
        constraints.gridy = gridy
        constraints.gridwidth = 1
        val projectLabel = JBLabel("项目:")
        projectLabel.font = projectLabel.font.deriveFont(Font.BOLD)
        formPanel.add(projectLabel, constraints)
        
        constraints.gridx = 1
        constraints.gridwidth = 2
        if (isViewMode || isEditMode) {
            val projectField = JBTextField()
            projectField.text = existingIssue?.projectName ?: ""
            projectField.isEditable = false
            projectField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            projectField.background = UIUtil.getTextFieldBackground()
            formPanel.add(projectField, constraints)
        } else {
            projectCombo.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            formPanel.add(projectCombo, constraints)
        }
        gridy++
        
        // 文件路径
        if (existingIssue?.filePath != null || codeSelection?.filePath != null) {
            constraints.gridx = 0
            constraints.gridy = gridy
            constraints.gridwidth = 1
            val filePathLabel = JBLabel("包路径:")
            filePathLabel.font = filePathLabel.font.deriveFont(Font.PLAIN)
            formPanel.add(filePathLabel, constraints)
            
            constraints.gridx = 1
            constraints.gridwidth = 2
            val filePathField = JBTextField()
            
            // 将文件路径转换为包路径格式
            val packagePath = if (existingIssue?.filePath != null) {
                getPackagePathFromFilePath(existingIssue.filePath)
            } else if (codeSelection?.filePath != null) {
                getPackagePathFromFilePath(codeSelection.filePath)
            } else ""
            
            filePathField.text = packagePath
            filePathField.isEditable = false
            filePathField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            filePathField.background = UIUtil.getTextFieldBackground()
            formPanel.add(filePathField, constraints)
            gridy++
        }
        
        // 代码行
        if (existingIssue?.lineStart != null || codeSelection?.lineStart != null) {
            constraints.gridx = 0
            constraints.gridy = gridy
            constraints.gridwidth = 1
            val lineLabel = JBLabel("代码行:")
            lineLabel.font = lineLabel.font.deriveFont(Font.PLAIN)
            formPanel.add(lineLabel, constraints)
            
            constraints.gridx = 1
            constraints.gridwidth = 2
            val lineField = JBTextField()
            val lineStart = existingIssue?.lineStart ?: codeSelection?.lineStart
            val lineEnd = existingIssue?.lineEnd ?: codeSelection?.lineEnd
            lineField.text = if (lineStart != null) {
                if (lineEnd != null && lineEnd != lineStart) 
                    "第 $lineStart - $lineEnd 行" 
                else 
                    "第 $lineStart 行"
            } else ""
            lineField.isEditable = false
            lineField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            lineField.background = UIUtil.getTextFieldBackground()
            formPanel.add(lineField, constraints)
            gridy++
        }
        
        // 创建人
        if (existingIssue != null) {
            constraints.gridx = 0
            constraints.gridy = gridy
            constraints.gridwidth = 1
            val creatorLabel = JBLabel("创建人:")
            creatorLabel.font = creatorLabel.font.deriveFont(Font.BOLD)
            formPanel.add(creatorLabel, constraints)
            
            constraints.gridx = 1
            constraints.gridwidth = 2
            val creatorField = JBTextField()
            creatorField.text = existingIssue.creatorName
            creatorField.isEditable = false
            creatorField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            creatorField.background = UIUtil.getTextFieldBackground()
            formPanel.add(creatorField, constraints)
            gridy++
        }
        
        // 指派人
        constraints.gridx = 0
        constraints.gridy = gridy
        constraints.gridwidth = 1
        val assigneeLabel = JBLabel("指派人:")
        assigneeLabel.font = assigneeLabel.font.deriveFont(Font.BOLD)
        formPanel.add(assigneeLabel, constraints)
        
        constraints.gridx = 1
        constraints.gridwidth = 2
        if (isViewMode) {
            val assigneeField = JBTextField()
            assigneeField.text = existingIssue?.assigneeName ?: "未指派"
            assigneeField.isEditable = false
            assigneeField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            assigneeField.background = UIUtil.getTextFieldBackground()
            formPanel.add(assigneeField, constraints)
        } else {
            assigneeCombo.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            formPanel.add(assigneeCombo, constraints)
        }
        gridy++
        
        // 问题类型
        constraints.gridx = 0
        constraints.gridy = gridy
        constraints.gridwidth = 1
        val typeLabel = JBLabel("问题类型:")
        typeLabel.font = typeLabel.font.deriveFont(Font.BOLD)
        formPanel.add(typeLabel, constraints)
        
        constraints.gridx = 1
        constraints.gridwidth = 2
        if (isViewMode) {
            val typeField = JBTextField()
            typeField.text = reverseIssueTypeMap[existingIssue?.issueType] ?: existingIssue?.issueType ?: ""
            typeField.isEditable = false
            typeField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            typeField.background = UIUtil.getTextFieldBackground()
            formPanel.add(typeField, constraints)
        } else {
            issueTypeCombo.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            formPanel.add(issueTypeCombo, constraints)
        }
        gridy++
        
        // 优先级
        constraints.gridx = 0
        constraints.gridy = gridy
        constraints.gridwidth = 1
        val priorityLabel = JBLabel("优先级:")
        priorityLabel.font = priorityLabel.font.deriveFont(Font.BOLD)
        formPanel.add(priorityLabel, constraints)
        
        constraints.gridx = 1
        constraints.gridwidth = 2
        if (isViewMode) {
            val priorityField = JBTextField()
            priorityField.text = reversePriorityMap[existingIssue?.priority] ?: existingIssue?.priority ?: ""
            priorityField.isEditable = false
            priorityField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            priorityField.background = UIUtil.getTextFieldBackground()
            formPanel.add(priorityField, constraints)
        } else {
            priorityCombo.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            formPanel.add(priorityCombo, constraints)
        }
        gridy++
        
        // 状态
        constraints.gridx = 0
        constraints.gridy = gridy
        constraints.gridwidth = 1
        val statusLabel = JBLabel("状态:")
        statusLabel.font = statusLabel.font.deriveFont(Font.BOLD)
        formPanel.add(statusLabel, constraints)
        
        constraints.gridx = 1
        constraints.gridwidth = 2
        if (isViewMode) {
            val statusField = JBTextField()
            statusField.text = reverseStatusMap[existingIssue?.status] ?: existingIssue?.status ?: ""
            statusField.isEditable = false
            statusField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            statusField.background = UIUtil.getTextFieldBackground()
            formPanel.add(statusField, constraints)
        } else {
            statusCombo.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            formPanel.add(statusCombo, constraints)
        }
        gridy++
        
        // 严重程度
        constraints.gridx = 0
        constraints.gridy = gridy
        constraints.gridwidth = 1
        val severityLabel = JBLabel("严重程度:")
        severityLabel.font = severityLabel.font.deriveFont(Font.BOLD)
        formPanel.add(severityLabel, constraints)
        
        constraints.gridx = 1
        constraints.gridwidth = 2
        if (isViewMode) {
            val severityField = JBTextField()
            severityField.text = if (existingIssue?.severity != null) {
                reverseSeverityMap[existingIssue.severity] ?: existingIssue.severity
            } else ""
            severityField.isEditable = false
            severityField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            severityField.background = UIUtil.getTextFieldBackground()
            formPanel.add(severityField, constraints)
        } else {
            severityCombo.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            formPanel.add(severityCombo, constraints)
        }
        gridy++
        
        // 创建时间
        if (existingIssue != null) {
            constraints.gridx = 0
            constraints.gridy = gridy
            constraints.gridwidth = 1
            val createdAtLabel = JBLabel("创建时间:")
            createdAtLabel.font = createdAtLabel.font.deriveFont(Font.PLAIN)
            formPanel.add(createdAtLabel, constraints)
            
            constraints.gridx = 1
            constraints.gridwidth = 2
            val createdAtField = JBTextField()
            createdAtField.text = existingIssue.createdAt
            createdAtField.isEditable = false
            createdAtField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            createdAtField.background = UIUtil.getTextFieldBackground()
            formPanel.add(createdAtField, constraints)
            gridy++
        }
        
        // 更新时间
        if (existingIssue?.updatedAt != null) {
            constraints.gridx = 0
            constraints.gridy = gridy
            constraints.gridwidth = 1
            val updatedAtLabel = JBLabel("更新时间:")
            updatedAtLabel.font = updatedAtLabel.font.deriveFont(Font.PLAIN)
            formPanel.add(updatedAtLabel, constraints)
            
            constraints.gridx = 1
            constraints.gridwidth = 2
            val updatedAtField = JBTextField()
            updatedAtField.text = existingIssue.updatedAt
            updatedAtField.isEditable = false
            updatedAtField.border = BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(JBColor.border()),
                BorderFactory.createEmptyBorder(5, 8, 5, 8)
            )
            updatedAtField.background = UIUtil.getTextFieldBackground()
            formPanel.add(updatedAtField, constraints)
            gridy++
        }
        
        // 描述
        constraints.gridx = 0
        constraints.gridy = gridy
        constraints.gridwidth = 1
        constraints.anchor = GridBagConstraints.NORTHWEST
        constraints.insets = JBUI.insets(12, 8, 8, 8)  // 顶部增加更多间距
        val descLabel = JBLabel("描述:")
        descLabel.font = descLabel.font.deriveFont(Font.BOLD)
        formPanel.add(descLabel, constraints)
        
        constraints.gridx = 1
        constraints.gridwidth = 2
        constraints.fill = GridBagConstraints.BOTH
        constraints.weighty = 1.0
        descriptionArea.lineWrap = true
        descriptionArea.wrapStyleWord = true
        descriptionArea.border = BorderFactory.createEmptyBorder(5, 8, 5, 8)
        descriptionArea.isEditable = !isViewMode
        descriptionArea.font = Font(Font.MONOSPACED, Font.PLAIN, 13)
        val descScrollPane = JBScrollPane(descriptionArea)
        descScrollPane.border = BorderFactory.createLineBorder(JBColor.border())
        descScrollPane.preferredSize = Dimension(400, 150)  // 设置较大的高度
        formPanel.add(descScrollPane, constraints)
        gridy++
        
        // 显示代码内容（如果有）
        if ((existingIssue?.codeContent != null && existingIssue.codeContent.isNotEmpty()) || 
            (codeSelection?.selectedCode != null && codeSelection.selectedCode.isNotEmpty())) {
            constraints.gridx = 0
            constraints.gridy = gridy
            constraints.gridwidth = 1
            constraints.weighty = 0.0
            constraints.anchor = GridBagConstraints.NORTHWEST
            constraints.insets = JBUI.insets(12, 8, 8, 8)  // 顶部增加更多间距
            val codeLabel = JBLabel("代码内容:")
            codeLabel.font = codeLabel.font.deriveFont(Font.BOLD)
            formPanel.add(codeLabel, constraints)
            
            constraints.gridx = 1
            constraints.gridwidth = 2
            constraints.weighty = 0.8
            constraints.fill = GridBagConstraints.BOTH
            
            val codeArea = JBTextArea(existingIssue?.codeContent ?: codeSelection?.selectedCode)
            codeArea.isEditable = false
            codeArea.lineWrap = true
            codeArea.wrapStyleWord = true
            codeArea.font = Font(Font.MONOSPACED, Font.PLAIN, 13)
            val codeScrollPane = JBScrollPane(codeArea)
            codeScrollPane.border = BorderFactory.createLineBorder(JBColor.border())
            codeScrollPane.preferredSize = Dimension(400, 150)  // 设置较大的高度
            formPanel.add(codeScrollPane, constraints)
            gridy++
        }
        
        // 将表单放入包含滚动面板的主面板中
        val scrollPane = JBScrollPane(formPanel)
        scrollPane.border = BorderFactory.createEmptyBorder()
        panel.add(scrollPane, BorderLayout.CENTER)
        
        // 更新标题字段长度显示
        updateTitleLength()
        titleField.document.addDocumentListener(object : DocumentListener {
            override fun insertUpdate(e: DocumentEvent) { updateTitleLength() }
            override fun removeUpdate(e: DocumentEvent) { updateTitleLength() }
            override fun changedUpdate(e: DocumentEvent) { updateTitleLength() }
        })
        
        // 如果不是查看模式，才加载数据
        if (!isViewMode && existingIssue == null) {
            loadData()
        }
        
        return panel
    }
    
    private fun updateTitleLength() {
        val length = titleField.text.length
        titleLengthLabel.text = "$length/100"
        
        // 如果超过100个字符，显示为红色
        if (length > 100) {
            titleLengthLabel.foreground = UIUtil.getErrorForeground()
        } else {
            titleLengthLabel.foreground = UIUtil.getLabelForeground()
        }
    }
    
    private fun createCodeSelectionPanel(): JComponent {
        val panel = JPanel(BorderLayout())
        panel.border = BorderFactory.createTitledBorder("代码选择信息")
        
        if (codeSelection != null) {
            val infoPanel = JPanel(GridBagLayout())
            val constraints = GridBagConstraints()
            constraints.fill = GridBagConstraints.HORIZONTAL
            constraints.weightx = 1.0
            constraints.insets = JBUI.insets(2)
            
            // 类名
            constraints.gridx = 0
            constraints.gridy = 0
            infoPanel.add(JBLabel("类名:"), constraints)
            
            constraints.gridx = 1
            infoPanel.add(JBLabel(codeSelection.className), constraints)
            
            // 文件路径 - 转为包路径格式
            constraints.gridx = 0
            constraints.gridy = 1
            infoPanel.add(JBLabel("包路径:"), constraints)
            
            constraints.gridx = 1
            val packagePath = getPackagePathFromFilePath(codeSelection.filePath)
            infoPanel.add(JBLabel(packagePath), constraints)
            
            // 行号
            constraints.gridx = 0
            constraints.gridy = 2
            infoPanel.add(JBLabel("代码行:"), constraints)
            
            constraints.gridx = 1
            val lineInfo = if (codeSelection.lineStart == codeSelection.lineEnd) {
                "第 ${codeSelection.lineStart} 行"
            } else {
                "第 ${codeSelection.lineStart} - ${codeSelection.lineEnd} 行"
            }
            infoPanel.add(JBLabel(lineInfo), constraints)
            
            // 提交信息
            if (codeSelection.commitInfo != null) {
                constraints.gridx = 0
                constraints.gridy = 3
                infoPanel.add(JBLabel("提交者:"), constraints)
                
                constraints.gridx = 1
                infoPanel.add(JBLabel(codeSelection.commitInfo.author), constraints)
                
                constraints.gridx = 0
                constraints.gridy = 4
                infoPanel.add(JBLabel("提交时间:"), constraints)
                
                constraints.gridx = 1
                infoPanel.add(JBLabel(codeSelection.commitInfo.date), constraints)
            }
            
            // 选中的代码
            constraints.gridx = 0
            constraints.gridy = 5
            infoPanel.add(JBLabel("选中代码:"), constraints)
            
            constraints.gridx = 0
            constraints.gridy = 6
            constraints.gridwidth = 2
            val codeArea = JBTextArea(codeSelection.selectedCode)
            codeArea.isEditable = false
            codeArea.lineWrap = true
            codeArea.wrapStyleWord = true
            codeArea.font = Font(Font.MONOSPACED, Font.PLAIN, 12)
            constraints.fill = GridBagConstraints.BOTH
            constraints.weighty = 1.0
            infoPanel.add(JBScrollPane(codeArea), constraints)
            
            panel.add(infoPanel, BorderLayout.CENTER)
        } else {
            panel.add(JBLabel("没有选择代码，将创建一般问题"), BorderLayout.CENTER)
        }
        
        return panel
    }
    
    private fun loadData() {
        // 加载优先级
        priorityCombo.removeAllItems()
        priorityMap.keys.forEach { priorityCombo.addItem(it) }
        priorityCombo.selectedItem = "中" // 默认中级优先级
        
        // 加载问题类型
        issueTypeCombo.removeAllItems()
        issueTypeMap.keys.forEach { issueTypeCombo.addItem(it) }
        
        // 如果有代码选择，默认选择代码审查类型
        if (codeSelection != null) {
            issueTypeCombo.selectedItem = "代码审查"
        } else {
            issueTypeCombo.selectedItem = "缺陷"
        }
        
        // 添加问题类型变化监听器，控制严重性下拉框的可用性
        issueTypeCombo.addActionListener {
            val selectedType = issueTypeCombo.selectedItem as String
            severityCombo.isEnabled = selectedType == "代码审查"
        }
        
        // 加载状态
        statusCombo.removeAllItems()
        statusMap.keys.forEach { statusCombo.addItem(it) }
        statusCombo.selectedItem = "待处理" // 默认状态
        
        // 加载严重程度
        severityCombo.removeAllItems()
        severityMap.keys.forEach { severityCombo.addItem(it) }
        severityCombo.selectedItem = "中" // 默认中级严重度
        
        // 根据初始问题类型设置严重性下拉框的可用性
        val selectedType = issueTypeCombo.selectedItem as String
        severityCombo.isEnabled = selectedType == "代码审查"
        
        // 加载项目列表
        loadProjects()
        
        // 加载用户列表(指派人)
        loadProjectMembers(existingIssue?.projectId ?: 0)
    }
    
    /**
     * 加载项目列表
     */
    private fun loadProjects() {
        // 如果已经在查看模式下加载了项目，不再重新加载
        if (projectsLoaded) {
            return
        }

        projectCombo.removeAllItems()

        // 默认禁用确定按钮，直到选择有效项目
        setOKActionEnabled(false)

        // 设置渲染器
        projectCombo.renderer = object : DefaultListCellRenderer() {
            override fun getListCellRendererComponent(
                list: JList<*>?,
                value: Any?,
                index: Int,
                isSelected: Boolean,
                cellHasFocus: Boolean
            ): Component {
                val label = super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus) as JLabel
                if (value is ApiModels.ProjectInfo) {
                    label.text = value.name
                } else if (value == null) {
                    label.text = "请选择项目"
                }
                return label
            }
        }

        try {
            println("[DEBUG] 开始获取项目列表")

            // 在后台线程中执行网络请求
            com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
                try {
                    // 获取默认项目
                    val defaultProject = issueService.getDefaultProject()

                    SwingUtilities.invokeLater {
                        if (defaultProject != null) {
                            println("[DEBUG] 成功获取默认项目: ${defaultProject.id} - ${defaultProject.name}")
                            projectCombo.addItem(defaultProject)
                            projectCombo.selectedItem = defaultProject
                            selectedProject = defaultProject
                            // 标记项目已加载
                            projectsLoaded = true

                            // 清除错误提示
                            setErrorText(null)
                            // 启用"确定"按钮
                            setOKActionEnabled(true)
                            
                            // 立即加载默认项目的指派人列表
                            loadProjectMembers(defaultProject.id)
                        } else {
                            // 如果没有默认项目，加载项目列表
                            loadProjectList()
                        }
                    }
                } catch (e: Exception) {
                    SwingUtilities.invokeLater {
                        println("[ERROR] 加载默认项目时出错: ${e.message}")
                        e.printStackTrace()
                        // 如果加载默认项目失败，尝试加载项目列表
                        loadProjectList()
                    }
                }
            }
        } catch (e: Exception) {
            println("[ERROR] 启动加载项目线程时出错: ${e.message}")
            e.printStackTrace()
            projectCombo.addItem(null)
            setErrorText("加载项目失败: ${e.message}", projectCombo)
            setOKActionEnabled(false)
        }

        // 添加项目选择监听器
        projectCombo.addActionListener {
            val newSelectedProject = projectCombo.selectedItem as? ApiModels.ProjectInfo
            
            // 只有当选择了新的项目时才触发加载
            if (newSelectedProject != selectedProject) {
                selectedProject = newSelectedProject
                
                // 验证选择的项目是否有效
                if (selectedProject != null && selectedProject?.id ?: -1 > 0) {
                    setErrorText(null)
                    setOKActionEnabled(true)
                    
                    // 加载指派人列表
                    println("[DEBUG] 项目选择变更，加载新项目的指派人列表: ${selectedProject?.id}")
                    loadProjectMembers(selectedProject?.id ?: 0)
                } else {
                    setErrorText("请选择一个项目", projectCombo)
                    setOKActionEnabled(false)
                    // 清空指派人列表
                    clearAssigneeCombo()
                }
            }
        }
    }

    /**
     * 加载项目列表
     */
    private fun loadProjectList() {
        println("[DEBUG] 加载项目列表")
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val projects = issueService.getProjects(page = 1, pageSize = 100)

                SwingUtilities.invokeLater {
                    if (projects.isNotEmpty()) {
                        println("[DEBUG] 成功获取${projects.size}个项目")
                        // 先添加提示项
                        projectCombo.addItem(ApiModels.ProjectInfo(
                            id = -1,
                            name = "-- 请选择项目 --",
                            description = "",
                            createdAt = ""
                        ))
                        // 再添加实际的项目列表
                        projects.forEach {
                            println("[DEBUG] 项目: ${it.id} - ${it.name}")
                            projectCombo.addItem(it)
                        }
                        
                        // 选择提示项
                        projectCombo.selectedIndex = 0
                        
                        // 标记项目已加载
                        projectsLoaded = true
                        
                        setOKActionEnabled(false)
                        setErrorText("请选择一个项目", projectCombo)
                    } else {
                        println("[WARN] 没有获取到项目，或项目列表为空")
                        projectCombo.addItem(null)
                        setErrorText("请先登录并确保有可用项目", projectCombo)
                        setOKActionEnabled(false)
                    }
                }
            } catch (e: Exception) {
                SwingUtilities.invokeLater {
                    println("[ERROR] 加载项目列表时出错: ${e.message}")
                    e.printStackTrace()
                    projectCombo.addItem(null)
                    setErrorText("加载项目失败: ${e.message}", projectCombo)
                    setOKActionEnabled(false)
                }
            }
        }
    }

    /**
     * 清空指派人下拉框
     */
    private fun clearAssigneeCombo() {
        assigneeCombo.removeAllItems()
        assigneeCombo.addItem(null)
    }

    /**
     * 加载项目成员列表
     */
    private fun loadProjectMembers(projectId: Int) {
        println("[DEBUG] 开始加载项目成员，项目ID: $projectId")
        
        // 如果项目ID无效，清空指派人列表并返回
        if (projectId <= 0) {
            println("[DEBUG] 项目ID无效，清空指派人列表: $projectId")
            clearAssigneeCombo()
            return
        }

        // 设置渲染器（如果还没设置）
        if (assigneeCombo.renderer !is DefaultListCellRenderer) {
            assigneeCombo.renderer = object : DefaultListCellRenderer() {
                override fun getListCellRendererComponent(
                    list: JList<*>?,
                    value: Any?,
                    index: Int,
                    isSelected: Boolean,
                    cellHasFocus: Boolean
                ): Component {
                    val label = super.getListCellRendererComponent(list, value, index, isSelected, cellHasFocus) as JLabel
                    if (value == null) {
                        label.text = "未指派"
                    } else if (value is ApiModels.UserInfo) {
                        label.text = value.username
                    }
                    return label
                }
            }
        }
        
        // 先清空现有列表并添加"未指派"选项
        clearAssigneeCombo()
        
        // 先尝试从IssueService内存缓存中获取指派人列表
        val assigneesFromMemory = issueService.getAssigneesFromMemory(projectId)
        
        if (assigneesFromMemory.isNotEmpty()) {
            println("[DEBUG] 使用内存缓存中的指派人数据，数量: ${assigneesFromMemory.size}")
            SwingUtilities.invokeLater {
                assigneesFromMemory.forEach { user ->
                    assigneeCombo.addItem(user)
                }
            }
            return
        }
        
        // 启动预加载
        issueService.preloadAssignees(projectId)
        
        // 从服务器加载
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val members = issueService.getProjectMembers(projectId)
                println("[DEBUG] 从服务器获取到项目成员数量: ${members.size}")
                
                SwingUtilities.invokeLater {
                    // 使用Set确保用户ID的唯一性
                    val uniqueUserMap = mutableMapOf<Int, ApiModels.UserInfo>()
                    
                    // 将项目成员转换为UserInfo对象并添加到Map中
                    members.forEach { member ->
                        if (!uniqueUserMap.containsKey(member.userId)) {
                            uniqueUserMap[member.userId] = ApiModels.UserInfo(
                                id = member.userId,
                                username = member.username,
                                email = null,
                                roles = listOf(ApiModels.UserInfo.Role(name = member.roleName)),
                                isActive = member.isActive
                            )
                        }
                    }
                    
                    println("[DEBUG] 过滤后的唯一用户数量: ${uniqueUserMap.size}")
                    
                    // 清空已有项目，避免与已有项重复
                    clearAssigneeCombo()
                    
                    // 将过滤后的用户列表添加到下拉框
                    uniqueUserMap.values.forEach { user ->
                        assigneeCombo.addItem(user)
                    }
                }
            } catch (e: Exception) {
                println("[ERROR] 加载项目成员失败: ${e.message}")
                e.printStackTrace()
                
                SwingUtilities.invokeLater {
                    setErrorText("加载项目成员失败: ${e.message}", assigneeCombo)
                }
            }
        }
    }
    
    override fun doValidate(): ValidationInfo? {
        // 在查看模式下不验证
        if (isViewMode) {
            return null
        }
        
        // 标题验证
        if (titleField.text.isBlank()) {
            return ValidationInfo("请输入问题标题", titleField)
        }
        
        if (titleField.text.length > 100) {
            return ValidationInfo("标题最多100个字符", titleField)
        }
        
        // 项目验证
        if (selectedProject == null) {
            return ValidationInfo("请选择项目", projectCombo)
        }
        
        return null
    }
    
    override fun doOKAction() {
        if (isViewMode) {
            close(DialogWrapper.OK_EXIT_CODE)
            return
        }

        if (selectedProject == null || selectedProject?.id ?: -1 <= 0) {
            Messages.showErrorDialog("请选择项目", "无效输入")
            return
        }

        val title = titleField.text
        if (title.isNullOrBlank()) {
            Messages.showErrorDialog("标题不能为空", "无效输入")
            return
        }
        
        val description = descriptionArea.text
        val priorityItem = priorityCombo.selectedItem as String
        val priority = priorityMap[priorityItem] ?: "medium"
        
        val issueTypeItem = issueTypeCombo.selectedItem as String
        val issueType = issueTypeMap[issueTypeItem] ?: "bug"
        
        val severity = if (issueType == "bug" || issueType == "security") {
            val severityItem = severityCombo.selectedItem as String?
            severityMap[severityItem] ?: "medium"
        } else {
            null
        }
        
        val statusItem = statusCombo.selectedItem as String?
        val status = statusMap[statusItem] ?: "open"
        
        val assigneeId = (assigneeCombo.selectedItem as? ApiModels.UserInfo)?.id
        
        val codeContent = codeSelection?.selectedCode
        val filePath = codeSelection?.filePath?.let { getPackagePathFromFilePath(it) } // 转换为包路径
        val lineStart = codeSelection?.lineStart
        val lineEnd = codeSelection?.lineEnd
        
        if (existingIssue != null && isEditMode) {
            // 更新现有问题
            val updateRequest = ApiModels.IssueUpdateRequest(
                id = existingIssue.id,
                title = title,
                description = description,
                priority = priority,
                issueType = issueType,
                severity = severity,
                status = status,
                assigneeId = assigneeId,
                projectId = selectedProject?.id
            )
            
            val result = issueService.updateIssue(updateRequest)
            if (result) {
                close(DialogWrapper.OK_EXIT_CODE)
            } else {
                Messages.showErrorDialog("更新问题失败", "错误")
            }
        } else {
            // 创建新问题
            val createRequest = ApiModels.IssueCreateRequest(
                title = title,
                description = description,
                priority = priority,
                issueType = issueType,
                severity = severity,
                status = status,
                assigneeId = assigneeId,
                projectId = selectedProject?.id!!,
                codeContent = codeContent,
                filePath = filePath,
                lineStart = lineStart,
                lineEnd = lineEnd
            )
            
            val result = issueService.createIssue(createRequest)
            if (result != null) {
                close(DialogWrapper.OK_EXIT_CODE)
            } else {
                Messages.showErrorDialog("创建问题失败", "错误")
            }
        }
    }
    
    override fun createSouthPanel(): JComponent {
        val southPanel = super.createSouthPanel() as JPanel
        
        // 获取按钮，设置样式
        for (component in southPanel.components) {
            if (component is JButton) {
                component.background = JBColor(0x2563EB, 0x3B82F6) // 蓝色按钮背景
                component.foreground = JBColor.WHITE
                component.border = BorderFactory.createEmptyBorder(8, 16, 8, 16)
            } else if (component is JPanel) {
                // 遍历嵌套面板中的按钮
                for (nestedComponent in component.components) {
                    if (nestedComponent is JButton) {
                        nestedComponent.background = JBColor(0x2563EB, 0x3B82F6)
                        nestedComponent.foreground = JBColor.WHITE
                        nestedComponent.border = BorderFactory.createEmptyBorder(8, 16, 8, 16)
                    }
                }
            }
        }
        
        return southPanel
    }
    
    /**
     * 将文件路径转换为包路径格式（com.example.MyClass）
     */
    private fun getPackagePathFromFilePath(filePath: String): String {
        // 移除文件扩展名
        var path = filePath
        val lastDotIndex = path.lastIndexOf('.')
        if (lastDotIndex != -1) {
            path = path.substring(0, lastDotIndex)
        }
        
        // 查找src/main/java或src/main/kotlin等常见源码目录
        val sourceDirectories = listOf("/src/main/java/", "/src/main/kotlin/", "/src/")
        var sourceDirIndex = -1
        
        for (sourceDir in sourceDirectories) {
            val index = path.indexOf(sourceDir)
            if (index != -1) {
                sourceDirIndex = index + sourceDir.length
                break
            }
        }
        
        // 如果找到了源码目录，提取包路径
        if (sourceDirIndex != -1) {
            path = path.substring(sourceDirIndex)
        }
        
        // 将路径分隔符替换为点号
        path = path.replace('/', '.').replace('\\', '.')
        
        // 移除开头和结尾的点号
        path = path.trim('.')
        
        return path
    }
} 