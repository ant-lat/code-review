package com.ant.code.coderplugin.action

import com.ant.code.coderplugin.service.AuthService
import com.ant.code.coderplugin.ui.LoginDialog
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import javax.swing.Icon

class LoginAction : AnAction() {
    // 添加getActionUpdateThread方法，指定使用EDT线程
    override fun getActionUpdateThread(): ActionUpdateThread {
        return ActionUpdateThread.EDT
    }
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        
        val authService = AuthService.getInstance(project)
        
        // 已登录则提示是否退出
        if (authService.isLoggedIn()) {
            val result = Messages.showYesNoDialog(
                project,
                "您已登录，是否要退出当前账号？",
                "已登录提示",
                "退出登录",
                "取消",
                Messages.getQuestionIcon()
            )
            
            if (result == Messages.YES) {
                authService.logout()
                Messages.showInfoMessage(project, "已成功退出登录", "退出登录")
            }
            
            return
        }
        
        // 显示登录对话框
        val loginDialog = LoginDialog(project)
        
        if (loginDialog.showAndGet()) {
            val user = authService.getCurrentUser()
            if (user != null) {
                Messages.showInfoMessage(
                    project,
                    "登录成功，欢迎 ${user.username}",
                    "登录成功"
                )
            }
        }
    }
    
    override fun update(e: AnActionEvent) {
        val project = e.project
        e.presentation.isEnabledAndVisible = project != null
        
        if (project != null) {
            val authService = AuthService.getInstance(project)
            if (authService.isLoggedIn()) {
                e.presentation.text = "退出登录"
            } else {
                e.presentation.text = "登录代码检视平台"
            }
        }
    }
} 