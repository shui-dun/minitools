package com.example.blanktrim

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import org.mozilla.universalchardet.UniversalDetector
import java.io.ByteArrayOutputStream
import java.nio.charset.Charset
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

class MainActivity : Activity() {

    private var pickerLaunched = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
    }

    override fun onResume() {
        super.onResume()
        if (!pickerLaunched) {
            pickerLaunched = true
            openFilePicker()
        }
    }

    /** 调用系统 SAF 文件选择器 */
    private fun openFilePicker() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
            putExtra(
                Intent.EXTRA_MIME_TYPES,
                arrayOf("text/plain", "application/epub+zip", "application/octet-stream")
            )
        }
        startActivityForResult(intent, REQUEST_CODE_PICK_FILE)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != REQUEST_CODE_PICK_FILE || resultCode != Activity.RESULT_OK) {
            finish()
            return
        }
        data?.data?.let { uri -> processFile(uri) } ?: finish()
    }

    /** 读取文件 → 格式化 → 覆盖写回 */
    private fun processFile(uri: Uri) {
        try {
            val rawBytes = contentResolver.openInputStream(uri)?.use { stream ->
                val buffer = ByteArrayOutputStream()
                val chunk = ByteArray(32768)
                var n: Int
                while (stream.read(chunk).also { n = it } != -1) {
                    buffer.write(chunk, 0, n)
                }
                buffer.toByteArray()
            } ?: throw IllegalStateException("无法读取文件")

            val resultBytes = if (isZipFile(rawBytes)) {
                formatEpub(rawBytes)
            } else {
                val enc = detectEncoding(rawBytes)
                val text = decodeBytes(rawBytes)

                formatText(text).toByteArray(enc)
            }

            // "rwt" = 读写截断。单纯 "w" 部分设备不截断旧文件，导致残留
            contentResolver.openOutputStream(uri, "rwt")?.use { it.write(resultBytes) }

            Toast.makeText(this, "处理完成", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(this, "处理失败: ${e.message}", Toast.LENGTH_LONG).show()
        } finally {
            finish()
        }
    }

    companion object {
        private const val REQUEST_CODE_PICK_FILE = 1

        private val TEXT_ENTRY_EXTENSIONS = setOf("xhtml", "html", "htm", "xml", "opf", "ncx")

        // ═══════════════════════════════════════════════════════════════
        // 格式化规则 —— 直接改 [...] 里的字符即可增删
        // ═══════════════════════════════════════════════════════════════

        /**
         * ① 标点符号 → 中文逗号（，）
         * 连续多个标点只替换为一个逗号。
         *
         * 包含：～ ~ ！ ! ？ ? 、 … — ： : ； ; ． . " " ' ' 《 》 【 】 「 」 『 』 （ ） ( ) [ ] { } < >
         *
         * 增删方法：直接在下面字符串的 [ ] 里加/删字符。
         * 注意这四个字符在 [ ] 里需转义： ] → \]   \ → \\   ^ → \^   - → \-
         */
        private val PUNCTUATION_TO_COMMA = Regex(
            "[" +
            "～~！!？?、" +           // 波浪号 感叹号 问号 顿号
            "…—" +                   // 省略号 破折号
            "：:；;．." +             // 冒号 分号 句点（中文。保留不动）
            "“”" +          // "" 左右弯引号
            "‘’" +          // '' 左右弯单引号
            "《》" +          // 《》
            "【】" +          // 【】
            "「」" +          // 「」
            "『』" +          // 『』
            "（）" +          // 全角括号 （）
            "\"'" +                   // 英文直引号 " '
            "()\\[\\]{}<>" +          // 英文括号
            "]+"
        )

        /**
         * ② 无意义符号 → 直接删除（不替换为逗号）。
         * 这些是广告/排版符号，不是标点，删掉即可。
         *
         * 增删方法：直接在 [ ] 里加/删字符。
         */
        private val JUNK_SYMBOLS_TO_REMOVE = Regex(
            "[" +
            "\\-\\-=+*#@_|\\\\/" +   // - - = + * # @ _ | \ /
            "\\^&%\$￥€£©®™°" +      // ^ & % $ ￥ € £ © ® ™ °
            "·•‧・" + // · • ‧ ・（各种点）
            "]+"
        )

        /**
         * ③ 空白字符 → 删除。
         * \s = ASCII空白(空格/tab/换行/回车)
         * \p{Z} = Unicode分隔符(全角空格/不间断空格/行段分隔等)
         *  = NEL换行  ​ = 零宽空格  ﻿ = BOM
         */
        private val WHITESPACE_PATTERN = Regex("[\\s\\p{Z}\\u0085\\u200B\\uFEFF]+")

        private val XML_ENCODING_PATTERN = Regex(
            """encoding\s*=\s*["'][^"']+["']""",
            RegexOption.IGNORE_CASE
        )

        // ========== 公开 API ==========

        /**
         * 格式化文本，三步流水线：
         * ① 各种标点符号 → 中文逗号（，）
         * ② 无意义符号 → 直接删除
         * ③ 所有空白字符 → 删除
         *
         * 最终只有中文逗号（，）和句号（。）保留下来供听书软件断句。
         */
        fun formatText(text: String): String {
            return text
                .replace(PUNCTUATION_TO_COMMA, "，")   // ① 标点 → 逗号
                .replace(JUNK_SYMBOLS_TO_REMOVE, "")   // ② 广告符号 → 删除
                .replace(WHITESPACE_PATTERN, "")       // ③ 空白 → 删除
        }

        fun isZipFile(bytes: ByteArray): Boolean {
            return bytes.size >= 4 &&
                bytes[0] == 0x50.toByte() &&
                bytes[1] == 0x4B.toByte() &&
                bytes[2] == 0x03.toByte() &&
                bytes[3] == 0x04.toByte()
        }

        fun isTextEntry(name: String): Boolean {
            return name.substringAfterLast('.', "").lowercase() in TEXT_ENTRY_EXTENSIONS
        }

        // ========== 编码检测（Mozilla Universal Charset Detector）==========

        /** 中文编码族：库检测映射或回退时使用 */
        private val GBK_CHARSET by lazy { Charset.forName("GBK") }

        /** 库能可靠识别的中文编码名集合 */
        private val KNOWN_CHINESE_ENCODINGS = setOf(
            "GB18030", "GBK", "GB2312", "BIG5", "BIG5-HKSCS",
            "EUC-KR", "EUC-JP", "SHIFT_JIS", "UTF-8", "UTF-16LE", "UTF-16BE"
        )

        /**
         * 使用 Mozilla Universal Charset Detector 检测编码。
         *
         * 库在短文本时可能返回 null 或误判（如 GBK → KOI8-R），
         * 此时回退到 UTF-8/GBK 双向 CJK 计数择优。
         */
        fun detectEncoding(bytes: ByteArray): Charset {
            if (bytes.isEmpty()) return Charsets.UTF_8

            val detector = UniversalDetector(null)
            detector.handleData(bytes, 0, bytes.size)
            detector.dataEnd()
            val name = detector.detectedCharset

            // 库给出了明确的中文相关编码 → 直接使用
            if (name != null && name.uppercase() in KNOWN_CHINESE_ENCODINGS) {
                return when (name.uppercase()) {
                    "GB18030", "GB2312" -> GBK_CHARSET
                    else -> try {
                        Charset.forName(name)
                    } catch (_: Exception) {
                        Charsets.UTF_8
                    }
                }
            }

            // 库返回 null 或非中文编码（如 KOI8-R）→ 回退到 CJK 计数择优
            val utf8Text = String(bytes, Charsets.UTF_8)
            val gbkText = String(bytes, GBK_CHARSET)
            val utf8Cjk = countCjk(utf8Text)
            val gbkCjk = countCjk(gbkText)
            return if (gbkCjk > utf8Cjk) GBK_CHARSET else Charsets.UTF_8
        }

        /** 统计字符串中 CJK 统一表意文字的数量（基本区 + 扩展 A 区） */
        private fun countCjk(text: String): Int {
            var n = 0
            for (ch in text) {
                if (ch in '一'..'鿿' || ch in '㐀'..'䶿') n++
            }
            return n
        }

        /**
         * 检测编码 + 解码为字符串。
         * 对 BOM 文件自动剥离 BOM 头（UniversalDetector 不处理 BOM）。
         */
        fun decodeBytes(bytes: ByteArray): String {
            if (bytes.isEmpty()) return ""

            // BOM 剥离
            if (bytes.size >= 3 && bytes[0] == 0xEF.toByte() &&
                bytes[1] == 0xBB.toByte() && bytes[2] == 0xBF.toByte()
            ) {
                return String(bytes, 3, bytes.size - 3, Charsets.UTF_8)
            }
            if (bytes.size >= 2) {
                when {
                    bytes[0] == 0xFF.toByte() && bytes[1] == 0xFE.toByte() ->
                        return String(bytes, 2, bytes.size - 2, Charsets.UTF_16LE)
                    bytes[0] == 0xFE.toByte() && bytes[1] == 0xFF.toByte() ->
                        return String(bytes, 2, bytes.size - 2, Charsets.UTF_16BE)
                }
            }

            val enc = detectEncoding(bytes)
            return String(bytes, enc)
        }

        // ========== epub/ZIP 处理 ==========

        fun formatEpub(bytes: ByteArray): ByteArray {
            val zipIn = ZipInputStream(bytes.inputStream())
            val outBuf = ByteArrayOutputStream()
            val zipOut = ZipOutputStream(outBuf)

            var entry = zipIn.nextEntry
            while (entry != null) {
                val entryBytes = zipIn.readBytes()
                zipOut.putNextEntry(ZipEntry(entry.name))
                if (isTextEntry(entry.name)) {
                    val text = decodeBytes(entryBytes)
                    val formatted = formatText(text)
                    val fixed = XML_ENCODING_PATTERN.replaceFirst(formatted, """encoding="UTF-8"""")
                    zipOut.write(fixed.toByteArray(Charsets.UTF_8))
                } else {
                    zipOut.write(entryBytes)
                }
                zipOut.closeEntry()
                zipIn.closeEntry()
                entry = zipIn.nextEntry
            }

            zipOut.finish()
            zipIn.close()
            return outBuf.toByteArray()
        }
    }
}
