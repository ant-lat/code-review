package com.ant.code.coderplugin.ui

import com.ant.code.coderplugin.api.ApiModels
import com.ant.code.coderplugin.service.AuthService
import com.ant.code.coderplugin.service.IssueService
import com.ant.code.coderplugin.settings.CodeReviewSettings
import com.intellij.openapi.Disposable
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.ComboBox
import com.intellij.openapi.util.Disposer
import com.intellij.ui.components.JBList
import com.intellij.ui.components.JBScrollPane
import com.intellij.util.ui.JBUI
import com.intellij.util.ui.UIUtil
import java.awt.BorderLayout
import java.awt.Color
import java.awt.Component
import java.awt.Dimension
import java.awt.FlowLayout
import java.awt.Graphics
import java.awt.Graphics2D
import java.awt.RenderingHints
import java.awt.event.ActionEvent
import java.awt.event.ActionListener
import java.awt.event.MouseAdapter
import java.awt.event.MouseEvent
import java.awt.geom.Ellipse2D
import javax.swing.*
import javax.swing.DefaultListCellRenderer
import javax.swing.event.ListSelectionEvent
import javax.swing.event.ListSelectionListener
import com.intellij.ide.ui.LafManager
import com.intellij.ide.ui.LafManagerListener
import com.intellij.ui.JBColor
import java.awt.event.MouseListener
import java.awt.BasicStroke
import javax.swing.table.AbstractTableModel
import javax.swing.table.DefaultTableCellRenderer
import com.intellij.ui.scale.JBUIScale
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.ui.DialogWrapper
import com.intellij.ui.components.JBLabel
import com.intellij.ui.table.JBTable
import javax.swing.table.TableCellEditor
import javax.swing.table.TableCellRenderer
import javax.swing.CellEditor
import javax.swing.table.TableModel
import java.awt.CardLayout
import java.awt.Font

class IssueListPanel(private val project: Project) : JPanel(BorderLayout()), Disposable {
    private val issueService = IssueService.getInstance(project)
    private val authService = AuthService.getInstance(project)
    private val settings = CodeReviewSettings.getInstance()
    private var tableModel = IssueTableModel()
    private var table = JTable(tableModel)
    private val refreshButton = JButton("刷新")
    private val createButton = JButton("创建问题")
    private val statusMap = mapOf(
        "open" to "待处理",
        "in_progress" to "处理中",
        "resolved" to "已解决",
        "verified" to "已验证",
        "closed" to "已关闭",
        "reopened" to "重新打开",
        "rejected" to "已拒绝"
    )

    private val priorityMap = mapOf(
        "low" to "低",
        "medium" to "中",
        "high" to "高",
        "critical" to "紧急"
    )

    private val typeMap = mapOf(
        "bug" to "缺陷",
        "feature" to "功能",
        "improvement" to "改进",
        "task" to "任务",
        "security" to "安全问题",
        "code_review" to "代码审查"
    )

    // 为状态定义对应的颜色（亮色主题下的颜色，暗色主题下的颜色）
    private val statusColors = mapOf(
        "open" to JBColor(0x2563EB, 0x5E9BFF),
        "in_progress" to JBColor(0xF59E0B, 0xFFB74D),
        "resolved" to JBColor(0x10B981, 0x4CAF50),
        "verified" to JBColor(0x059669, 0x388E3C),
        "closed" to JBColor(0x6B7280, 0x9E9E9E),
        "reopened" to JBColor(0x9333EA, 0xBA68C8),
        "rejected" to JBColor(0xEF4444, 0xFF5252)
    )

    private var avatarButton: JButton? = null
    private var themeLafListener: LafManagerListener? = null
    private var projectsLoaded = false // 添加标志变量以跟踪项目是否已加载
    private var projectCombo = ComboBox<ApiModels.ProjectInfo>() // 将ComboBox升级为类成员变量

    private val LOG = com.intellij.openapi.diagnostic.Logger.getInstance(IssueListPanel::class.java)

    // 缓存项目成员和用户列表
    private val projectMembersCache = mutableMapOf<Int, List<ApiModels.ProjectMember>>()
    private val usersCache = mutableMapOf<Int, List<ApiModels.UserInfo>>()
    
    // 项目成员加载状态
    private var isLoadingMembers = false

    // 添加标志位防止重复加载
    private var isLoadingIssues = false

    // 引入导入映射
    private val reverseStatusMap = mapOf(
        "open" to "待处理",
        "in_progress" to "进行中",
        "resolved" to "已解决",
        "verified" to "已验证",
        "closed" to "已关闭",
        "reopened" to "重新打开",
        "rejected" to "已拒绝"
    )
    
    private val reverseIssueTypeMap = mapOf(
        "bug" to "缺陷",
        "feature" to "功能",
        "improvement" to "改进",
        "task" to "任务",
        "code_review" to "代码审查",
        "security" to "安全问题"
    )
    
    private val reversePriorityMap = mapOf(
        "low" to "低",
        "medium" to "中", 
        "high" to "高",
        "critical" to "紧急"
    )
    
    private val reverseSeverityMap = mapOf(
        "low" to "低",
        "medium" to "中", 
        "high" to "高",
        "critical" to "紧急"
    )

    init {
        // 在项目销毁时释放资源
        Disposer.register(project, this)

        initComponents()
        setupThemeListener()
        // 不在初始化时加载问题列表，等待用户选择项目后再加载
    }

    private fun setupThemeListener() {
        themeLafListener = LafManagerListener {
            updateUITheme()
        }

        // 订阅主题变化事件
        val connection = project.messageBus.connect(this)
        connection.subscribe(LafManagerListener.TOPIC, themeLafListener!!)
    }

    private fun updateUITheme() {
        // 更新UI组件以适应当前主题
        background = UIUtil.getPanelBackground()

        // 更新表格样式
        table.gridColor = UIUtil.getTableGridColor()
        table.background = UIUtil.getTableBackground()

        // 更新表头样式
        val tableHeader = table.tableHeader
        tableHeader.background = UIUtil.getPanelBackground()
        tableHeader.foreground = UIUtil.getLabelForeground()
        tableHeader.border = JBUI.Borders.customLine(UIUtil.getBoundsColor(), 0, 0, 1, 0)

        // 更新按钮样式
        updateButtonsStyle()

        // 刷新UI
        revalidate()
        repaint()
    }

    private fun updateButtonsStyle() {
        val buttonBackgroundColor = UIUtil.getPanelBackground()
        val buttonForegroundColor = UIUtil.getLabelForeground()
        val buttonBorderColor = UIUtil.getBoundsColor()
        refreshButton.apply {
            background = buttonBackgroundColor
            foreground = buttonForegroundColor
            border = JBUI.Borders.customLine(buttonBorderColor, 1)
        }

        createButton.apply {
            background = buttonBackgroundColor
            foreground = buttonForegroundColor
            border = JBUI.Borders.customLine(buttonBorderColor, 1)
        }

        avatarButton?.repaint()
    }

    /**
     * 初始化组件
     */
    private fun initComponents() {
        // 设置面板布局
        layout = BorderLayout()
        
        // 创建工具栏
        val toolbarPanel = createToolbar()
        add(toolbarPanel, BorderLayout.NORTH)
        
        // 创建表格面板
        val tablePanel = JPanel(BorderLayout())
        table = JBTable() // 使用JBTable代替JTable
        tableModel = IssueTableModel()
        table.model = tableModel
        
        // 初始化表格
        initTable()
        
        // 添加表格到滚动面板
        val scrollPane = JBScrollPane(table)
        tablePanel.add(scrollPane, BorderLayout.CENTER)
        
        // 添加表格面板到主面板
        add(tablePanel, BorderLayout.CENTER)
        
        // 创建状态栏
        val statusBar = createStatusBar()
        add(statusBar, BorderLayout.SOUTH)
        
        // 设置右键菜单
        setupContextMenu()
        
        // 注册到主题变化监听器
        setupThemeListener()
        
        // 初始加载用户信息
        updateUserInfoUI()
    }

