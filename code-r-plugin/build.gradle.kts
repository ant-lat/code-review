plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "1.9.25"
    id("org.jetbrains.intellij") version "1.17.4"

}

group = "com.ant.code"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
}

dependencies {
    // 移除 com.intellij.modules.java，因为这已经在intellij.plugins中配置
    // implementation("com.intellij.modules.java")
    
    // 整合OkHttp依赖，使用统一版本
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    
    // 整合Jackson依赖，使用统一版本
    implementation("com.fasterxml.jackson.module:jackson-module-kotlin:2.15.3")
    implementation("com.fasterxml.jackson.core:jackson-databind:2.15.3")
    implementation("com.fasterxml.jackson.core:jackson-core:2.15.3")
    implementation("com.fasterxml.jackson.core:jackson-annotations:2.15.3")
    
    // Kotlin依赖
    implementation("org.jetbrains.kotlin:kotlin-reflect:1.9.25")
    implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.25")
    
    // 移除重复的依赖
    // implementation ("com.squareup.okhttp3:okhttp:4.9.3")  // 更新到4.x版本
    // implementation ("com.fasterxml.jackson.module:jackson-module-kotlin:2.13.0")
    
    // Git4idea依赖会通过intellij插件系统获取，不需要额外添加
}

// Configure Gradle IntelliJ Plugin
// Read more: https://plugins.jetbrains.com/docs/intellij/tools-gradle-intellij-plugin.html
intellij {
    version.set("2024.1.7")
    type.set("IC") // Target IDE Platform
    updateSinceUntilBuild.set(false)

    plugins.set(listOf(
        "Git4Idea",
        "com.intellij.java"
    ))
}

tasks {
    // Set the JVM compatibility versions
    withType<JavaCompile> {
        sourceCompatibility = "17"
        targetCompatibility = "17"
    }
    withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
        kotlinOptions {
            jvmTarget = "17"
            languageVersion = "1.9"
            apiVersion = "1.9"
            freeCompilerArgs = listOf(
                "-Xjvm-default=all",
                "-opt-in=kotlin.ExperimentalStdlibApi"
            )
        }
    }

    patchPluginXml {
        sinceBuild.set("241")
        untilBuild.set("243.*")
        changeNotes.set("""
            <h3>1.0.0</h3>
            <ul>
                <li>初始版本发布</li>
                <li>支持代码审查基本功能</li>
                <li>IDE内集成问题管理</li>
            </ul>
        """.trimIndent())
    }

    signPlugin {
        certificateChain.set(System.getenv("CERTIFICATE_CHAIN"))
        privateKey.set(System.getenv("PRIVATE_KEY"))
        password.set(System.getenv("PRIVATE_KEY_PASSWORD"))
    }

    publishPlugin {
        token.set(System.getenv("PUBLISH_TOKEN"))
        channels.set(listOf("default"))
//        connectionTimeout.set(300000)
    }

    buildPlugin {
        destinationDirectory.set(file("${project.buildDir}/dist"))
    }

    register<Copy>("prepareForRelease") {
        dependsOn("buildPlugin")
        
        from("${project.buildDir}/dist")
        into("${project.buildDir}/release")
        
        doLast {
            println("插件已打包并准备发布，位于: ${project.buildDir}/release")
            println("使用以下命令推送到插件仓库：")
            println("./gradlew publishPlugin")
        }
    }
}

tasks.register("setupPublishEnvironment") {
    doLast {
        println("请设置以下环境变量以发布插件：")
        println("PUBLISH_TOKEN - JetBrains Marketplace的令牌")
        println("CERTIFICATE_CHAIN - 证书链文件内容")
        println("PRIVATE_KEY - 私钥文件内容")
        println("PRIVATE_KEY_PASSWORD - 私钥密码")
        
        println("\n在Windows系统中，您可以使用以下命令设置环境变量：")
        println("set PUBLISH_TOKEN=your-token-here")
        
        println("\n在Linux/Mac系统中，您可以使用以下命令设置环境变量：")
        println("export PUBLISH_TOKEN=your-token-here")
    }
}
