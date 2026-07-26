package com.example.blanktrim

import org.junit.Assert.*
import org.junit.Test
import java.nio.charset.Charset

class FormatLogicTest {

    private val gbk = Charset.forName("GBK")

    // ═════ ① 标点 → 逗号 ═════

    @Test
    fun `中文标点替换为逗号`() {
        assertEquals("你好，世界，测试，结束，",
            MainActivity.formatText("你好～世界？测试—结束……"))
    }

    @Test
    fun `英文标点替换为逗号`() {
        assertEquals("A，B，C，D，",
            MainActivity.formatText("A~B!C?D."))
    }

    @Test
    fun `连续不同标点只出一个逗号`() {
        assertEquals("你好，世界",
            MainActivity.formatText("你好～～！！？？…—世界"))
    }

    @Test
    fun `顿号替换为逗号`() {
        assertEquals("A，B，C",
            MainActivity.formatText("A、B、C"))
    }

    @Test
    fun `中文句号保留`() {
        val result = MainActivity.formatText("第一句。第二句。")
        assertTrue("句号应保留", result.contains("。"))
        assertEquals("第一句。第二句。", result)
    }

    @Test
    fun `引号括号变逗号`() {
        assertEquals("，你好，世界，",
            MainActivity.formatText("\"你好\"《世界》"))
    }

    // ═════ ② 无意义符号 → 删除 ═════

    @Test
    fun `广告符号删除`() {
        assertEquals("你好世界",
            MainActivity.formatText("你好-=-+*#@世界"))
    }

    @Test
    fun `下划线管道删除`() {
        assertEquals("HelloWorldTest",
            MainActivity.formatText("Hello_World|Test"))
    }

    // ═════ ③ 空白 → 删除 ═════

    @Test
    fun `ASCII空白删除`() {
        assertEquals("HelloWorldTestEndDone",
            MainActivity.formatText("Hello  World\tTest\nEnd\r\nDone"))
    }

    @Test
    fun `全角空格删除`() {
        assertEquals("这是段落的开头",
            MainActivity.formatText("　　这是段落的开头"))
    }

    // ═════ 综合 ═════

    @Test
    fun `三条规则同时工作`() {
        val input = "你好~~　　世界！\n测试-内容？广告==结束…"
        // ① ~~！？… → ，   ② - == → 直接删除   ③ 全角空格+换行 → 删除
        assertEquals("你好，世界，测试内容，广告结束，",
            MainActivity.formatText(input))
    }

    @Test
    fun `空字符串`() {
        assertEquals("", MainActivity.formatText(""))
    }

    @Test
    fun `纯空白清空`() {
        assertEquals("", MainActivity.formatText("  \t\n\r\n　　  "))
    }

    // ═════ 编码检测 ═════

    @Test
    fun `检测 UTF-8`() {
        val bytes = "你好世界Hello".toByteArray(Charsets.UTF_8)
        assertEquals(Charsets.UTF_8, MainActivity.detectEncoding(bytes))
    }

    @Test
    fun `检测 GBK`() {
        val bytes = "第一章　天地玄黄宇宙洪荒日月盈昃辰宿列张".toByteArray(gbk)
        assertEquals(gbk, MainActivity.detectEncoding(bytes))
    }

    @Test
    fun `BOM剥离`() {
        val text = "你好世界"
        val bytes = byteArrayOf(0xEF.toByte(), 0xBB.toByte(), 0xBF.toByte()) +
            text.toByteArray(Charsets.UTF_8)
        assertEquals(text, MainActivity.decodeBytes(bytes))
    }

    @Test
    fun `GBK解码正确`() {
        val text = "第一章　天地玄黄宇宙洪荒"
        assertEquals(text, MainActivity.decodeBytes(text.toByteArray(gbk)))
    }

    // ═════ 完整往返 ═════

    @Test
    fun `GBK完整流程`() {
        val original = "第一章~~　　测试！介绍…背景\r\n第二章　内容-广告"
        val bytes = original.toByteArray(gbk)
        val enc = MainActivity.detectEncoding(bytes)
        assertEquals(gbk, enc)

        val decoded = String(bytes, enc)
        val formatted = MainActivity.formatText(decoded)
        val output = formatted.toByteArray(enc)
        val reread = String(output, enc)

        assertFalse(reread.contains(Regex("[～~！!…?]")))
        assertFalse(reread.contains("-"))
        assertFalse(reread.contains(Regex("[\\s\\p{Z}]")))
        assertEquals(formatted, reread)
    }

    // ═════ epub ═════

    @Test
    fun `epub内容不含旧标点`() {
        val input = javaClass.getResourceAsStream("/test_sample.xhtml")
            ?.bufferedReader(Charsets.UTF_8)?.readText()
            ?: throw IllegalStateException("无法加载测试资源")
        assertFalse(MainActivity.formatText(input).contains(Regex("[~！!…]")))
    }

    // ═════ 50万字管线 ═════

    @Test
    fun `50万字小说管线——只剩逗号和句号`() {
        val para = "第一章　天地玄黄宇宙洪荒日月盈昃辰宿列张。" +
            "闰余成岁律吕调阳云腾致雨露结为霜~~测试！！"
        val sb = StringBuilder()
        val lbs = listOf("\r\n", "\n", "\r")
        var i = 0
        while (sb.length < 500_000) {
            sb.append(para)
            if (sb.length % 157 < para.length) sb.append("…—？")
            sb.append(lbs[i++ % 3])
            sb.append("　　  ")
            if (sb.length % 313 < 10) sb.append("-=-+*@")
        }

        val bytes = sb.toString().toByteArray(gbk)
        val enc = MainActivity.detectEncoding(bytes)
        assertEquals(gbk, enc)

        val decoded = String(bytes, enc)
        val formatted = MainActivity.formatText(decoded)
        val output = formatted.toByteArray(enc)
        val reread = String(output, enc)

        assertEquals("应无换行", 0, reread.count { it == '\n' || it == '\r' })
        assertEquals("残留旧标点",
            0, Regex("[～~！!？?…—：:；;．.、]").findAll(reread).count())
        assertEquals("残留广告符号",
            0, Regex("[\\-=\\+*#@_|]").findAll(reread).count())
        assertEquals("残留空白",
            0, Regex("[\\s\\p{Z}]").findAll(reread).count())
        assertTrue("句号应保留", reread.contains("。"))
        assertTrue("不应为空", reread.isNotEmpty())
    }

    // ═════ 辅助 ═════

    @Test
    fun `ZIP魔数`() {
        assertTrue(MainActivity.isZipFile(byteArrayOf(0x50, 0x4B, 0x03, 0x04)))
        assertFalse(MainActivity.isZipFile("Hello".toByteArray()))
    }

    @Test
    fun `文本条目`() {
        assertTrue(MainActivity.isTextEntry("OEBPS/Text/part0003.xhtml"))
        assertFalse(MainActivity.isTextEntry("cover.jpeg"))
    }
}
