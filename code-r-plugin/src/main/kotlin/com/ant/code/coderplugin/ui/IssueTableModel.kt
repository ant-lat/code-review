package com.ant.code.coderplugin.ui

import com.ant.code.coderplugin.api.ApiModels
import javax.swing.table.AbstractTableModel

class IssueTableModel : AbstractTableModel() {
    private val columnNames = arrayOf("ID", "标题", "状态", "优先级", "类型", "项目", "创建人", "创建时间")
    var issues: List<ApiModels.IssueListItem> = emptyList()

    // 添加clearData方法，清空表格数据并通知数据变化
    fun clearData() {
        issues = emptyList()
        fireTableDataChanged()
    }

    override fun getRowCount(): Int {
        return issues.size
    }

    override fun getColumnCount(): Int {
        return columnNames.size
    }

    override fun getColumnName(columnIndex: Int): String {
        return columnNames[columnIndex]
    }

    override fun getColumnClass(columnIndex: Int): Class<*> {
        return String::class.java
    }

    override fun getValueAt(rowIndex: Int, columnIndex: Int): Any {
        val issue = issues[rowIndex]
        return when (columnIndex) {
            0 -> issue.id
            1 -> issue.title
            2 -> issue.status
            3 -> issue.priority
            4 -> issue.issueType
            5 -> issue.projectName
            6 -> issue.creatorName
            7 -> issue.createdAt
            else -> throw IllegalArgumentException("Invalid column index")
        }
    }
} 