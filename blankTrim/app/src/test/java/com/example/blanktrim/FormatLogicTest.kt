package com.example.blanktrim

import org.junit.Assert.*
import org.junit.Test
import java.nio.charset.Charset

/**
 * 格式化逻辑单元测试。
 * 使用从《奥德赛》epub 中提取的真实内容进行验证。
 */
class FormatLogicTest {

    private val gbk = Charset.forName("GBK")

    // ========== formatText 基础测试 ==========

    @Test
    fun `替换连续目标字符为中文逗号`() {
        assertEquals("Hello，World，Test，End，",
            MainActivity.formatText("Hello~World！Test!End…"))
    }

    @Test
    fun `多个目标字符合并为一个逗号`() {
        assertEquals("A，B，C，D，E，F",
            MainActivity.formatText("A~~~B！！C!!D……E~~！…F"))
    }

    @Test
    fun `移除ASCII空白字符`() {
        assertEquals("HelloWorldTestEndDone",
            MainActivity.formatText("Hello  World\tTest\nEnd\r\nDone"))
    }

    @Test
    fun `移除全角空格U3000`() {
        assertEquals("这是段落的开头",
            MainActivity.formatText("　　这是段落的开头"))
    }

    @Test
    fun `移除不间断空格U00A0`() {
        assertEquals("HelloWorld",
            MainActivity.formatText("Hello  World"))
    }

    @Test
    fun `同时处理目标字符和各种空白`() {
        assertEquals("你好，世界你好，测试，结束",
            MainActivity.formatText("你好~~　　世界  \n  你好！!!!测试…结束"))
    }

    @Test
    fun `空字符串不变`() {
        assertEquals("", MainActivity.formatText(""))
    }

    @Test
    fun `纯ASCII空白字符变成空字符串`() {
        assertEquals("", MainActivity.formatText("  \t\n\r\n  "))
    }

    // ========== 编码检测：detectEncoding ==========

    @Test
    fun `检测 UTF-8 无BOM`() {
        val bytes = "你好世界Hello".toByteArray(Charsets.UTF_8)
        assertEquals(Charsets.UTF_8, MainActivity.detectEncoding(bytes))
    }

    @Test
    fun `检测 UTF-8 带BOM`() {
        val bytes = byteArrayOf(0xEF.toByte(), 0xBB.toByte(), 0xBF.toByte()) +
            "你好世界".toByteArray(Charsets.UTF_8)
        assertEquals(Charsets.UTF_8, MainActivity.detectEncoding(bytes))
    }

    @Test
    fun `检测 GBK 编码`() {
        // 用一段足够长的中文，确保 CJK 计数能超过误解码
        val text = "第一章　天地玄黄宇宙洪荒日月盈昃辰宿列张寒来暑往秋收冬藏"
        val bytes = text.toByteArray(gbk)
        val detected = MainActivity.detectEncoding(bytes)
        assertEquals("应为 GBK 但检测为 $detected", gbk, detected)
    }

    @Test
    fun `检测 GBK 编码——短文本`() {
        // 短文本也能正确检测
        val text = "天地玄黄宇宙洪荒"
        val bytes = text.toByteArray(gbk)
        assertEquals(gbk, MainActivity.detectEncoding(bytes))
    }

    @Test
    fun `检测 UTF-16 LE 带BOM`() {
        val bytes = byteArrayOf(0xFF.toByte(), 0xFE.toByte()) +
            "你好世界".toByteArray(Charsets.UTF_16LE)
        assertEquals(Charsets.UTF_16LE, MainActivity.detectEncoding(bytes))
    }

    @Test
    fun `检测 UTF-16 BE 带BOM`() {
        val bytes = byteArrayOf(0xFE.toByte(), 0xFF.toByte()) +
            "你好世界".toByteArray(Charsets.UTF_16BE)
        assertEquals(Charsets.UTF_16BE, MainActivity.detectEncoding(bytes))
    }

    @Test
    fun `纯ASCII检测为UTF-8`() {
        val bytes = "Hello World 12345".toByteArray(Charsets.UTF_8)
        assertEquals(Charsets.UTF_8, MainActivity.detectEncoding(bytes))
    }

    // ========== 编码检测：decodeBytes（BOM 剥离） ==========

    @Test
    fun `UTF-8 BOM 解码时剥离`() {
        val text = "你好世界"
        val bytes = byteArrayOf(0xEF.toByte(), 0xBB.toByte(), 0xBF.toByte()) +
            text.toByteArray(Charsets.UTF_8)
        assertEquals(text, MainActivity.decodeBytes(bytes))
    }

