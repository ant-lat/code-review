package com.ant.code.coderplugin.listeners

import com.intellij.util.messages.Topic

/**
 * 登录状态监听器接口
 * 用于通知登录状态的变更
 */
interface LoginStatusListener {
    companion object {
        val TOPIC = Topic.create("Code Review Login Status", LoginStatusListener::class.java)
    }
    
    /**
     * 当用户登录成功时调用
     */
    fun onLogin() {
        // 默认空实现
    }
    
    /**
     * 当用户退出登录时调用
     */
    fun onLogout() {
        // 默认空实现
    }
} 