package com.ant.code.coderplugin.settings

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.components.PersistentStateComponent
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.State
import com.intellij.openapi.components.Storage

/**
 * 应用设置状态类
 * 保存持久化的应用设置
 */
@Service
@State(
    name = "com.ant.code.coderplugin.settings.AppSettingsState",
    storages = [Storage("CodeReviewSettings.xml")]
)
class AppSettingsState : PersistentStateComponent<AppSettingsState.State> {
    /**
     * 设置状态数据类
     */
    class State {
        var apiUrl: String = System.getProperty("code.review.api.url", 
                             System.getenv("CODE_REVIEW_API_URL") ?: 
                             "http://localhost:8080/api/v1")
        var savedUsername: String = ""
        var savedPassword: String = ""
        var loggedInUsername: String = ""
    }

    private var myState = State()

    companion object {
        fun getInstance(): AppSettingsState = ApplicationManager.getApplication().getService(AppSettingsState::class.java)
    }

    override fun getState(): State = myState

    override fun loadState(state: State) {
        myState = state
    }

    /**
     * 获取API URL
     */
    fun getApiUrl(): String {
        return myState.apiUrl
    }

    /**
     * 设置API URL
     */
    fun setApiUrl(url: String) {
        myState.apiUrl = url
    }

    /**
     * 获取保存的用户名
     */
    var savedUsername: String
        get() = myState.savedUsername
        set(value) { myState.savedUsername = value }

    /**
     * 获取保存的密码 (只读，不应该从这里获取实际密码)
     */
    var savedPassword: String
        get() = myState.savedPassword
        private set(value) { myState.savedPassword = value }

    /**
     * 获取当前登录的用户名
     */
    var loggedInUsername: String
        get() = myState.loggedInUsername
        set(value) { myState.loggedInUsername = value }
} 