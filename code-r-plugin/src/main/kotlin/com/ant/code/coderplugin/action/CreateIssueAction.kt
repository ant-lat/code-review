package com.ant.code.coderplugin.action

import com.ant.code.coderplugin.api.ApiModels
import com.ant.code.coderplugin.service.AuthService
import com.ant.code.coderplugin.service.IssueService
import com.ant.code.coderplugin.ui.CreateIssueDialog
import com.ant.code.coderplugin.ui.LoginDialog
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.project.Project
import com.intellij.openapi.roots.ProjectFileIndex
import com.intellij.openapi.ui.Messages
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.psi.PsiDocumentManager
import com.intellij.psi.PsiFile
import com.intellij.psi.util.PsiTreeUtil
import com.intellij.openapi.util.TextRange
import com.intellij.vcs.log.VcsCommitMetadata
import git4idea.GitUtil
import git4idea.repo.GitRepository
import git4idea.history.GitHistoryUtils
import java.util.*

/**
 * 创建问题的Action类，用于在编辑器中右键菜单创建问题
 */
class CreateIssueAction : AnAction() {
    // 添加getActionUpdateThread方法，指定使用EDT线程
    override fun getActionUpdateThread(): ActionUpdateThread {
        return ActionUpdateThread.EDT
    }
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR)
        val psiFile = e.getData(CommonDataKeys.PSI_FILE)
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        
        // 添加调试日志
        println("[DEBUG] CreateIssueAction被触发")
        println("[DEBUG] project=$project, editor=$editor, psiFile=$psiFile, virtualFile=$virtualFile")
        
        val authService = AuthService.getInstance(project)
        val issueService = IssueService.getInstance(project)
        
        // 检查是否已登录
        if (!authService.isLoggedIn()) {
            val loginDialog = LoginDialog(project)
            if (!loginDialog.showAndGet() || !authService.isLoggedIn()) {
                Messages.showWarningDialog(
                    project,
                    "您需要先登录才能创建问题",
                    "需要登录"
                )
                return
            }
        }
        
        // 获取选中的代码
        var selectedText = ""
        var startLine = 1
        var endLine = 1
        var filePath = ""
        var className = ""
        
        if (editor != null && editor.selectionModel.hasSelection()) {
            selectedText = editor.selectionModel.selectedText ?: ""
            val startOffset = editor.selectionModel.selectionStart
            val endOffset = editor.selectionModel.selectionEnd
            val document = editor.document
            
            // 获取选中代码的行号范围
            startLine = document.getLineNumber(startOffset) + 1 // 转换为1-based行号
            endLine = document.getLineNumber(endOffset) + 1
        }
        
        // 获取文件信息
        if (psiFile != null) {
            className = psiFile.name
        }
        
        if (virtualFile != null) {
            filePath = getRelativePath(project, virtualFile)
            
            // 如果没有选中代码，则显示提示但允许继续
            if (selectedText.isEmpty()) {
                val result = Messages.showYesNoDialog(
                    project,
                    "您没有选择任何代码。是否继续创建问题？",
                    "未选择代码",
                    "继续",
                    "取消",
                    Messages.getQuestionIcon()
                )
                
                if (result != Messages.YES) {
                    return
                }
            }
            
            // 获取git提交信息
            val commitInfo = if (virtualFile != null) {
                getLastCommitInfo(project, virtualFile, startLine)
            } else null
            
            // 创建代码选择信息对象
            val codeSelectionInfo = ApiModels.CodeSelectionInfo(
                className = className,
                filePath = filePath,
                lineStart = startLine,
                lineEnd = endLine,
                selectedCode = selectedText,
                commitInfo = commitInfo
            )
            
            // 创建对话框
            val dialog = CreateIssueDialog(project, codeSelectionInfo)
            
            if (dialog.showAndGet()) {
                Messages.showInfoMessage(
                    project,
                    "问题创建成功",
                    "创建成功"
                )
            }
        } else {
            // 如果没有虚拟文件，创建一个没有代码选择的对话框
            val dialog = CreateIssueDialog(project)
            
            if (dialog.showAndGet()) {
                Messages.showInfoMessage(
                    project,
                    "问题创建成功",
                    "创建成功"
                )
            }
        }
    }
    
    override fun update(e: AnActionEvent) {
        // 始终启用此动作
        e.presentation.isEnabledAndVisible = e.project != null
    }

    // 获取文件的类名（修改为不依赖PsiMethod）
    private fun getClassName(psiFile: PsiFile, editor: Editor): String {
        // 简化实现，直接返回文件名
        return psiFile.name
    }

    // 获取文件相对于项目的路径
    private fun getRelativePath(project: Project, file: VirtualFile): String {
        val projectFileIndex = ProjectFileIndex.getInstance(project)
        val contentRoot = projectFileIndex.getContentRootForFile(file)
        val moduleName = projectFileIndex.getModuleForFile(file)?.name ?: ""

        return when {
            contentRoot != null -> {
                val relativePath = file.path.removePrefix(contentRoot.path)
                "${moduleName}${relativePath}"
            }
            else -> file.path
        }
    }

    // 获取最后一次提交信息
    private fun getLastCommitInfo(project: Project, file: VirtualFile, lineNumber: Int): ApiModels.CommitInfo? {
        try {
            // 获取Git仓库
            val repository = GitUtil.getRepositoryManager(project).getRepositoryForFile(file)
            if (repository == null) {
                println("[DEBUG] 未找到Git仓库")
                return null
            }

            // 使用history方法替代collectMetadata
            val history = GitHistoryUtils.history(
                project, 
                repository.root, 
                "--max-count=1", // 只获取最后一次提交
                file.path
            )
            
            if (history.isEmpty()) {
                println("[DEBUG] 未找到提交记录")
                return null
            }
            
            val lastCommit = history[0]
            
            return ApiModels.CommitInfo(
                author = lastCommit.author.name,
                date = formatDate(lastCommit.commitTime * 1000L), // 转换为毫秒
                message = lastCommit.fullMessage,
                hash = lastCommit.id.toShortString()
            )
        } catch (e: Exception) {
            println("[ERROR] 获取Git提交信息失败: ${e.message}")
            e.printStackTrace()
            return null
        }
    }
    
    // 格式化日期
    private fun formatDate(timestamp: Long): String {
        val date = Date(timestamp)
        return date.toString()
    }
} 