    @Test
    fun `GBK 解码后文本正确`() {
        val text = "第一章　天地玄黄宇宙洪荒"
        val bytes = text.toByteArray(gbk)
        assertEquals(text, MainActivity.decodeBytes(bytes))
    }

    // ========== 完整流程：编码往返测试 ==========

    @Test
    fun `GBK 编码文件——完整处理流程`() {
        // 模拟真实场景：GBK 编码的文件 → 检测 → 解码 → 格式化 → 用 GBK 写回
        val original = "第一章~~　　测试！介绍…背景\n\n第二章　开始\r\n内容"
        val rawBytes = original.toByteArray(gbk)

        // Step 1: 检测编码
        val detected = MainActivity.detectEncoding(rawBytes)
        assertEquals(gbk, detected)

        // Step 2: 解码
        val decoded = String(rawBytes, detected)
        assertEquals(original, decoded)

        // Step 3: 格式化
        val formatted = MainActivity.formatText(decoded)

        // Step 4: 用检测到的编码写回
        val outputBytes = formatted.toByteArray(detected)

        // Step 5: 重新读取验证
        val reread = String(outputBytes, detected)
        assertEquals(formatted, reread)

        // 验证格式化正确
        assertFalse(reread.contains(Regex("[~！!…]")))
        assertFalse(reread.contains(Regex("[\\s\\p{Z}]")))
    }

    @Test
    fun `UTF-8 编码文件——完整处理流程`() {
        val original = "第一章~~　　测试！介绍…背景\n\n第二章　开始\r\n内容"
        val rawBytes = original.toByteArray(Charsets.UTF_8)

        val detected = MainActivity.detectEncoding(rawBytes)
        assertEquals(Charsets.UTF_8, detected)

        val decoded = String(rawBytes, detected)
        val formatted = MainActivity.formatText(decoded)
        val outputBytes = formatted.toByteArray(detected)
        val reread = String(outputBytes, detected)

        assertFalse(reread.contains(Regex("[~！!…]")))
        assertFalse(reread.contains(Regex("[\\s\\p{Z}]")))
    }

    // ========== epub 真实内容测试 ==========

    @Test
    fun `epub真实内容格式化后不含目标字符`() {
        val input = javaClass.getResourceAsStream("/test_sample.xhtml")
            ?.bufferedReader(Charsets.UTF_8)
            ?.readText()
            ?: throw IllegalStateException("无法加载测试资源 test_sample.xhtml")

        val result = MainActivity.formatText(input)
        val hasTarget = result.contains(Regex("[~！!…]"))
        assertFalse("格式化后仍存在目标字符", hasTarget)
    }

    @Test
    fun `epub真实内容格式化后不含任何类型空白字符`() {
        val input = javaClass.getResourceAsStream("/test_sample.xhtml")
            ?.bufferedReader(Charsets.UTF_8)
            ?.readText()
            ?: throw IllegalStateException("无法加载测试资源 test_sample.xhtml")

        val result = MainActivity.formatText(input)
        val hasWhitespace = result.contains(Regex("[\\s\\p{Z}]"))
        assertFalse("格式化后仍存在空白字符", hasWhitespace)
    }

    // ========== 长文本压力测试：模拟真实文件处理管线 ==========

