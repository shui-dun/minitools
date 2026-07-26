# BlankTrim

极简安卓 App：选择 `.txt` / `.epub` 文件 → 自动格式化 → 静默覆盖原文件。

## 功能

- **零交互**：打开 App 自动弹出系统文件选择器，选完即处理，无需按钮或弹窗
- **静默覆盖**：格式化后直接覆盖原文件，不提示
- 自动识别文件类型：纯文本按字符串处理；epub 按 ZIP 容器处理（格式化内部 XHTML 文本文件后重打包）

### 格式化规则

1. 连续的 `~`、`！`、`!`、`…` 替换为中文逗号 `，`
2. 移除所有空白字符（ASCII 空格/制表符/换行符 + Unicode 全角空格/不间断空格/行段分隔符等）

---

## 从零开始：如何编译

### 第一步：安装 JDK 17+

```bash
java -version   # 确认已安装，版本 ≥ 17
```

如果没装，去 [Adoptium](https://adoptium.net/) 下载安装，选 Temurin 21 或 17。

### 第二步：安装 Android SDK 命令行工具

1. 下载 [Android SDK command-line tools](https://developer.android.com/studio#command-line-tools-only)（Windows 选 `commandlinetools-win-*_latest.zip`）
2. 解压到 `C:\Android\cmdline-tools\latest\`，确保 `C:\Android\cmdline-tools\latest\bin\sdkmanager.bat` 存在
3. 打开终端，安装需要的包：
   ```bash
   set ANDROID_HOME=C:\Android
   cd C:\Android\cmdline-tools\latest\bin
   sdkmanager --sdk_root=C:\Android "platforms;android-35" "build-tools;35.0.0" "platform-tools"
   ```
4. **永久设置环境变量**（可选但推荐）：
   ```
   setx ANDROID_HOME "C:\Android"
   ```

### 第三步：编译

```bash
# 克隆仓库
git clone <this-repo-url> blankTrim
cd blankTrim

# 设置 SDK 路径（如果上一步没设环境变量的话必须做）
echo sdk.dir=C\:\\Android > local.properties

# 编译
gradlew assembleDebug
```

APK 输出位置：`app/build/outputs/apk/debug/app-debug.apk`

> **关于 `gradlew`**：项目根目录下的 `gradlew`（Windows 上是 `gradlew.bat`）是 Gradle Wrapper 脚本。它依赖 `gradle/wrapper/gradle-wrapper.jar` 这个二进制文件——**这个文件必须提交到 Git**，没有它 `gradlew` 就不能工作。这是所有 Gradle 项目（无论 Java/Kotlin/Android）的标准做法，不是本项目的特殊情况。

### 运行测试

```bash
gradlew test
```

测试报告在 `app/build/reports/tests/testDebugUnitTest/index.html`。

---

## 安装到手机

**方式一：USB 连接**

```bash
# adb 在安装 Android SDK 时已通过 platform-tools 获得
adb install app\build\outputs\apk\debug\app-debug.apk
```

**方式二：直接传文件**

把 `app-debug.apk` 传到手机，用文件管理器点击安装（需在系统设置中允许"安装未知来源应用"）。

---

## 项目结构

```
blankTrim/
├── build.gradle.kts                 # 项目级 Gradle 配置
├── settings.gradle.kts              # 模块声明
├── gradle.properties                # Gradle 属性
├── local.properties                 # SDK 路径（本地文件，不提交 Git）
├── gradlew / gradlew.bat           # Gradle Wrapper 脚本
├── gradle/wrapper/
│   ├── gradle-wrapper.jar           # Wrapper JAR（必须提交！）
│   └── gradle-wrapper.properties
├── .gitignore
├── README.md
├── app/
│   ├── build.gradle.kts             # 模块级构建配置
│   └── src/
│       ├── main/
│       │   ├── AndroidManifest.xml   # 无额外权限（使用 SAF）
│       │   ├── java/com/example/blanktrim/
│       │   │   └── MainActivity.kt   # 唯一代码文件（~150 行）
│       │   └── res/values/
│       │       ├── strings.xml
│       │       └── themes.xml
│       └── test/
│           ├── java/com/example/blanktrim/
│           │   └── FormatLogicTest.kt # 25 个单元测试
│           └── resources/
│               └── test_sample.xhtml  # 测试素材（从 epub 提取）
└── test/
    └── resource/
        ├── test.txt                  # txt 测试文件
        └── 奥德赛.epub              # epub 测试文件
```

## 技术要点

- **纯 Android SDK**：零第三方依赖，无 AppCompat、无 Material 组件
- **SAF 文件访问**：通过系统 Storage Access Framework 读写，无需 `READ/WRITE_EXTERNAL_STORAGE` 权限
- **epub 处理**：epub 本质是 ZIP 容器，App 解压 → 格式化 `.xhtml/.html/.xml/.opf/.ncx` 文本条目 → 重新打包，图片等二进制条目原样保留
- **空白符覆盖范围**：`[\s\p{Z}]+`，同时覆盖 ASCII 空白和 Unicode 分隔符（全角空格 `　`、不间断空格 ` `、行/段分隔符等）
