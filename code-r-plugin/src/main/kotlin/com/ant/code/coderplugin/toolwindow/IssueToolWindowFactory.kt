package com.ant.code.coderplugin.toolwindow

import com.ant.code.coderplugin.ui.IssueListPanel
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory
import com.intellij.openapi.application.ModalityState
import com.intellij.openapi.Disposable
import com.intellij.openapi.util.Disposer
import com.intellij.openapi.diagnostic.Logger
import java.util.concurrent.atomic.AtomicBoolean

class IssueToolWindowFactory : ToolWindowFactory {
    private val LOG = Logger.getInstance(IssueToolWindowFactory::class.java)
    
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        if (project.isDisposed) return
        
        // 确保应用已完全初始化后再创建面板
        try {
            val application = ApplicationManager.getApplication()
            if (!application.isDisposed) {
                application.invokeLater({
                    if (project.isDisposed) return@invokeLater
                    
                    try {
                        val contentFactory = ContentFactory.getInstance()
                        // 使用延迟加载方式创建内容
                        val lazyPanel = LazyPanel(project)
                        val content = contentFactory.createContent(lazyPanel, "问题清单", false)
                        
                        // 注册content的释放机制
                        Disposer.register(content, lazyPanel)
                        
                        if (!project.isDisposed && !toolWindow.isDisposed) {
                            toolWindow.contentManager.addContent(content)
                        }
                    } catch (e: Exception) {
                        LOG.error("创建工具窗口内容时出错", e)
                    }
                }, ModalityState.nonModal())
            }
        } catch (e: Exception) {
            LOG.error("安排工具窗口创建时出错", e)
        }
    }
    
    override fun shouldBeAvailable(project: Project): Boolean {
        // 对所有项目都可用
        return true
    }
    
    // 延迟加载面板，只有在实际显示时才创建IssueListPanel
    private class LazyPanel(private val project: Project) : javax.swing.JPanel(java.awt.BorderLayout()), Disposable {
        private val LOG = Logger.getInstance(LazyPanel::class.java)
        private val initialized = AtomicBoolean(false)
        private val isDisposed = AtomicBoolean(false)
        private var panel: IssueListPanel? = null
        
        init {
            // 添加一个简单的加载信息
            add(javax.swing.JLabel("加载中..."), java.awt.BorderLayout.CENTER)
            
            // 注册到项目的生命周期
            Disposer.register(project, this)
            LOG.info("LazyPanel初始化")
        }
        
        override fun addNotify() {
            if (isDisposed.get()) {
                LOG.warn("尝试在已释放的面板上调用addNotify")
                return
            }
            
            super.addNotify()
            
            if (!initialized.getAndSet(true)) {
                // 在EDT线程中延迟初始化
                try {
                    val application = ApplicationManager.getApplication()
                    if (!application.isDisposed) {
                        application.invokeLater({
                            if (isDisposed.get() || project.isDisposed) return@invokeLater
                            
                            try {
                                // 移除加载信息
                                removeAll()
                                
                                // 创建实际面板
                                panel = IssueListPanel(project)
                                add(panel, java.awt.BorderLayout.CENTER)
                                
                                // 重新布局
                                revalidate()
                                repaint()
                                LOG.info("IssueListPanel创建成功")
                            } catch (e: Exception) {
                                LOG.error("创建IssueListPanel失败", e)
                                add(javax.swing.JLabel("加载失败: ${e.message}"), java.awt.BorderLayout.CENTER)
                            }
                        }, ModalityState.any())
                    }
                } catch (e: Exception) {
                    LOG.error("安排IssueListPanel初始化时出错", e)
                }
            }
        }
        
        override fun removeNotify() {
            if (isDisposed.get()) return
            
            try {
                super.removeNotify()
            } catch (e: Exception) {
                LOG.warn("调用removeNotify时出错", e)
            }
        }
        
        fun disposeResources() {
            if (isDisposed.getAndSet(true)) return
            
            try {
                LOG.info("开始释放LazyPanel资源")
                
                // 显式释放面板资源
                panel?.let {
                    try {
                        it.removeAll()
                        // 如果IssueListPanel实现了Disposable，则调用dispose
                        if (it is Disposable && !Disposer.isDisposed(it)) {
                            Disposer.dispose(it)
                        }
                    } catch (e: Exception) {
                        LOG.warn("释放IssueListPanel时出错", e)
                    }
                }
                panel = null
                
                // 清理其他资源
                try {
                    removeAll()
                } catch (e: Exception) {
                    LOG.warn("移除所有组件时出错", e)
                }
                
                LOG.info("LazyPanel资源已释放")
            } catch (e: Exception) {
                LOG.error("释放LazyPanel资源时出错", e)
            }
        }
        
        override fun dispose() {
            disposeResources()
        }
    }
} 