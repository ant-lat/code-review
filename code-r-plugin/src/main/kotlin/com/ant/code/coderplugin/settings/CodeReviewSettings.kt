package com.ant.code.coderplugin.settings

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage
import com.intellij.util.xmlb.XmlSerializerUtil

/**
 * 代码检视设置
 * 保存插件全局设置，如服务器地址、默认项目等
 */
@Service
@State(
    name = "com.ant.code.coderplugin.settings.CodeReviewSettings",
    storages = [Storage("CodeReviewSettings.xml")]
)
class CodeReviewSettings : PersistentStateComponent<CodeReviewSettings> {
    
    var apiUrl: String = System.getProperty("code.review.api.url",
                         System.getenv("CODE_REVIEW_API_URL") ?: 
                         "http://localhost:8080/api")
    var defaultProjectId: Int = 0
    var defaultProjectName: String = ""
    
    /**
     * 设置默认项目
     */
    fun setDefaultProject(id: Int, name: String) {
        defaultProjectId = id
        defaultProjectName = name
    }
    
    /**
     * 检查是否有默认项目
     */
    fun hasDefaultProject(): Boolean {
        return defaultProjectId > 0
    }
    
    override fun getState(): CodeReviewSettings {
        return this
    }
    
    override fun loadState(state: CodeReviewSettings) {
        XmlSerializerUtil.copyBean(state, this)
    }
    
    companion object {
        fun getInstance(): CodeReviewSettings {
            return ApplicationManager.getApplication().getService(CodeReviewSettings::class.java)
        }
    }
} 