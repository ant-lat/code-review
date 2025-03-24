package com.ant.code.coderplugin.lifecycle

import com.intellij.openapi.Disposable
import com.intellij.openapi.project.Project
import com.intellij.openapi.startup.StartupActivity
import com.intellij.openapi.util.Disposer
import com.intellij.util.messages.MessageBusConnection
import com.intellij.ide.AppLifecycleListener
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.project.ProjectCloseListener
import com.intellij.ide.plugins.DynamicPluginListener
import com.intellij.ide.plugins.IdeaPluginDescriptor
import com.intellij.ide.plugins.PluginManagerCore
import com.intellij.openapi.extensions.PluginId
import com.intellij.openapi.diagnostic.Logger
import java.util.concurrent.atomic.AtomicBoolean

/**
 * 插件生命周期管理器
 * 使用现代的方式管理插件资源，替代已废弃的ProjectComponent
 */
class PluginLifecycleManager : StartupActivity.DumbAware {
    private val LOG = Logger.getInstance(PluginLifecycleManager::class.java)
    private val isInitialized = AtomicBoolean(false)
    
    // 保存当前活动的资源管理器实例，确保它们在应用关闭时能被正确清理
    companion object {
        private val managersMap = HashMap<Project, ResourceManager>()
        private val pluginId = PluginId.getId("com.ant.code.code-r-plugin")
        private var appConnection: MessageBusConnection? = null
        private val cleaningUp = AtomicBoolean(false)
        private val LOG = Logger.getInstance(PluginLifecycleManager::class.java)
        
        fun cleanup() {
            if (cleaningUp.getAndSet(true)) {
                return // 防止重复清理
            }
            
            try {
                LOG.info("清理所有活动的Code-Review-Plugin资源管理器...")
                
                // 断开应用级别的连接
                try {
                    appConnection?.disconnect()
                    appConnection = null
                } catch (e: Exception) {
                    LOG.warn("断开应用级连接时出错", e)
                }
                
                // 复制一份再清理，避免并发修改异常
                val managers = HashMap(managersMap)
                managersMap.clear()
                
                // 释放所有资源管理器
                managers.values.forEach { 
                    try {
                        if (!Disposer.isDisposed(it)) {
                            Disposer.dispose(it)
                        }
                    } catch (e: Exception) {
                        LOG.error("清理资源管理器时出错", e)
                    }
                }
                
                // 手动调用系统GC
                System.gc()
                
                LOG.info("Code-Review-Plugin资源清理完成")
            } finally {
                cleaningUp.set(false)
            }
        }
    }
    
    override fun runActivity(project: Project) {
        if (project.isDisposed) return
        
        try {
            LOG.info("Code-Review-Plugin 生命周期管理器初始化...")
            
            // 确保全局初始化只进行一次
            if (isInitialized.compareAndSet(false, true)) {
                setupApplicationListeners()
            }
            
            // 为此项目创建资源管理器
            synchronized(managersMap) {
                if (!managersMap.containsKey(project) && !project.isDisposed) {
                    val resourceManager = ResourceManager(project)
                    managersMap[project] = resourceManager
                    Disposer.register(project, resourceManager)
                }
            }
            
            // 注册项目关闭处理逻辑
            val projectConnection = project.messageBus.connect()
            projectConnection.subscribe(ProjectCloseListener.TOPIC, object : ProjectCloseListener {
                override fun projectClosing(closingProject: Project) {
                    if (project == closingProject) {
                        LOG.info("项目即将关闭，释放项目关联资源: ${project.name}")
                        
                        try {
                            projectConnection.disconnect()
                        } catch (e: Exception) {
                            LOG.warn("断开项目连接时出错", e)
                        }
                        
                        synchronized(managersMap) {
                            val manager = managersMap.remove(project)
                            if (manager != null && !Disposer.isDisposed(manager)) {
                                Disposer.dispose(manager)
                            }
                        }
                    }
                }
            })
            
            LOG.info("Code-Review-Plugin 生命周期管理器初始化完成: ${project.name}")
        } catch (e: Exception) {
            LOG.error("初始化插件生命周期管理器时出错", e)
        }
    }
    
    private fun setupApplicationListeners() {
        // 只设置一次应用级别的监听器
        if (appConnection != null) return
        
        try {
            appConnection = ApplicationManager.getApplication().messageBus.connect()
            
            // 监听应用关闭事件
            appConnection?.subscribe(AppLifecycleListener.TOPIC, object : AppLifecycleListener {
                override fun appWillBeClosed(isRestart: Boolean) {
                    LOG.info("应用即将关闭，释放Code-Review-Plugin所有资源...")
                    cleanup()
                }
            })
            
            // 监听插件卸载事件
            appConnection?.subscribe(DynamicPluginListener.TOPIC, object : DynamicPluginListener {
                override fun beforePluginUnload(pluginDescriptor: IdeaPluginDescriptor, isUpdate: Boolean) {
                    if (pluginDescriptor.pluginId == pluginId) {
                        LOG.info("插件即将卸载，释放所有资源...")
                        cleanup()
                    }
                }
                
                override fun pluginUnloaded(pluginDescriptor: IdeaPluginDescriptor, isUpdate: Boolean) {
                    // 这里故意留空，避免在处理过程中遇到问题
                }
            })
            
            LOG.info("应用级监听器设置完成")
        } catch (e: Exception) {
            LOG.error("设置应用级监听器时出错", e)
        }
    }
    
    /**
     * 资源管理器
     * 集中管理所有需要释放的资源
     */
    private class ResourceManager(private val project: Project) : Disposable {
        private val disposables = ArrayList<Disposable>()
        private val isDisposed = AtomicBoolean(false)
        private val LOG = Logger.getInstance(ResourceManager::class.java)
        
        init {
            LOG.info("Code-Review-Plugin 资源管理器初始化: ${project.name}")
            // 可以在这里添加需要管理的资源
        }
        
        override fun dispose() {
            if (isDisposed.getAndSet(true)) return
            
            LOG.info("开始释放Code-Review-Plugin项目资源: ${project.name}")
            try {
                // 复制列表再清理，避免并发修改
                val toDispose = ArrayList(disposables)
                disposables.clear()
                
                // 释放所有注册的资源
                toDispose.forEach { 
                    try {
                        if (!Disposer.isDisposed(it)) {
                            Disposer.dispose(it)
                        }
                    } catch (e: Exception) {
                        LOG.warn("释放资源时出错", e)
                    }
                }
                
                // 移除此管理器
                synchronized(managersMap) {
                    managersMap.remove(project)
                }
                
                LOG.info("Code-Review-Plugin项目资源已释放: ${project.name}")
            } catch (e: Exception) {
                LOG.error("释放资源管理器时出错", e)
            }
        }
        
        /**
         * 注册一个需要被管理的资源
         */
        fun registerDisposable(disposable: Disposable) {
            if (!isDisposed.get()) {
                disposables.add(disposable)
                Disposer.register(this, disposable)
            }
        }
    }
} 