    @Test
    fun `50万字小说级管线测试——格式化后只有一行`() {
        // 模拟真实 50 万字中文小说，走完整管线：
        //   原始文本 → GBK 编码 → detectEncoding → decode → formatText
        //   → 用检测到的编码写回 → 重读 → 验证
        val gbk = Charset.forName("GBK")
        val paragraph = "第一章　天地玄黄宇宙洪荒日月盈昃辰宿列张寒来暑往秋收冬藏。" +
            "闰余成岁律吕调阳云腾致雨露结为霜金生丽水玉出昆冈~~测试！！"

        val sb = StringBuilder()
        // 段落之间插入各种换行符
        val lineBreaks = listOf("\r\n", "\n", "\r")
        var lineCount = 0
        var targetCount = 0
        var spaceCount = 0

        while (sb.length < 500_000) {
            sb.append(paragraph)
            // 每段插入一个目标字符和空白
            if (sb.length % 157 < paragraph.length) {
                sb.append('…')
                targetCount++
            }
            if (sb.length % 211 < paragraph.length) {
                sb.append("~！!")
                targetCount += 3
            }
            // 随机换行符
            sb.append(lineBreaks[lineCount % 3])
            lineCount++
            // 段首缩进（全角空格 + 普通空格）
            sb.append("　　  ")
            spaceCount += 4
        }

        val original = sb.toString()
        val originalLines = original.split(Regex("\\R")).size
        println("原文行数: $originalLines, 原文长度: ${original.length}")

        // === 完整管线：bytes → detect → decode → format → encode ===

        // Step 1: 以 GBK 编码为字节（模拟 GBK 编码的文件）
        val rawBytes = original.toByteArray(gbk)
        println("GBK 字节数: ${rawBytes.size}")

        // Step 2: 检测编码
        val detected = MainActivity.detectEncoding(rawBytes)
        assertEquals("应检测为 GBK", gbk, detected)

        // Step 3: 解码
        val decoded = String(rawBytes, detected)
        // 解码后不应有 � 替换字符
        val replacementChars = decoded.count { it == '�' }
        assertEquals("解码不应产生替换字符(�)", 0, replacementChars)

        // Step 4: 格式化
        val formatted = MainActivity.formatText(decoded)
        println("格式化后长度: ${formatted.length}")

        // Step 5: 用检测到的编码写回
        val outputBytes = formatted.toByteArray(detected)

        // Step 6: 重新读取验证
        val reread = String(outputBytes, detected)
        assertEquals("重读应与格式化结果一致", formatted, reread)

        // === 核心断言 ===
        // 1. 不应残留任何换行
        val remainingNewlines = reread.count { it == '\n' || it == '\r' }
        assertEquals("应无换行符残留, 但找到 $remainingNewlines 个", 0, remainingNewlines)

        // 2. 不应残留任何目标字符
        val remainingTargets = Regex("[~！!…]").findAll(reread).count()
        assertEquals("应无目标字符残留", 0, remainingTargets)

        // 3. 不应残留空白（包括全角空格）
        val remainingSpaces = Regex("[\\s\\p{Z}\\u0085\\u200B\\uFEFF]").findAll(reread).count()
        assertEquals("应无空白字符残留", 0, remainingSpaces)

        // 4. 不应该为空
        assertTrue("格式化后不应为空", reread.isNotEmpty())
        assertTrue("格式化后应更短", reread.length < original.length)

        println("✅ 50万字管线测试通过：${reread.take(50)}...")
    }

    @Test
    fun `UTF-8 50万字管线测试`() {
        val paragraph = "第一章　天地玄黄宇宙洪荒日月盈昃辰宿列张寒来暑往秋收冬藏。" +
            "闰余成岁律吕调阳云腾致雨露结为霜金生丽水玉出昆冈~~测试！！"

        val sb = StringBuilder()
        val lineBreaks = listOf("\r\n", "\n", "\r")
        var i = 0
        while (sb.length < 500_000) {
            sb.append(paragraph)
            if (sb.length % 157 < paragraph.length) sb.append('…')
            sb.append(lineBreaks[i++ % 3])
            sb.append("　　  ")
        }

        val original = sb.toString()
        val rawBytes = original.toByteArray(Charsets.UTF_8)

        // 完整管线
        val detected = MainActivity.detectEncoding(rawBytes)
        assertEquals(Charsets.UTF_8, detected)

        val decoded = String(rawBytes, detected)
        val formatted = MainActivity.formatText(decoded)
        val outputBytes = formatted.toByteArray(detected)
        val reread = String(outputBytes, detected)

        assertEquals("应无换行符", 0, reread.count { it == '\n' || it == '\r' })
        assertEquals("应无目标字符", 0, Regex("[~！!…]").findAll(reread).count())
        assertEquals("应无空白", 0, Regex("[\\s\\p{Z}\\u0085\\u200B\\uFEFF]").findAll(reread).count())
        assertTrue("不应为空", reread.isNotEmpty())
    }

    // ========== isZipFile 测试 ==========

    @Test
    fun `ZIP魔数识别为ZIP文件`() {
        assertTrue(MainActivity.isZipFile(byteArrayOf(0x50, 0x4B, 0x03, 0x04)))
    }

    @Test
    fun `纯文本不被识别为ZIP文件`() {
        assertFalse(MainActivity.isZipFile("Hello".toByteArray()))
    }

    // ========== isTextEntry 测试 ==========

    @Test
    fun `XHTML识别为文本条目`() {
        assertTrue(MainActivity.isTextEntry("OEBPS/Text/part0003.xhtml"))
    }

    @Test
    fun `图片不识别为文本条目`() {
        assertFalse(MainActivity.isTextEntry("cover.jpeg"))
    }
}
