package com.ant.code.coderplugin.api

import java.lang.reflect.ParameterizedType
import java.lang.reflect.Type

/**
 * 用于处理泛型类型的序列化和反序列化
 */
abstract class TypeReference<T> {
    val type: Type
        get() = (this.javaClass.genericSuperclass as ParameterizedType).actualTypeArguments[0]
} 