    /**
     * 创建工具栏
     */
    private fun createToolbar(): JPanel {
        val toolbar = JPanel(FlowLayout(FlowLayout.LEFT))
        toolbar.border = JBUI.Borders.empty(5)
        
        // 刷新按钮
        val refreshButton = JButton("刷新")
        refreshButton.addActionListener {
            // 直接从类成员变量获取当前选中的项目
            val selectedProject = projectCombo.selectedItem as? ApiModels.ProjectInfo
            
            if (selectedProject != null && selectedProject.id > 0) {
                println("[DEBUG] 点击刷新按钮: 当前选中项目=${selectedProject.name}, ID=${selectedProject.id}")
                // 加载项目成员
                if (projectMembersCache[selectedProject.id] == null) {
                    println("[DEBUG] 项目成员缓存为空，现在加载")
                }
                // 加载问题列表
                loadIssues(true)
            } else {
                // 记录详细的调试信息
                println("[DEBUG] 点击刷新按钮: 未选择有效项目")
                if (selectedProject == null) {
                    println("[DEBUG] 选中项为null")
                } else {
                    println("[DEBUG] 选中项的ID不是正数: ID=${selectedProject.id}, 名称=${selectedProject.name}")
                }
                showErrorNotification("未选择项目", "请先选择一个项目再查看问题列表")
            }
        }
        
        // 创建问题按钮
        val createIssueButton = JButton("创建问题")
        createIssueButton.addActionListener {
            showCreateIssueDialog()
        }
        
        // 重新初始化项目选择下拉框
        projectCombo = ComboBox<ApiModels.ProjectInfo>()
        projectCombo.preferredSize = Dimension(200, 30)
        projectCombo.maximumSize = Dimension(250, 30)
        
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
                when (value) {
                    null -> label.text = "请选择项目"
                    is ApiModels.ProjectInfo -> {
                        if (value.id <= 0) {
                            label.text = "请选择项目"
                        } else {
                            label.text = value.name
                        }
                    }
                    else -> label.text = value.toString()
                }
                return label
            }
        }
        
        // 添加鼠标监听器，检查登录状态
        projectCombo.addMouseListener(object : MouseAdapter() {
            override fun mouseClicked(e: MouseEvent?) {
                if (!authService.isLoggedIn()) {
                    com.intellij.openapi.ui.Messages.showWarningDialog(
                        project,
                        "您需要登录后才能查看项目列表",
                        "请先登录"
                    )
                    showLoginDialog()
                    e?.consume() // 阻止事件继续传递
                    return
                }
                
                // 已登录，检查下拉框内容是否为空或仅有"请选择/点击加载"等提示项
                if (projectCombo.itemCount <= 1) {
                    val firstItem = projectCombo.getItemAt(0)
                    if (firstItem == null || firstItem.id <= 0) {
                        println("[DEBUG] 项目下拉框为空或只有提示项，加载项目列表")
                        loadProjectsIntoCombo(projectCombo)
                    }
                } else {
                    println("[DEBUG] 项目下拉框已有数据，不重新加载")
                }
            }
        })
        
        // 添加选择事件监听
        projectCombo.addActionListener { e ->
            val selectedProject = projectCombo.selectedItem as? ApiModels.ProjectInfo
            if (selectedProject != null) {
                saveDefaultProject(selectedProject)
                
                // 加载问题列表
                loadIssues(false)
            }
        }
        
        // 创建项目选择区域
        val projectPanel = JPanel(BorderLayout())
        val projectLabel = JLabel("项目: ")
        projectPanel.add(projectLabel, BorderLayout.WEST)
        projectPanel.add(projectCombo, BorderLayout.CENTER)
        projectPanel.border = JBUI.Borders.emptyRight(10)
        
        // 设置合适的尺寸
        projectPanel.preferredSize = Dimension(250, 30)

        // 创建用户头像图标按钮
        try {
            println("[DEBUG] 开始加载头像图标")

            // 创建自定义圆形用户头像按钮
            avatarButton = createAvatarButton()

            // 设置按钮样式
            avatarButton?.toolTipText = if (authService.isLoggedIn()) "查看用户信息" else "点击登录"
            avatarButton?.border = JBUI.Borders.empty(5)
            avatarButton?.isContentAreaFilled = false // 移除按钮背景
            avatarButton?.addActionListener { handleAvatarClick() }

            println("[DEBUG] 头像按钮创建完成")
        } catch (e: Exception) {
            println("[ERROR] 创建头像按钮时出错: ${e.message}")
            e.printStackTrace()
            // 创建带文本的备选按钮
            avatarButton = JButton("登录")
            avatarButton?.addActionListener { handleAvatarClick() }
        }

        // 创建主工具栏面板（使用BorderLayout，便于在右侧放置头像按钮）
        val mainToolbarPanel = JPanel(BorderLayout())
        
        // 左侧工具栏面板
        val leftPanel = JPanel(FlowLayout(FlowLayout.LEFT))
        leftPanel.add(projectPanel)
        leftPanel.add(Box.createHorizontalStrut(10))
        leftPanel.add(refreshButton)
        leftPanel.add(Box.createHorizontalStrut(10))
        leftPanel.add(createIssueButton)
        
        // 右侧面板 - 放置头像
        val rightPanel = JPanel(FlowLayout(FlowLayout.RIGHT))
        rightPanel.add(avatarButton)
        
        // 将左右面板添加到主面板
        mainToolbarPanel.add(leftPanel, BorderLayout.WEST)
        mainToolbarPanel.add(rightPanel, BorderLayout.EAST)
        
        return mainToolbarPanel
    }
    
    /**
     * 加载项目列表到下拉框
     */
    private fun loadProjectsIntoCombo(projectCombo: ComboBox<ApiModels.ProjectInfo>) {
        // 检查登录状态
        if (!authService.isLoggedIn()) {
            projectCombo.removeAllItems()
            projectCombo.addItem(ApiModels.ProjectInfo(
                id = -1,
                name = "请先登录",
                description = "",
                createdAt = "",
                repositoryUrl = null,
                repositoryType = null,
                branch = null,
                status = null,
                memberCount = null,
                creator = null
            ))
            projectCombo.isEnabled = false
            return
        }
        
        // 清空并显示加载中...
        projectCombo.removeAllItems()
        projectCombo.addItem(ApiModels.ProjectInfo(
            id = -1,
            name = "加载中...",
            description = "",
            createdAt = "",
            repositoryUrl = null,
            repositoryType = null,
            branch = null,
            status = null,
            memberCount = null,
            creator = null
        ))
        projectCombo.isEnabled = false
        
        // 后台加载项目列表
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val issueService = IssueService.getInstance(project)
                
                // 获取项目列表（登录时已预加载到IssueService中）
                val projects = issueService.getProjects(page = 1, pageSize = 100)
                println("[DEBUG] 加载项目列表完成，共${projects.size}个项目")
                
                // 在EDT线程中更新UI
                SwingUtilities.invokeLater {
                    try {
                        projectCombo.removeAllItems()
                        
                        if (projects.isNotEmpty()) {
                            // 添加项目到下拉框
                            projects.forEach { projectCombo.addItem(it) }
                            
                            // 选择默认项目
                            val settings = CodeReviewSettings.getInstance()
                            val defaultProjectId = settings.defaultProjectId
                            var selectedIndex = 0
                            
                            if (defaultProjectId > 0) {
                                val defaultProject = projects.find { it.id == defaultProjectId }
                                if (defaultProject != null) {
                                    projectCombo.selectedItem = defaultProject
                                    selectedIndex = projectCombo.selectedIndex
                                } else {
                                    projectCombo.selectedIndex = 0
                                    selectedIndex = 0
                                }
                            } else if (projectCombo.itemCount > 0) {
                                projectCombo.selectedIndex = 0
                                selectedIndex = 0
                            }
                            
                            projectCombo.isEnabled = true
                            
                            // 如果有选择的项目，主动触发项目选择事件以加载问题列表
                            if (selectedIndex >= 0 && projectCombo.itemCount > 0) {
                                val project = projectCombo.getItemAt(selectedIndex)
                                if (project != null && project.id > 0) {
                                    // 保存为默认项目
                                    settings.setDefaultProject(project.id, project.name)
                                }
                            }
                        } else {
                            // 如果没有项目，显示空提示
                            projectCombo.addItem(ApiModels.ProjectInfo(
                                id = -1,
                                name = "没有可用项目",
                                description = "",
                                createdAt = "",
                                repositoryUrl = null,
                                repositoryType = null,
                                branch = null,
                                status = null,
                                memberCount = null,
                                creator = null
                            ))
                            projectCombo.isEnabled = false
                        }
                    } catch (e: Exception) {
                        LOG.error("更新项目下拉框时出错", e)
                        projectCombo.removeAllItems()
                        projectCombo.addItem(ApiModels.ProjectInfo(
                            id = -1,
                            name = "加载失败: ${e.message}",
                            description = "",
                            createdAt = "",
                            repositoryUrl = null,
                            repositoryType = null,
                            branch = null,
                            status = null,
                            memberCount = null,
                            creator = null
                        ))
                        projectCombo.isEnabled = false
                    }
                }
            } catch (e: Exception) {
                LOG.error("加载项目列表时出错", e)
                // 在EDT线程中更新UI
                SwingUtilities.invokeLater {
                    projectCombo.removeAllItems()
                    projectCombo.addItem(ApiModels.ProjectInfo(
                        id = -1,
                        name = "加载失败: ${e.message}",
                        description = "",
                        createdAt = "",
                        repositoryUrl = null,
                        repositoryType = null,
                        branch = null,
                        status = null,
                        memberCount = null,
                        creator = null
                    ))
                    projectCombo.isEnabled = false
                }
            }
        }
    }

    // 显示登录对话框
    private fun showLoginDialog() {
        try {
            // 如果在EDT线程，直接显示对话框
            if (com.intellij.openapi.application.ApplicationManager.getApplication().isDispatchThread) {
                val loginDialog = LoginDialog(project)
                if (loginDialog.showAndGet()) {
                    // 对话框关闭后刷新数据
                    refreshData()
                }
            } else {
                // 如果不在EDT线程，切换到EDT显示对话框
                com.intellij.openapi.application.ApplicationManager.getApplication().invokeLater {
                    try {
                        val loginDialog = LoginDialog(project)
                        if (loginDialog.showAndGet()) {
                            // 对话框关闭后刷新数据
                            refreshData()
                        }
                    } catch (e: Exception) {
                        LOG.error("显示登录对话框时出错", e)
                    }
                }
            }
        } catch (e: Exception) {
            LOG.error("显示登录对话框时出错", e)
        }
    }

    // 处理头像点击事件
    private fun handleAvatarClick() {
        if (authService.isLoggedIn()) {
            // 已登录，显示用户详情和退出选项
            val user = authService.getCurrentUser()
            if (user != null) {
                // 创建下拉菜单
                val popupMenu = JPopupMenu()
                
                // 在下拉菜单顶部显示用户名
                val userLabel = JLabel("  用户: ${user.username}  ")
                userLabel.font = userLabel.font.deriveFont(Font.BOLD)
                userLabel.border = JBUI.Borders.empty(5, 10)
                
                // 将用户名添加到面板中
                val userPanel = JPanel(BorderLayout())
                userPanel.add(userLabel, BorderLayout.CENTER)
                userPanel.border = JBUI.Borders.customLine(JBColor.border(), 0, 0, 1, 0)
                
                // 将面板添加到弹出菜单
                popupMenu.add(userPanel)
                
                // 添加查看用户信息选项
                val viewInfoItem = JMenuItem("个人信息")
                viewInfoItem.addActionListener {
                    // 查看用户信息
                    val message = """
                        用户ID: ${user.id}
                        用户名: ${user.username}
                        邮箱: ${user.email ?: "未设置"}
                        状态: ${if (user.isActive ?: true) "正常" else "禁用"}
                        注册时间: ${user.createdAt}
                    """.trimIndent()

                    com.intellij.openapi.ui.Messages.showInfoMessage(
                        project,
                        message,
                        "用户信息"
                    )
                }
                popupMenu.add(viewInfoItem)
                
                // 添加分隔线
                popupMenu.addSeparator()
                
                // 添加退出登录选项
                val logoutItem = JMenuItem("退出登录")
                logoutItem.addActionListener {
                    val confirmLogout = com.intellij.openapi.ui.Messages.showYesNoDialog(
                        project,
                        "确认退出登录？",
                        "退出登录",
                        com.intellij.openapi.ui.Messages.getQuestionIcon()
                    )
                    
                    if (confirmLogout == com.intellij.openapi.ui.Messages.YES) {
                        // 执行退出操作
                        try {
                            authService.logout()
                            // 更新UI
                            updateUserInfoUI()
                            // 清空项目列表
                            projectCombo.removeAllItems()
                            projectCombo.addItem(ApiModels.ProjectInfo(
                                id = -1,
                                name = "请先登录",
                                description = "",
                                createdAt = "",
                                repositoryUrl = null,
                                repositoryType = null,
                                branch = null,
                                status = null,
                                memberCount = null,
                                creator = null
                            ))
                            // 清空表格内容
                            tableModel.clearData()
                            com.intellij.openapi.ui.Messages.showInfoMessage(
                                project,
                                "已成功退出登录",
                                "退出成功"
                            )
                        } catch (e: Exception) {
                            com.intellij.openapi.ui.Messages.showErrorDialog(
                                project,
                                "退出登录时出错: ${e.message}",
                                "错误"
                            )
                        }
                    }
                }
                popupMenu.add(logoutItem)
                
                // 显示弹出菜单
                popupMenu.show(avatarButton, 0, avatarButton?.height ?: 0)
            }
        } else {
            // 未登录，显示登录对话框
            showLoginDialog()
        }
    }

    // 更新用户信息UI
    private fun updateUserInfoUI() {
        try {
            val isLoggedIn = authService.isLoggedIn()
            val user = authService.getCurrentUser()

            // 更新头像按钮提示
            if (isLoggedIn && user != null) {
                avatarButton?.toolTipText = "已登录: ${user.username} (点击查看详情)"
                println("[DEBUG] 用户已登录: ${user.username}")

                // 更新头像按钮显示的用户首字母
                if (avatarButton is JButton) {
                    (avatarButton as JButton).text = user.username.take(1).uppercase()
                    avatarButton?.repaint()
                }
            } else {
                avatarButton?.toolTipText = "未登录 (点击登录)"
                println("[DEBUG] 用户未登录或获取用户信息失败")

                // 重置为默认首字母
                if (avatarButton is JButton) {
                    (avatarButton as JButton).text = "U"
                    avatarButton?.repaint()
                }
            }

            // 刷新UI组件
            avatarButton?.repaint()
            revalidate()
            repaint()
        } catch (e: Exception) {
            println("[ERROR] 更新用户信息UI时出错: ${e.message}")
        }
    }

    // 加载问题列表
    fun loadIssues(forceRefresh: Boolean = false) {
        try {
            // 如果正在加载，则直接返回
            if (isLoadingIssues) {
                println("[INFO] 问题列表正在加载中，跳过重复请求")
                return
            }
            
        if (authService.isLoggedIn()) {
                // 直接从类成员变量获取选中项目
                val selectedProject = projectCombo.selectedItem as? ApiModels.ProjectInfo
                val selectedProjectId = selectedProject?.id ?: -1
                val selectedProjectName = selectedProject?.name ?: ""
                
                // 详细的调试日志
                println("[DEBUG] loadIssues: 选中项目ID=$selectedProjectId, 名称=$selectedProjectName")
                
                // 如果没有选择有效的项目，清空表格和显示提示
                if (selectedProjectId <= 0) {
                    println("[INFO] 未选择有效项目，不加载问题列表，ID: $selectedProjectId")
                    tableModel.updateIssues(emptyList())
                    
                    // 仅当用户主动点击刷新按钮或需要强制显示提示时才显示通知
                    if (forceRefresh) {
                        // 检查是否为临时状态项目（如加载中...）
                        if (selectedProject != null) {
                            val name = selectedProject.name.lowercase()
                            if (name.contains("加载") || name.contains("选择") || name.contains("请先")) {
                                println("[DEBUG] 跳过错误提示，当前显示项: ${selectedProject.name}")
                            } else {
                                showErrorNotification("未选择项目", "请先选择一个项目再查看问题列表")
                            }
                        } else {
                            showErrorNotification("未选择项目", "请先选择一个项目再查看问题列表")
                        }
                    }
                    return
                }
                
                // 设置加载标记
                isLoadingIssues = true
                
                // 在后台线程中执行网络操作
                com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
                    try {
                        // 确保先获取最新的用户信息
                        authService.fetchCurrentUser()
                        
                        // 如果是强制刷新，尝试加载项目成员
                        if (forceRefresh && selectedProjectId > 0) {
                            println("[DEBUG] 刷新项目成员缓存")
                        }

                        // 使用SwingUtilities.invokeLater确保UI更新在EDT线程中执行
                        SwingUtilities.invokeLater {
                            // 再获取问题列表
                            val user = authService.getCurrentUser()
                            if (user != null) {
                                println("[DEBUG] 已登录用户: ${user.username}, 正在获取项目[$selectedProjectName]的问题列表")
                                try {
                                    // 根据选中的项目获取该用户可见的问题列表
                                    val issues = issueService.getProjectIssues(selectedProjectId)
                                    tableModel.updateIssues(issues)
                                    updateUserInfoUI()
                                } catch (e: Exception) {
                                    println("[ERROR] 加载问题列表时出错: ${e.message}")
                                    e.printStackTrace()
                                    tableModel.updateIssues(emptyList())
                                    showErrorNotification("加载问题列表失败", e.message ?: "未知错误")
                                }
                            } else {
                                println("[WARNING] 用户已登录但获取用户信息失败，无法加载问题列表")
                                tableModel.updateIssues(emptyList())
                                showErrorNotification("获取用户信息失败", "请尝试重新登录")
                            }
                        }
                    } catch (e: Exception) {
                        println("[ERROR] 获取用户信息时出错: ${e.message}")
                        e.printStackTrace()
                        
                        // 在EDT线程中更新UI
                        SwingUtilities.invokeLater {
                            tableModel.updateIssues(emptyList())
                            showErrorNotification("获取用户信息失败", e.message ?: "未知错误")
                        }
                    } finally {
                        // 确保无论如何都会重置加载标记
                        if (isLoadingIssues) {
                            SwingUtilities.invokeLater {
                                isLoadingIssues = false
                            }
                        }
                    }
                }
            } else {
                println("[INFO] 用户未登录，不加载问题列表")
                tableModel.updateIssues(emptyList())
                
                // 仅在强制刷新时显示提示
                if (forceRefresh) {
                    showLoginDialog()
                }
            }
        } catch (e: Exception) {
            println("[ERROR] 加载问题异常: ${e.message}")
            e.printStackTrace()
            
            // 重置加载标记
            isLoadingIssues = false
            
            tableModel.updateIssues(emptyList())
            showErrorNotification("加载失败", "加载问题列表失败: ${e.message}")
        }
    }

    // 显示错误通知
    private fun showErrorNotification(title: String, message: String) {
        try {
            com.intellij.notification.NotificationGroupManager.getInstance()
                .getNotificationGroup("CodeReview")
                .createNotification(
                    title,
                    message,
                    com.intellij.notification.NotificationType.ERROR
                )
                .notify(project)
        } catch (e: Exception) {
            // 如果通知显示失败，则使用标准错误对话框
            println("[ERROR] 显示通知失败: ${e.message}")
            com.intellij.openapi.ui.Messages.showErrorDialog(
                project, 
                message,
                title
            )
        }
    }

    // 显示信息通知
    private fun showInfoNotification(title: String, message: String) {
        try {
            com.intellij.notification.NotificationGroupManager.getInstance()
                .getNotificationGroup("CodeReview")
                .createNotification(
                    title,
                    message,
                    com.intellij.notification.NotificationType.INFORMATION
                )
                .notify(project)
        } catch (e: Exception) {
            // 如果通知显示失败，则使用标准信息对话框
            println("[ERROR] 显示通知失败: ${e.message}")
            com.intellij.openapi.ui.Messages.showInfoMessage(
                project, 
                message,
                title
            )
        }
    }

    // 显示问题详情
    private fun showIssueDetail(issue: ApiModels.IssueListItem) {
        // 使用CreateIssueDialog作为详情对话框显示问题详情
        val detailDialog = CreateIssueDialog(project, null, issue)
        detailDialog.show()
    }

    // 显示创建问题对话框
    private fun showCreateIssueDialog() {
        if (!authService.isLoggedIn()) {
            com.intellij.openapi.ui.Messages.showInfoMessage(
                project,
                "您需要登录后才能创建问题",
                "请先登录"
            )
            showLoginDialog()
            return
        }

        // 检查是否已选择项目 - 现在直接使用类的成员变量
        val selectedProject = projectCombo.selectedItem as? ApiModels.ProjectInfo
        val selectedProjectId = selectedProject?.id ?: -1
        
        if (selectedProjectId <= 0) {
            com.intellij.openapi.ui.Messages.showInfoMessage(
                project,
                "请先选择一个项目，然后再创建问题",
                "未选择项目"
            )
            return
        }

        val dialog = CreateIssueDialog(project)
        if (dialog.showAndGet()) {
            // 刷新问题列表
            loadIssues(false)
        }
    }

    // 创建自定义头像按钮
    private fun createAvatarButton(): JButton {
        return object : JButton() {
            init {
                isBorderPainted = false
                isContentAreaFilled = false
                isFocusPainted = false
                preferredSize = Dimension(32, 32) // 设置大小
            }

            override fun paintComponent(g: Graphics) {
                super.paintComponent(g)
                val g2 = g as Graphics2D
                g2.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)

                // 获取当前的背景颜色，考虑UI主题
                val bgColor = if (UIUtil.isUnderDarcula()) {
                    JBColor(0x3C3F41, 0x3C3F41) // 暗色主题
                } else {
                    JBColor(0xF2F2F2, 0xF2F2F2) // 亮色主题
                }

                // 判断是否已登录，决定头像样式和文字
                if (authService.isLoggedIn()) {
                    val user = authService.getCurrentUser()
                    val initial = user?.username?.firstOrNull()?.uppercase() ?: "?"

                    // 已登录用户的头像颜色（蓝色系）
                    val avatarColor = JBColor(0x1E88E5, 0x64B5F6)
                    
                    g2.color = avatarColor
                    g2.fill(Ellipse2D.Float(1f, 1f, width - 2f, height - 2f))
                    
                    g2.color = JBColor.WHITE
                    g2.font = font.deriveFont(Font.BOLD, 14f)
                    
                    // 计算文字位置以居中显示
                    val fm = g2.fontMetrics
                    val x = (width - fm.stringWidth(initial)) / 2
                    val y = (height - fm.height) / 2 + fm.ascent
                    
                    g2.drawString(initial, x, y)
                } else {
                    // 未登录用户的头像样式（灰色系带图标）
                    val avatarColor = JBColor(0x78909C, 0x90A4AE) // 使用更柔和的灰色，在浅色和深色主题下看起来都不错
                    
                    g2.color = avatarColor
                    g2.fill(Ellipse2D.Float(1f, 1f, width - 2f, height - 2f))
                    
                    // 绘制用户图标
                    g2.color = JBColor.WHITE
                    g2.stroke = BasicStroke(1.5f)
                    
                    // 绘制头部圆圈
                    val headSize = width * 0.35f
                    g2.fill(Ellipse2D.Float(
                        (width - headSize) / 2,
                        height * 0.25f,
                        headSize,
                        headSize
                    ))
                    
                    // 绘制身体部分
                    val bodyWidth = width * 0.6f
                    val bodyHeight = height * 0.35f
                    val bodyX = (width - bodyWidth) / 2
                    val bodyY = height * 0.55f
                    
                    val bodyShape = Ellipse2D.Float(bodyX, bodyY, bodyWidth, bodyHeight)
                    g2.fill(bodyShape)
                }
                
                // 添加圆形边框
                g2.color = UIUtil.getBoundsColor()
                g2.stroke = BasicStroke(1f)
                g2.drawOval(1, 1, width - 3, height - 3)
            }
        }
    }

    // 设置表格属性和样式
    private fun setupTable() {
        // 状态单元格渲染器
        val statusRenderer = StatusCellRenderer()
        
        // 设置列宽
        val columnModel = table.columnModel
        columnModel.getColumn(0).minWidth = 60 // ID
        columnModel.getColumn(0).maxWidth = 80
        columnModel.getColumn(0).preferredWidth = 60
        
        columnModel.getColumn(1).preferredWidth = 300 // 标题
        columnModel.getColumn(1).minWidth = 150
        
        columnModel.getColumn(2).preferredWidth = 120 // 项目
        columnModel.getColumn(2).minWidth = 80
        
        columnModel.getColumn(3).minWidth = 80 // 状态
        columnModel.getColumn(3).maxWidth = 100
        columnModel.getColumn(3).preferredWidth = 80
        // 为状态列设置自定义渲染器
        columnModel.getColumn(3).cellRenderer = statusRenderer
        
        // 其他列设置通用渲染器
        val alternateRowRenderer = AlternateRowColorRenderer()
        for (i in 0 until columnModel.columnCount) {
            if (i != 3) { // 除了状态列，其他列使用通用渲染器
                columnModel.getColumn(i).cellRenderer = alternateRowRenderer
            }
        }

        // 设置表格行高
        table.rowHeight = 30
        
        // 设置表格选择模式
        table.selectionModel.selectionMode = ListSelectionModel.SINGLE_SELECTION
        
        // 设置表头颜色和字体
        table.tableHeader.foreground = UIUtil.getLabelForeground()
        table.tableHeader.background = UIUtil.getTableBackground()
        table.tableHeader.font = table.tableHeader.font.deriveFont(Font.BOLD)
        
        // 显示网格线
        table.showHorizontalLines = true
        table.showVerticalLines = false
        table.gridColor = JBColor(0xE5E7EB, 0x313438)
    }
    
    // 状态单元格渲染器
    inner class StatusCellRenderer : DefaultTableCellRenderer() {
        override fun getTableCellRendererComponent(
            table: JTable, value: Any?, isSelected: Boolean,
            hasFocus: Boolean, row: Int, column: Int
        ): Component {
            val comp = super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column)
            comp as JLabel
            
            if (!isSelected) {
                if (row % 2 == 0) {
                    comp.background = UIUtil.getTableBackground()
                } else {
                    comp.background = UIUtil.getDecoratedRowColor()
                }
            }
            
            // 获取该行的问题
            val issue = tableModel.getIssueAt(row)
            
            // 设置状态的显示文本
            comp.text = statusMap[issue.status] ?: issue.status
            
            // 根据状态设置字体和颜色
            val statusColor = statusColors[issue.status]
            if (statusColor != null) {
                comp.foreground = statusColor
                comp.font = comp.font.deriveFont(Font.BOLD)
            } else {
                comp.foreground = UIUtil.getLabelForeground()
            }
            
            // 如果是rejected状态，加粗显示
            if (issue.status == "rejected") {
                comp.foreground = statusColors["rejected"] ?: JBColor(0xEF4444, 0xFF5252)
                comp.font = comp.font.deriveFont(Font.BOLD)
            }
            
            // 设置单元格边框
            comp.border = JBUI.Borders.empty(2, 8)
            
            return comp
        }
    }

    // 交替行颜色渲染器
    inner class AlternateRowColorRenderer : DefaultTableCellRenderer() {
        override fun getTableCellRendererComponent(
            table: JTable, value: Any?, isSelected: Boolean,
            hasFocus: Boolean, row: Int, column: Int
        ): Component {
            val c = super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column)

            if (!isSelected) {
                if (row % 2 == 0) {
                    c.background = UIUtil.getTableBackground()
                } else {
                    c.background = UIUtil.getDecoratedRowColor()
                }
            }

            // 设置单元格边框
            setBorder(JBUI.Borders.empty(2, 8))

            return c
        }
    }

    // 刷新数据
    private fun refreshData() {
        try {
            println("[DEBUG] 刷新数据")
            // 清除缓存
            issueService.clearIssueListCache()
            issueService.clearProjectListCache()
            
            // 更新用户信息UI
            updateUserInfoUI()
            
            // 如果用户已登录，加载项目列表
            if (authService.isLoggedIn()) {
                println("[DEBUG] 刷新数据: 用户已登录，加载项目列表")
                loadProjectsIntoCombo(projectCombo)
            } else {
                println("[DEBUG] 刷新数据: 用户未登录，不加载项目列表")
                // 清空并禁用项目选择组件
                    projectCombo.removeAllItems()
                    projectCombo.addItem(ApiModels.ProjectInfo(
                        id = -1,
                    name = "请先登录",
                        description = "",
                        createdAt = "",
                        repositoryUrl = null,
                        repositoryType = null,
                        branch = null,
                        status = null,
                        memberCount = null,
                        creator = null
                    ))
                projectCombo.isEnabled = false
                    
                // 清空表格
                    tableModel.updateIssues(emptyList())
                }
            } catch (e: Exception) {
            println("[ERROR] 刷新数据时出错: ${e.message}")
            e.printStackTrace()
        }
    }
    
    /**
     * 获取工具栏组件
     */
    private fun getToolbarComponents(): Array<Component> {
        // 查找工具栏组件
        for (component in components) {
            if (component is JPanel && component.layout is BorderLayout) {
                // 不需要获取布局对象
                val northComponent = component.getComponent(0)
                if (northComponent is JPanel) {
                    return northComponent.components
                }
            }
        }
        return emptyArray()
    }

    override fun dispose() {
        // 清理资源
        if (themeLafListener != null) {
            // 取消订阅主题变化事件
            try {
                // 在旧版本中无法直接移除监听器，所以只记录日志
                println("[DEBUG] 主题监听器将随对象一起被垃圾回收")
            } catch (e: Exception) {
                println("[ERROR] 移除主题监听器失败: ${e.message}")
            }
        }

        println("[DEBUG] IssueListPanel已释放")
    }

    /**
     * 设置右键菜单
     */
    private fun setupContextMenu() {
        val popup = JPopupMenu()
        
        // 添加查看详情菜单项
        val viewDetailItem = JMenuItem("查看详情")
        viewDetailItem.addActionListener {
            val selectedRow = table.selectedRow
            if (selectedRow >= 0) {
                val issue = tableModel.getIssueAt(selectedRow)
                showIssueDetail(issue)
            }
        }
        popup.add(viewDetailItem)
        
        // 添加跳转到代码位置菜单项
        val navigateToCodeItem = JMenuItem("跳转到代码位置")
        navigateToCodeItem.addActionListener {
            val selectedRow = table.selectedRow
            if (selectedRow >= 0) {
                val issue = tableModel.getIssueAt(selectedRow)
                navigateToCodeLocation(issue)
            }
        }
        popup.add(navigateToCodeItem)
        
        // 添加编辑菜单项
        val editItem = JMenuItem("编辑问题")
        editItem.addActionListener {
            val selectedRow = table.selectedRow
            if (selectedRow >= 0) {
                val issue = tableModel.getIssueAt(selectedRow)
                // 以编辑模式打开CreateIssueDialog
                val editDialog = CreateIssueDialog(project, null, issue, true)
                if (editDialog.showAndGet()) {
                    // 编辑后刷新问题列表
                    loadIssues(false)
                }
            }
        }
        popup.add(editItem)
        
        // 添加分隔线
        popup.addSeparator()
        
        // 添加改变状态子菜单
        val changeStatusMenu = JMenu("更改状态")
        
        // 使用更完整的状态选项列表
        val statusOptions = listOf(
            "待处理" to "open",
            "处理中" to "in_progress",
            "已解决" to "resolved",
            "已验证" to "verified",
            "已关闭" to "closed",
            "已拒绝" to "rejected"
        )
        
        statusOptions.forEach { (displayText, statusCode) ->
            val statusItem = JMenuItem(displayText)
            statusItem.addActionListener {
                val selectedRow = table.selectedRow
                if (selectedRow >= 0) {
                    val issue = tableModel.getIssueAt(selectedRow)
                    // 直接调用后端API更新状态
                    updateIssueStatusInBackend(issue.id, statusCode)
                }
            }
            changeStatusMenu.add(statusItem)
        }
        
        popup.add(changeStatusMenu)
        
        // 添加改变指派人子菜单
        val changeAssigneeMenu = JMenu("更改指派人")
        
        // 定义更新指派人菜单项的函数
        val updateAssigneeMenuItems = object {
            fun update() {
                changeAssigneeMenu.removeAll()
                
                // 添加"未指派"选项
                val unassignedItem = JMenuItem("未指派")
                unassignedItem.addActionListener {
                    val selectedRow = table.selectedRow
                    if (selectedRow >= 0) {
                        val issue = tableModel.getIssueAt(selectedRow)
                        // 直接更新为未指派
                        updateAssigneeDirectly(issue.id, null, null)
                    }
                }
                changeAssigneeMenu.add(unassignedItem)
                
                // 获取当前选中的项目
                val selectedProject = projectCombo.selectedItem as? ApiModels.ProjectInfo
                if (selectedProject != null && selectedProject.id > 0) {
                    // 获取项目成员
                    val members = getProjectMembers(selectedProject.id)
                    if (members.isNotEmpty()) {
                        // 添加分隔线
                        changeAssigneeMenu.addSeparator()
                        
                        // 按用户名字母排序
                        val sortedMembers = members.sortedBy { it.username }
                        
                        // 添加项目成员
                        sortedMembers.forEach { member ->
                            val memberItem = JMenuItem(member.username)
                            memberItem.addActionListener {
                                val selectedRow = table.selectedRow
                                if (selectedRow >= 0) {
                                    val issue = tableModel.getIssueAt(selectedRow)
                                    // 直接更新指派人
                                    updateAssigneeDirectly(issue.id, member.userId, member.username)
                                }
                            }
                            changeAssigneeMenu.add(memberItem)
                        }
            } else {
                        // 如果没有成员数据，添加加载项
                        val loadingItem = JMenuItem("加载项目成员中...")
                        loadingItem.isEnabled = false
                        changeAssigneeMenu.add(loadingItem)
                        
                        // 异步加载项目成员
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                                val loadedMembers = issueService.getProjectMembers(selectedProject.id, page = 1, pageSize = 100)
                // 更新缓存
                                projectMembersCache[selectedProject.id] = loadedMembers
                                
                                // 创建唯一用户列表
                                val uniqueUsers = mutableMapOf<Int, ApiModels.UserInfo>()
                                loadedMembers.forEach { member ->
                                    if (!uniqueUsers.containsKey(member.userId)) {
                                        uniqueUsers[member.userId] = ApiModels.UserInfo(
                                            id = member.userId,
                                            username = member.username,
                                            email = null,
                                            roles = listOf(ApiModels.UserInfo.Role(name = member.roleName)),
                                            isActive = member.isActive
                                        )
                                    }
                                }
                                // 更新用户缓存
                                usersCache[selectedProject.id] = uniqueUsers.values.toList()
                                
                                // 在EDT线程中更新菜单
                SwingUtilities.invokeLater {
                                    update()
            }
        } catch (e: Exception) {
                                LOG.error("加载项目成员失败", e)
                SwingUtilities.invokeLater {
                                    changeAssigneeMenu.removeAll()
                                    val errorItem = JMenuItem("加载失败，请重试")
                                    errorItem.isEnabled = false
                                    changeAssigneeMenu.add(errorItem)
                                }
                            }
                        }
                    }
            } else {
                    // 如果没有选中项目，显示提示
                    val noProjectItem = JMenuItem("请先选择项目")
                    noProjectItem.isEnabled = false
                    changeAssigneeMenu.add(noProjectItem)
                }
            }
        }
        
        // 初始化指派人菜单
        changeAssigneeMenu.addMenuListener(object : javax.swing.event.MenuListener {
            override fun menuSelected(e: javax.swing.event.MenuEvent?) {
                // 菜单被选中时刷新内容
                updateAssigneeMenuItems.update()
            }
            
            override fun menuDeselected(e: javax.swing.event.MenuEvent?) {}
            
            override fun menuCanceled(e: javax.swing.event.MenuEvent?) {}
        })
        
        popup.add(changeAssigneeMenu)
        
        // 为表格添加右键菜单
        table.componentPopupMenu = popup
    }
    
    /**
     * 直接更新指派人
     */
    private fun updateAssigneeDirectly(issueId: Int, assigneeId: Int?, assigneeName: String?) {
        // 先更新本地模型
        tableModel.updateIssueAssignee(issueId, assigneeId, assigneeName)
        
        // 调用后端API
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                // 使用updateIssue方法更新指派人
                val updateData = mutableMapOf<String, Any?>()
                updateData["assignee_id"] = assigneeId
                
                val response = issueService.updateIssue(issueId, updateData)
                
                if (response) {
                    LOG.debug("成功更新问题指派人 ID=$issueId, 指派给=${assigneeName ?: "未指派"}")
                SwingUtilities.invokeLater {
                        // 刷新表格显示
                        loadIssues(false)
                        showInfoNotification("更新成功", "已将问题指派给${assigneeName ?: "未指派"}")
                    }
                } else {
                    LOG.error("更新指派人失败")
                    SwingUtilities.invokeLater {
                        showErrorNotification("更新失败", "服务器未能更新指派人，请稍后重试")
                    }
                }
            } catch (e: Exception) {
                LOG.error("更新指派人异常", e)
                SwingUtilities.invokeLater {
                    showErrorNotification("更新失败", "更新指派人时出错: ${e.message}")
                }
            }
        }
    }
    
    /**
     * 更新问题状态到后端
     */
    private fun updateIssueStatusInBackend(issueId: Int, status: String) {
        try {
            println("[DEBUG] 更新问题状态, 问题ID: $issueId, 状态: $status")
            
            // 调用后端API更新状态
            val updateResult = issueService.updateIssueField(issueId, "status", status)
            
            if (updateResult) {
                println("[DEBUG] 成功更新问题状态")
                
                // 更新表格中的状态
                tableModel.updateIssueStatus(issueId, status)
                
                // 展示更新成功通知
                com.intellij.notification.NotificationGroupManager.getInstance()
                    .getNotificationGroup("CodeReview")
                    .createNotification(
                        "状态已更新",
                        "问题 #$issueId 状态已更改为 ${reverseStatusMap[status] ?: status}",
                        com.intellij.notification.NotificationType.INFORMATION
                    )
                    .notify(project)
            } else {
                println("[ERROR] 更新问题状态失败")
                
                // 展示错误通知
                com.intellij.notification.NotificationGroupManager.getInstance()
                    .getNotificationGroup("CodeReview")
                    .createNotification(
                        "状态更新失败",
                        "无法更新问题 #$issueId 的状态，请检查网络连接或刷新列表",
                        com.intellij.notification.NotificationType.ERROR
                    )
                    .notify(project)
            }
        } catch (e: Exception) {
            println("[ERROR] 更新问题状态时出错: ${e.message}")
            e.printStackTrace()
            
            // 展示错误通知
            com.intellij.notification.NotificationGroupManager.getInstance()
                .getNotificationGroup("CodeReview")
                .createNotification(
                    "状态更新错误",
                    "更新问题 #$issueId 状态时发生错误: ${e.message}",
                    com.intellij.notification.NotificationType.ERROR
                )
                .notify(project)
        }
    }

    /**
     * 处理登出
     */
    private fun handleLogout() {
        if (!authService.isLoggedIn()) {
            return
        }
        
        // 清除项目成员缓存
        clearMembersCache()
        
        // 在后台线程中执行登出操作
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                authService.logout()
                
                // 更新UI
                SwingUtilities.invokeLater {
                    try {
                        updateUserInfoUI()
                        tableModel.updateIssues(emptyList())
                        
                        // 更新项目下拉框
                        projectCombo.removeAllItems()
                        projectCombo.addItem(ApiModels.ProjectInfo(
                            id = -1,
                            name = "请先登录",
                            description = "",
                            createdAt = "",
                            repositoryUrl = null,
                            repositoryType = null,
                            branch = null,
                            status = null,
                            memberCount = null,
                            creator = null
                        ))
                        projectCombo.isEnabled = false
                        
                        showInfoNotification("已退出登录", "用户已成功退出登录")
                    } catch (e: Exception) {
                        LOG.error("更新UI时出错", e)
                    }
                }
            } catch (e: Exception) {
                LOG.error("执行登出操作时出错", e)
                
                // 更新UI
                    SwingUtilities.invokeLater {
                    showErrorNotification("登出失败", e.message ?: "未知错误")
                }
            }
        }
    }

    /**
     * 保存用户选择的默认项目
     */
    private fun saveDefaultProject(selectedProject: ApiModels.ProjectInfo) {
        if (selectedProject.id > 0) {
            // 保存为默认项目
            val settings = CodeReviewSettings.getInstance()
            settings.setDefaultProject(selectedProject.id, selectedProject.name)
            println("[DEBUG] 已保存默认项目：${selectedProject.name} (ID: ${selectedProject.id})")
        } else {
            println("[DEBUG] 选择了无效项目，不保存为默认项目")
        }
    }

    /**
     * 清除项目成员缓存
     */
    fun clearMembersCache() {
        projectMembersCache.clear()
        usersCache.clear()
    }

    /**
     * 获取缓存的项目成员
     * @param projectId 项目ID
     * @return 项目成员列表
     */
    fun getProjectMembers(projectId: Int): List<ApiModels.ProjectMember> {
        return projectMembersCache[projectId] ?: emptyList()
    }
    
    /**
     * 获取缓存的项目用户
     * @param projectId 项目ID
     * @return 用户列表
     */
    fun getProjectUsers(projectId: Int): List<ApiModels.UserInfo> {
        return usersCache[projectId] ?: emptyList()
    }
    
    /**
     * 更新问题指派人
     */
    private fun updateIssueAssignee(issueId: Int, assigneeId: Int?, assigneeName: String?) {
        com.intellij.openapi.application.ApplicationManager.getApplication().executeOnPooledThread {
            try {
                val issueService = IssueService.getInstance(project)
                
                // 使用updateIssue方法更新指派人
                val updateData = mutableMapOf<String, Any?>()
                updateData["assignee_id"] = assigneeId
                
                val response = issueService.updateIssue(issueId, updateData)
                
                if (response) {
                    println("[INFO] 成功更新问题指派人 ID=$issueId, 指派给=${assigneeName ?: "未指派"}")
                    // 不再直接刷新整个列表，而是让表格模型自行更新单行数据
                } else {
                    println("[ERROR] 更新指派人失败")
                }
            } catch (e: Exception) {
                println("[ERROR] 更新指派人异常: ${e.message}")
                e.printStackTrace()
            }
        }
    }
    
    /**
     * 提交问题状态和指派人更改
     */
    private fun submitChanges(issue: ApiModels.IssueListItem) {
        try {
            // 从表格模型中获取当前的状态和指派人
            val currentStatus = tableModel.getIssueStatus(issue.id)
            val currentAssignee = tableModel.getIssueAssignee(issue.id)
            
            LOG.debug("提交更改 - 当前状态: $currentStatus, 原状态: ${issue.status}")
            LOG.debug("提交更改 - 当前指派人: ${currentAssignee?.id}, 原指派人: ${issue.assigneeId}")
            
            var hasChanges = false
            
            // 执行提交操作
            if (currentStatus != issue.status) {
                LOG.debug("提交状态更改: ${issue.id}, 从 ${issue.status} 到 $currentStatus")
                
                // 显示正在更新的提示
                showInfoNotification("正在更新", "正在更新状态，请稍候...")
                
                try {
                    // 使用专门的更新状态API
                    val success = issueService.updateIssueStatus(issue.id, currentStatus)
                    if (success) {
                        hasChanges = true
                        LOG.debug("状态更新成功: ${issue.id}")
                    } else {
                        LOG.error("状态更新API返回失败: ${issue.id}, 状态: $currentStatus")
                        showErrorNotification("状态更新失败", "服务器未能成功更新问题状态，请检查网络连接或联系管理员")
                        return
                    }
                } catch (e: Exception) {
                    LOG.error("状态更新异常: ${e.javaClass.simpleName}: ${e.message}", e)
                    showErrorNotification("状态更新失败", "更新状态时出错: ${e.message}")
                    return
                }
            }
            
            if (currentAssignee?.id != issue.assigneeId) {
                LOG.debug("提交指派人更改: ${issue.id}, 从 ${issue.assigneeId} 到 ${currentAssignee?.id}")
                
                // 如果之前有状态更新，就不需要再显示提示了
                if (!hasChanges) {
                    showInfoNotification("正在更新", "正在更新指派人，请稍候...")
                }
                
                try {
                    // 使用专门的updateIssue API更新指派人
                    val updateData = mutableMapOf<String, Any?>()
                    updateData["assignee_id"] = currentAssignee?.id
                    
                    LOG.debug("发送指派人更新请求: ${issue.id}, 指派人ID: ${currentAssignee?.id}")
                    val success = issueService.updateIssue(issue.id, updateData)
                    if (success) {
                        hasChanges = true
                        LOG.debug("指派人更新成功: ${issue.id}")
                } else {
                        LOG.error("指派人更新API返回失败: ${issue.id}, 指派人ID: ${currentAssignee?.id}")
                        showErrorNotification("指派人更新失败", "服务器未能成功更新问题指派人，请检查网络连接或联系管理员")
                        return
                    }
                } catch (e: Exception) {
                    LOG.error("指派人更新异常: ${e.javaClass.simpleName}: ${e.message}", e)
                    showErrorNotification("指派人更新失败", "更新指派人时出错: ${e.message}")
                    return
                }
            }
            
            // 显示提交成功提示
            if (hasChanges) {
                showInfoNotification("更新成功", "问题状态和指派人已更新")
                
                // 刷新问题列表以显示最新数据
                LOG.debug("开始刷新问题列表...")
                        loadIssues(false)
                } else {
                LOG.debug("没有检测到状态或指派人的变化，不提交更改")
                showInfoNotification("提示", "没有检测到更改")
                }
            } catch (e: Exception) {
            LOG.error("提交更改时出错: ${e.javaClass.simpleName}: ${e.message}", e)
            showErrorNotification("更新失败", "提交更改时出错: ${e.message}")
        }
    }

    /**
     * 初始化表格
     */
    private fun initTable() {
        // 确保table和tableModel不为空
        if (table == null || tableModel == null) {
            return
        }
        
        // 设置行高
        table.rowHeight = 32
        
        // 设置选择模式为单选
        table.selectionModel.selectionMode = ListSelectionModel.SINGLE_SELECTION
        
        // 设置交替行颜色
        (table as? JBTable)?.isStriped = true
        
        // 设置表格字体
        table.font = table.font.deriveFont(13f)
        
        // 设置表头字体为粗体
        val tableHeader = table.tableHeader
        tableHeader.font = tableHeader.font.deriveFont(Font.BOLD, 13f)
        
        // 自动调整列宽
        table.autoResizeMode = JTable.AUTO_RESIZE_SUBSEQUENT_COLUMNS
        
        // 设置每列默认宽度
        val columnModel = table.columnModel
        columnModel.getColumn(0).preferredWidth = 40  // ID列
        columnModel.getColumn(1).preferredWidth = 250 // 标题列
        columnModel.getColumn(2).preferredWidth = 120 // 项目列
        columnModel.getColumn(3).preferredWidth = 120 // 包路径列
        columnModel.getColumn(4).preferredWidth = 80  // 代码行列
        columnModel.getColumn(5).preferredWidth = 80  // 状态列
        columnModel.getColumn(6).preferredWidth = 60  // 类型列
        columnModel.getColumn(7).preferredWidth = 80  // 优先级列
        columnModel.getColumn(8).preferredWidth = 80  // 严重程度列
        columnModel.getColumn(9).preferredWidth = 80  // 指派人列
        columnModel.getColumn(10).preferredWidth = 80  // 创建人列
        columnModel.getColumn(11).preferredWidth = 80  // 创建时间列
        columnModel.getColumn(12).preferredWidth = 80  // 更新时间列
        
        // 设置状态列的渲染器
        columnModel.getColumn(5).cellRenderer = StatusCellRenderer()
        
        // 设置指派人列的渲染器
        columnModel.getColumn(9).cellRenderer = AssigneeCellRenderer()
        
        // 设置表格行选择监听器
        table.selectionModel.addListSelectionListener { e ->
            if (!e.valueIsAdjusting) {
                // 表格行选择发生变化
                val selectedRow = table.selectedRow
                if (selectedRow >= 0) {
                    // 有选中的行
                }
            }
        }
    }

    /**
     * 创建状态栏
     */
    private fun createStatusBar(): JComponent {
        val statusBar = JPanel(BorderLayout())
        statusBar.border = JBUI.Borders.empty(5)
        
        // 添加状态信息
        val statusLabel = JLabel("就绪")
        statusBar.add(statusLabel, BorderLayout.WEST)
        
        return statusBar
    }
    
    /**
     * 指派人单元格渲染器
     */
    private inner class AssigneeCellRenderer : DefaultTableCellRenderer() {
        override fun getTableCellRendererComponent(
            table: JTable?,
            value: Any?,
            isSelected: Boolean,
            hasFocus: Boolean,
            row: Int,
            column: Int
        ): Component {
            val comp = super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column)
            if (comp is JLabel && value != null) {
                comp.text = value.toString()
                comp.horizontalAlignment = JLabel.CENTER
                
                // 设置样式
                if (value.toString() == "未指派") {
                    comp.foreground = JBColor.GRAY
                }
            }
            return comp
        }
    }
    
    /**
     * 问题列表表格模型
     */
    private inner class IssueTableModel : AbstractTableModel() {
        private val columns = arrayOf(
            "ID", "标题", "项目", "包路径", "代码行", "状态", "类型", "优先级", "严重程度", "指派人", "创建人", "创建时间", "更新时间"
        )
        
        private var issues = listOf<ApiModels.IssueListItem>()
        
        fun updateIssues(issues: List<ApiModels.IssueListItem>) {
            this.issues = issues
            fireTableDataChanged()
        }
        
        // 清空表格数据
        fun clearData() {
            this.issues = emptyList()
            fireTableDataChanged()
        }
        
        fun getIssueAt(row: Int): ApiModels.IssueListItem {
            return issues[row]
        }
        
        // 获取指定问题的索引
        fun getIssueIndex(issueId: Int): Int {
            return issues.indexOfFirst { it.id == issueId }
        }
        
        // 更新指定问题的状态
        fun updateIssueStatus(issueId: Int, status: String) {
            val index = getIssueIndex(issueId)
            if (index >= 0) {
                issues = issues.toMutableList().apply {
                    this[index] = this[index].copy(status = status)
                }
                fireTableRowsUpdated(index, index)
            }
        }
        
        // 更新指定问题的指派人
        fun updateIssueAssignee(issueId: Int, assigneeId: Int?, assigneeName: String?) {
            val index = getIssueIndex(issueId)
            if (index >= 0) {
                issues = issues.toMutableList().apply {
                    this[index] = this[index].copy(
                        assigneeId = assigneeId,
                        assigneeName = assigneeName
                    )
                }
                fireTableRowsUpdated(index, index)
            }
        }
        
        /**
         * 获取问题当前状态
         */
        fun getIssueStatus(issueId: Int): String {
            val issue = issues.find { it.id == issueId } ?: return "open"
            return issue.status
        }
        
        /**
         * 获取问题当前指派人
         */
        fun getIssueAssignee(issueId: Int): ApiModels.UserInfo? {
            val issue = issues.find { it.id == issueId } ?: return null
            return issue.assigneeId?.let { 
                ApiModels.UserInfo(
                    id = it,
                    username = issue.assigneeName ?: "未知用户",
                            email = null,
                            roles = null
                )
            }
        }
        
        override fun getRowCount() = issues.size
        
        override fun getColumnCount() = columns.size
        
        override fun getColumnName(column: Int) = columns[column]
        
        override fun getValueAt(rowIndex: Int, columnIndex: Int): Any? {
            val issue = issues[rowIndex]
            return when (columnIndex) {
                0 -> issue.id
                1 -> issue.title
                2 -> issue.projectName
                3 -> issue.filePath ?: "" // 包路径列
                4 -> formatLineNumbers(issue.lineStart, issue.lineEnd) // 代码行列
                5 -> reverseStatusMap[issue.status] ?: issue.status
                6 -> reverseIssueTypeMap[issue.issueType] ?: issue.issueType
                7 -> reversePriorityMap[issue.priority] ?: issue.priority
                8 -> if (issue.severity != null) reverseSeverityMap[issue.severity] ?: issue.severity else ""
                9 -> issue.assigneeName ?: "未指派"
                10 -> issue.creatorName
                11 -> issue.createdAt
                12 -> issue.updatedAt ?: ""
                else -> null
        }
    }
    
    /**
         * 格式化行号显示
         */
        private fun formatLineNumbers(lineStart: Int?, lineEnd: Int?): String {
            return when {
                lineStart == null -> ""
                lineEnd == null || lineStart == lineEnd -> "第 $lineStart 行"
                else -> "第 $lineStart-$lineEnd 行"
            }
        }
        
        override fun getColumnClass(columnIndex: Int): Class<*> {
            return when (columnIndex) {
                0 -> java.lang.Integer::class.java
                else -> String::class.java
            }
        }
    }

    /**
     * 表格单元格渲染器
     */
    private inner class IssueTableCellRenderer : DefaultTableCellRenderer() {
        
        init {
            // 设置渲染器的基本属性
            horizontalAlignment = LEFT
            verticalAlignment = CENTER
            border = BorderFactory.createEmptyBorder(2, 8, 2, 8)
        }
        
        override fun getTableCellRendererComponent(
            table: JTable,
            value: Any?,
            isSelected: Boolean,
            hasFocus: Boolean,
            row: Int,
            column: Int
        ): Component {
            val c = super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column)
            c as JLabel
            
            // 重置字体样式
            c.font = UIUtil.getLabelFont() // 使用标准标签字体替代getTableFont
            
            // 清除背景颜色，使用默认选中色
            if (isSelected) {
                c.background = UIUtil.getTableSelectionBackground(true)
                c.foreground = UIUtil.getTableSelectionForeground(true)
            } else {
                c.background = if (row % 2 == 0) {
                UIUtil.getTableBackground()
                } else {
                    // 交替行背景色
                    UIUtil.getDecoratedRowColor()
                }
                c.foreground = UIUtil.getTableForeground()
            }
            
            // 根据列内容设置样式
            if (column == 1) { // 标题列
                // 标题使用蓝色且有下划线
                c.foreground = JBColor(0x2563EB, 0x3B82F6)
                c.font = c.font.deriveFont(Font.BOLD)
            } else if (column == 5) { // 状态列
                val status = value?.toString() ?: ""
                
                // 设置状态颜色
                when (status) {
                    "待处理" -> {
                        c.foreground = JBColor(0x6B7280, 0x9CA3AF) // 灰色
                    }
                    "处理中" -> {
                        c.foreground = JBColor(0x2563EB, 0x3B82F6) // 蓝色
                        c.font = c.font.deriveFont(Font.BOLD)
                    }
                    "已解决" -> {
                        c.foreground = JBColor(0x059669, 0x10B981) // 绿色
                        c.font = c.font.deriveFont(Font.BOLD)
                    }
                    "已验证" -> {
                        c.foreground = JBColor(0x7C3AED, 0x8B5CF6) // 紫色
                        c.font = c.font.deriveFont(Font.BOLD)
                    }
                    "已关闭" -> {
                        c.foreground = JBColor(0x1F2937, 0x6B7280) // 深灰色
                    }
                    "重新打开" -> {
                        c.foreground = JBColor(0xD97706, 0xF59E0B) // 橙色
                        c.font = c.font.deriveFont(Font.BOLD)
                    }
                    "已拒绝" -> {
                        c.foreground = JBColor(0xDC2626, 0xEF4444) // 红色
                    }
                }
            } else if (column == 7) { // 优先级列
                val priority = value?.toString() ?: ""
                
                // 设置优先级颜色
                when (priority) {
                    "低" -> {
                        c.foreground = JBColor(0x6B7280, 0x9CA3AF) // 灰色
                    }
                    "中" -> {
                        c.foreground = JBColor(0x2563EB, 0x3B82F6) // 蓝色
                    }
                    "高" -> {
                        c.foreground = JBColor(0xD97706, 0xF59E0B) // 橙色
                        c.font = c.font.deriveFont(Font.BOLD)
                    }
                    "紧急" -> {
                        c.foreground = JBColor(0xDC2626, 0xEF4444) // 红色
                        c.font = c.font.deriveFont(Font.BOLD)
                    }
                }
            } else if (column == 8) { // 严重程度列
                val severity = value?.toString() ?: ""
                
                // 设置严重程度颜色
                when (severity) {
                    "低" -> {
                        c.foreground = JBColor(0x6B7280, 0x9CA3AF) // 灰色
                    }
                    "中" -> {
                        c.foreground = JBColor(0x2563EB, 0x3B82F6) // 蓝色
                    }
                    "高" -> {
                        c.foreground = JBColor(0xD97706, 0xF59E0B) // 橙色
                        c.font = c.font.deriveFont(Font.BOLD)
                    }
                    "紧急" -> {
                        c.foreground = JBColor(0xDC2626, 0xEF4444) // 红色
                        c.font = c.font.deriveFont(Font.BOLD)
                    }
                }
            } else if (column == 3) { // 包路径列
                val filePath = value?.toString() ?: ""
                if (filePath.isNotEmpty()) {
                    c.foreground = JBColor(0x059669, 0x10B981) // 绿色
                    c.font = c.font.deriveFont(Font.ITALIC)
                }
            } else if (column == 4) { // 代码行列
                val lineInfo = value?.toString() ?: ""
                if (lineInfo.isNotEmpty()) {
                    c.foreground = JBColor(0xD97706, 0xF59E0B) // 橙色
                    c.font = c.font.deriveFont(Font.ITALIC)
                }
            }
            
            // 设置工具提示，在鼠标悬停时显示完整内容
            c.toolTipText = value?.toString()
            
            // 设置单元格边框
            c.border = JBUI.Borders.empty(2, 8)
            
            return c
        }
    }

    /**
     * 将包路径和行号转换回文件路径，并打开文件定位到对应行
     */
    private fun navigateToCodeLocation(issue: ApiModels.IssueListItem) {
        if (issue.filePath.isNullOrEmpty()) {
            showErrorNotification("跳转失败", "该问题没有关联代码位置")
            return
        }
        
        try {
            // 将包路径转换为文件路径格式
            val packagePath = issue.filePath
            
            // 拆分获取包名和类名
            val packageParts = packagePath.split(".")
            val packageName = packageParts.dropLast(1).joinToString(".")
            val className = packageParts.lastOrNull() ?: ""
            
            println("[DEBUG] 尝试定位文件，包路径: $packagePath")
            
            // 在项目中查找匹配的文件
            val projectBasePath = project.basePath
            if (projectBasePath == null) {
                showErrorNotification("跳转失败", "无法获取项目根路径")
                return
            }
            
            // 搜索可能的文件扩展名
            val possibleExtensions = listOf(".java", ".kt", ".scala", ".groovy", ".js", ".ts", ".py", ".c", ".cpp", ".h", ".cs")
            var virtualFile: com.intellij.openapi.vfs.VirtualFile? = null
            
            // 首先尝试在项目的源码目录中查找
            val sourceDirs = listOf(
                "src/main/java", 
                "src/main/kotlin", 
                "src", 
                "lib", 
                "app", 
                "source"
            )
            
            // 通过查找构建正确的路径
            val packageAsPath = packageName.replace('.', '/')
            
            for (sourceDir in sourceDirs) {
                for (ext in possibleExtensions) {
                    // 检查项目根目录 + 源码目录 + 包路径 + 类名 + 扩展名的组合
                    val filePath = "$projectBasePath/$sourceDir/$packageAsPath/$className$ext"
                    val file = java.io.File(filePath)
                    if (file.exists()) {
                        virtualFile = com.intellij.openapi.vfs.LocalFileSystem.getInstance().findFileByIoFile(file)
                        if (virtualFile != null) {
                            break
                        }
                    }
                }
                if (virtualFile != null) break
            }
            
            // 如果没有找到文件，尝试通过项目索引搜索
            if (virtualFile == null) {
                val scope = com.intellij.psi.search.GlobalSearchScope.projectScope(project)
                
                // 使用FileTypeIndex查找文件，而不是FileBasedIndex.getFilesByName
                val javaFiles = com.intellij.psi.search.FilenameIndex.getFilesByName(
                    project,
                    "$className.java", 
                    scope
                )
                
                val kotlinFiles = com.intellij.psi.search.FilenameIndex.getFilesByName(
                    project,
                    "$className.kt", 
                    scope
                )
                
                if (javaFiles.isNotEmpty()) {
                    virtualFile = javaFiles[0].virtualFile
                } else if (kotlinFiles.isNotEmpty()) {
                    virtualFile = kotlinFiles[0].virtualFile
                }
            }
            
            // 如果找到了文件，打开并定位到指定行
            if (virtualFile != null && virtualFile.isValid) {
                println("[DEBUG] 找到文件: ${virtualFile.path}")
                
                // 打开文件并定位到行
                com.intellij.openapi.application.ApplicationManager.getApplication().invokeLater {
                    val fileEditor = com.intellij.openapi.fileEditor.FileEditorManager.getInstance(project)
                        .openFile(virtualFile, true, true).firstOrNull()
                    
                    if (fileEditor is com.intellij.openapi.editor.Editor) {
                        // 如果有行号，定位到指定行
                        if (issue.lineStart != null && issue.lineStart > 0) {
                            val document = fileEditor.document
                            val lineNumber = issue.lineStart - 1 // 转为0-based索引
                            if (lineNumber >= 0 && lineNumber < document.lineCount) {
                                val offset = document.getLineStartOffset(lineNumber)
                                fileEditor.caretModel.moveToOffset(offset)
                                fileEditor.scrollingModel.scrollToCaret(com.intellij.openapi.editor.ScrollType.CENTER)
                                
                                // 高亮行
                                if (issue.lineEnd != null && issue.lineEnd > issue.lineStart) {
                                    val endLineNumber = issue.lineEnd - 1
                                    val endOffset = document.getLineEndOffset(endLineNumber)
                                    fileEditor.selectionModel.setSelection(offset, endOffset)
                                }
                            }
                        }
                    }
                }
            } else {
                // 如果找不到文件，提示用户
                showErrorNotification("跳转失败", "在项目中找不到文件: $packagePath")
            }
        } catch (e: Exception) {
            println("[ERROR] 打开文件时出错: ${e.message}")
            e.printStackTrace()
            showErrorNotification("跳转失败", "打开文件时出错: ${e.message}")
        }
    }
} 