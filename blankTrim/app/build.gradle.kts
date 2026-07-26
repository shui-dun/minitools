plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.example.blanktrim"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.example.blanktrim"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    // Mozilla 编码自动检测（Firefox 同款算法，处理 GBK/UTF-8/Big5 等）
    implementation("com.googlecode.juniversalchardet:juniversalchardet:1.0.3")
    testImplementation("junit:junit:4.13.2")
}
