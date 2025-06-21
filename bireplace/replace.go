package main

import (
	"bytes"
	"errors"
	"io"
	"os"
)

var ErrDifferentLength = errors.New("old and new byte slices must have the same length")

// BinaryReplace 在二进制文件中替换所有指定的字符串
// 返回替换的次数和可能的错误
func BinaryReplace(input io.Reader, output io.Writer, old, new []byte) (int, error) {
	if len(old) != len(new) {
		return 0, ErrDifferentLength
	}

	// 读取所有内容
	content, err := io.ReadAll(input)
	if err != nil {
		return 0, err
	}

	// 计算替换次数
	count := bytes.Count(content, old)

	// 替换所有匹配项
	content = bytes.ReplaceAll(content, old, new)

	// 写入输出
	_, err = output.Write(content)
	if err != nil {
		return 0, err
	}

	return count, nil
}

// FileReplace 对文件执行二进制替换操作
func FileReplace(inputPath, outputPath string, old, new string) (int, error) {
	input, err := os.Open(inputPath)
	if err != nil {
		return 0, err
	}
	defer input.Close()

	output, err := os.Create(outputPath)
	if err != nil {
		return 0, err
	}
	defer output.Close()

	return BinaryReplace(input, output, []byte(old), []byte(new))
}
