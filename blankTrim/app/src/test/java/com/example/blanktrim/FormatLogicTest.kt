package com.example.blanktrim

import org.junit.Assert.*
import org.junit.Test

/**
 * 格式化逻辑单元测试。
 * 使用从《奥德赛》epub 中提取的真实内容进行验证。
 */
class FormatLogicTest {

    // ========== formatText 基础测试 ==========

    @Test
    fun `替换连续目标字符为中文逗号`() {
        val input = "Hello~World！Test!End…"
        val result = MainActivity.formatText(input)
        assertEquals("Hello，World，Test，End，", result)
    }

    @Test
    fun `多个目标字符合并为一个逗号`() {
        val input = "A~~~B！！C!!D……E~~！…F"
        val result = MainActivity.formatText(input)
        assertEquals("A，B，C，D，E，F", result)
    }

    @Test
    fun `移除ASCII空白字符`() {
        val input = "Hello  World\tTest\nEnd\r\nDone"
        val result = MainActivity.formatText(input)
        assertEquals("HelloWorldTestEndDone", result)
    }

    @Test
    fun `移除全角空格U3000`() {
        // 中文排版常用的全角空格（　）用作段落缩进
        val input = "　　这是段落的开头"
        val result = MainActivity.formatText(input)
        assertEquals("这是段落的开头", result)
    }

    @Test
    fun `移除不间断空格U00A0`() {
        val input = "Hello  World"
        val result = MainActivity.formatText(input)
        assertEquals("HelloWorld", result)
    }

    @Test
    fun `移除Unicode行分隔符和段分隔符`() {
        val input = "Line1 Line2 Line3"
        val result = MainActivity.formatText(input)
        assertEquals("Line1Line2Line3", result)
    }

    @Test
    fun `混合所有类型的空白字符`() {
        // ASCII空格 + 全角空格 + 不间断空格 + tab + 换行 + 回车
        val input = "Hello　World x\t\nTest\r\n End"
        val result = MainActivity.formatText(input)
        assertEquals("HelloWorldxTestEnd", result)
    }

    @Test
    fun `同时处理目标字符和各种空白`() {
        val input = "你好~~　　世界  \n  你好！!!!测试…结束"
        val expected = "你好，世界你好，测试，结束"
        assertEquals(expected, MainActivity.formatText(input))
    }

    @Test
    fun `空字符串不变`() {
        assertEquals("", MainActivity.formatText(""))
    }

    @Test
    fun `纯ASCII空白字符变成空字符串`() {
        assertEquals("", MainActivity.formatText("  \t\n\r\n  "))
    }

    @Test
    fun `纯Unicode空白字符变成空字符串`() {
        assertEquals("", MainActivity.formatText("　　   "))
    }

    @Test
    fun `不需要替换的文本不变`() {
        val input = "纯中文文本没有任何特殊字符"
        assertEquals(input, MainActivity.formatText(input))
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

        // 必须同时检查 ASCII 空白和 Unicode 空白
        val hasWhitespace = result.contains(Regex("[\\s\\p{Z}]"))
        assertFalse("格式化后仍存在空白字符", hasWhitespace)
    }

    @Test
    fun `epub真实内容格式化后不含全角空格`() {
        val input = javaClass.getResourceAsStream("/test_sample.xhtml")
            ?.bufferedReader(Charsets.UTF_8)
            ?.readText()
            ?: throw IllegalStateException("无法加载测试资源 test_sample.xhtml")

        val result = MainActivity.formatText(input)

        assertFalse("格式化后仍存在全角空格（\\u3000）", result.contains('　'))
    }

    @Test
    fun `epub真实内容格式化前后长度变化合理`() {
        val input = javaClass.getResourceAsStream("/test_sample.xhtml")
            ?.bufferedReader(Charsets.UTF_8)
            ?.readText()
            ?: throw IllegalStateException("无法加载测试资源 test_sample.xhtml")

        val result = MainActivity.formatText(input)

        assertTrue("格式化后应更短: ${result.length} vs ${input.length}", result.length <= input.length)
        assertTrue("格式化后不应过短: ${result.length}", result.length > 10000)
    }

    // ========== isZipFile 测试 ==========

    @Test
    fun `ZIP魔数识别为ZIP文件`() {
        val zipMagic = byteArrayOf(0x50, 0x4B, 0x03, 0x04)
        assertTrue(MainActivity.isZipFile(zipMagic))
    }

    @Test
    fun `纯文本不被识别为ZIP文件`() {
        val textBytes = "Hello World".toByteArray(Charsets.UTF_8)
        assertFalse(MainActivity.isZipFile(textBytes))
    }

    @Test
    fun `短字节数组不被识别为ZIP文件`() {
        assertFalse(MainActivity.isZipFile(ByteArray(3)))
        assertFalse(MainActivity.isZipFile(ByteArray(0)))
    }

    @Test
    fun `XHTML文件不误识别为ZIP`() {
        val epubBytes = javaClass.getResourceAsStream("/test_sample.xhtml")
            ?.readBytes()
            ?: throw IllegalStateException("无法加载测试资源")
        assertFalse(MainActivity.isZipFile(epubBytes))
    }

    // ========== isTextEntry 测试 ==========

    @Test
    fun `XHTML文件识别为文本条目`() {
        assertTrue(MainActivity.isTextEntry("OEBPS/Text/part0003.xhtml"))
    }

    @Test
    fun `HTML文件识别为文本条目`() {
        assertTrue(MainActivity.isTextEntry("chapter.html"))
    }

    @Test
    fun `XML文件识别为文本条目`() {
        assertTrue(MainActivity.isTextEntry("content.opf"))
        assertTrue(MainActivity.isTextEntry("toc.ncx"))
    }

    @Test
    fun `图片文件不识别为文本条目`() {
        assertFalse(MainActivity.isTextEntry("cover.jpeg"))
        assertFalse(MainActivity.isTextEntry("image.png"))
    }

    @Test
    fun `CSS文件不识别为文本条目`() {
        assertFalse(MainActivity.isTextEntry("style.css"))
    }
}
