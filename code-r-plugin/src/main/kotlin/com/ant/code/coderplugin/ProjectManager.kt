package com.ant.code.coderplugin

import com.ant.code.coderplugin.api.ApiModels
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.project.Project
import java.io.File
import com.intellij.openapi.vfs.VfsUtil

/**
 * 项目管理器
 * 处理项目数据的本地缓存和持久化
 */
@Service(Service.Level.PROJECT)
class ProjectManager(private val project: Project) {
    private val objectMapper: ObjectMapper = jacksonObjectMapper()
    
    companion object {
        private const val PROJECTS_CACHE_FILENAME = "code_r_projects.json"
        
        /**
         * 获取ProjectManager实例
         */
        @JvmStatic
        fun getInstance(project: Project): ProjectManager = project.service<ProjectManager>()
    }
    
    /**
     * 获取项目缓存文件
     */
    private fun getProjectCacheFile(): File {
        val ideaDir = File(project.basePath, ".idea")
        if (!ideaDir.exists()) {
            ideaDir.mkdirs()
        }
        return File(ideaDir, PROJECTS_CACHE_FILENAME)
    }
    
    /**
     * 将项目列表保存到缓存
     * @param projects 要缓存的项目列表
     */
    fun saveProjectsToCache(projects: List<ApiModels.ProjectInfo>) {
        try {
            val cacheFile = getProjectCacheFile()
            println("[DEBUG] 保存项目列表到缓存: ${cacheFile.absolutePath}")
            
            // 将项目列表转换为JSON并保存到文件
            objectMapper.writeValue(cacheFile, projects)
            
            // 刷新虚拟文件系统，确保IntelliJ能够看到更新的文件
            VfsUtil.markDirtyAndRefresh(false, false, false, cacheFile)
            
            println("[DEBUG] 成功保存${projects.size}个项目到缓存")
        } catch (e: Exception) {
            println("[ERROR] 保存项目列表到缓存时出错: ${e.message}")
            e.printStackTrace()
        }
    }
    
    /**
     * 从缓存中读取项目列表
     * @return 缓存的项目列表，如果没有缓存则返回空列表
     */
    fun getProjectsFromCache(): List<ApiModels.ProjectInfo> {
        try {
            val cacheFile = getProjectCacheFile()
            if (!cacheFile.exists()) {
                println("[DEBUG] 项目缓存文件不存在: ${cacheFile.absolutePath}")
                return emptyList()
            }
            
            println("[DEBUG] 从缓存读取项目列表: ${cacheFile.absolutePath}")
            
            // 从文件读取JSON并转换为项目列表
            val projects: List<ApiModels.ProjectInfo> = objectMapper.readValue(cacheFile)
            
            println("[DEBUG] 成功从缓存读取${projects.size}个项目")
            return projects
        } catch (e: Exception) {
            println("[ERROR] 从缓存读取项目列表时出错: ${e.message}")
            e.printStackTrace()
            return emptyList()
        }
    }
    
    /**
     * 清除项目缓存
     */
    fun clearProjectsCache() {
        try {
            val cacheFile = getProjectCacheFile()
            if (cacheFile.exists()) {
                println("[DEBUG] 清除项目缓存: ${cacheFile.absolutePath}")
                cacheFile.delete()
                
                // 刷新虚拟文件系统
                VfsUtil.markDirtyAndRefresh(false, false, false, cacheFile.parentFile)
                
                println("[DEBUG] 项目缓存已清除")
            } else {
                println("[DEBUG] 项目缓存文件不存在，无需清除")
            }
        } catch (e: Exception) {
            println("[ERROR] 清除项目缓存时出错: ${e.message}")
            e.printStackTrace()
        }
    }
} 