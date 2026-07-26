package com.example.blanktrim

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import java.io.ByteArrayOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipInputStream
import java.util.zip.ZipOutputStream

class MainActivity : Activity() {

    /** 标记是否已经启动过文件选择器，避免从选择器返回后再次触发 */
    private var pickerLaunched = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // 不设置 content view —— 直接弹出文件选择器
    }

    override fun onResume() {
        super.onResume()
        if (!pickerLaunched) {
            pickerLaunched = true
            openFilePicker()
        }
    }

    /** 调用系统 SAF 文件选择器，过滤 .txt / .epub */
    private fun openFilePicker() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "*/*"
            putExtra(
                Intent.EXTRA_MIME_TYPES,
                arrayOf(
                    "text/plain",               // .txt
                    "application/epub+zip",      // .epub
                    "application/octet-stream"   // 兜底：未知类型也显示
                )
            )
        }
        startActivityForResult(intent, REQUEST_CODE_PICK_FILE)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (requestCode != REQUEST_CODE_PICK_FILE || resultCode != Activity.RESULT_OK) {
            // 用户取消选择，直接退出
            finish()
            return
        }

        data?.data?.let { uri -> processFile(uri) } ?: finish()
    }

    /** 读取文件 → 检测类型 → 格式化 → 覆盖写回 */
    private fun processFile(uri: Uri) {
        try {
            val rawBytes = contentResolver.openInputStream(uri)?.readBytes()
                ?: throw IllegalStateException("无法读取文件")

            // 根据文件头判断：ZIP 头（PK）则为 epub，否则当纯文本处理
            val resultBytes = if (isZipFile(rawBytes)) {
                formatEpub(rawBytes)
            } else {
                val text = rawBytes.toString(Charsets.UTF_8)
                formatText(text).toByteArray(Charsets.UTF_8)
            }

            // 覆盖原文件（二进制模式写入）
            contentResolver.openOutputStream(uri, "w")?.use { out ->
                out.write(resultBytes)
            }

            Toast.makeText(this, "处理完成", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(this, "处理失败: ${e.message}", Toast.LENGTH_LONG).show()
        } finally {
            finish()
        }
    }

    companion object {
        private const val REQUEST_CODE_PICK_FILE = 1

        /** epub/ZIP 中需要格式化的文本文件扩展名 */
        private val TEXT_ENTRY_EXTENSIONS = setOf("xhtml", "html", "htm", "xml", "opf", "ncx")

        /** 需要替换为中文逗号的目标字符（支持连续出现） */
        private val TARGET_PATTERN = Regex("[~！!…]+")

        /**
         * 所有空白字符，包括：
         * - ASCII 空白（\s = 空格、\t、\n、\r、\f、\x0B）
         * - Unicode 分隔符（\p{Z} = 全角空格 　、不间断空格  、
         *   行分隔符  、段分隔符  、各种排版空格  -  等）
         */
        private val WHITESPACE_PATTERN = Regex("[\\s\\p{Z}]+")

        // ========== 公开 API，供单元测试调用 ==========

        /**
         * 格式化文本内容：
         * 1. 连续的 ~ / ！/ ! / … → 中文逗号（，）
         * 2. 移除所有空白字符（空格、制表符、换行符）
         */
        fun formatText(text: String): String {
            return text
                .replace(TARGET_PATTERN, "，")
                .replace(WHITESPACE_PATTERN, "")
        }

        /** 通过文件头魔数判断是否为 ZIP/epub 格式 */
        fun isZipFile(bytes: ByteArray): Boolean {
            return bytes.size >= 4 &&
                bytes[0] == 0x50.toByte() &&
                bytes[1] == 0x4B.toByte() &&
                bytes[2] == 0x03.toByte() &&
                bytes[3] == 0x04.toByte()
        }

        /** 判断 ZIP 条目是否为需要格式化的文本文件 */
        fun isTextEntry(name: String): Boolean {
            val ext = name.substringAfterLast('.', "").lowercase()
            return ext in TEXT_ENTRY_EXTENSIONS
        }

        /**
         * 格式化 epub 文件（ZIP 容器）：
         * - 文本条目（xhtml/html/xml/opf/ncx）→ 进行文本格式化
         * - 二进制条目（图片、字体等）→ 原样复制
         */
        fun formatEpub(bytes: ByteArray): ByteArray {
            val zipIn = ZipInputStream(bytes.inputStream())
            val outBuf = ByteArrayOutputStream()
            val zipOut = ZipOutputStream(outBuf)

            var entry = zipIn.nextEntry
            while (entry != null) {
                val entryBytes = zipIn.readBytes()

                // 创建新的 ZIP 条目（不保留原始压缩方式，统一用默认压缩）
                zipOut.putNextEntry(ZipEntry(entry.name))

                if (isTextEntry(entry.name)) {
                    val text = entryBytes.toString(Charsets.UTF_8)
                    val formatted = formatText(text)
                    zipOut.write(formatted.toByteArray(Charsets.UTF_8))
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
