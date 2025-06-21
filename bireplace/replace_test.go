package main

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

func TestBinaryReplace(t *testing.T) {
	tests := []struct {
		name     string
		input    []byte
		old      []byte
		new      []byte
		expected []byte
		count    int
	}{
		{
			name:     "simple replacement",
			input:    []byte("hello world"),
			old:      []byte("world"),
			new:      []byte("there"),
			expected: []byte("hello there"),
			count:    1,
		},
		{
			name:     "multiple replacements",
			input:    []byte("test test test"),
			old:      []byte("test"),
			new:      []byte("done"),
			expected: []byte("done done done"),
			count:    3,
		},
		{
			name:     "no replacement",
			input:    []byte("hello world"),
			old:      []byte("xyz"),
			new:      []byte("abc"),
			expected: []byte("hello world"),
			count:    0,
		},
		{
			name:     "binary data replacement",
			input:    []byte{0x00, 0x01, 0x02, 0x00, 0x01, 0x02},
			old:      []byte{0x00, 0x01, 0x02},
			new:      []byte{0x03, 0x04, 0x05},
			expected: []byte{0x03, 0x04, 0x05, 0x03, 0x04, 0x05},
			count:    2,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			input := bytes.NewReader(tt.input)
			output := &bytes.Buffer{}

			count, err := BinaryReplace(input, output, tt.old, tt.new)
			if err != nil {
				t.Errorf("意外错误: %v", err)
			}

			if count != tt.count {
				t.Errorf("期望替换次数 %d, 实际得到 %d", tt.count, count)
			}

			if !bytes.Equal(output.Bytes(), tt.expected) {
				t.Errorf("期望得到 %v, 实际得到 %v", tt.expected, output.Bytes())
			}
		})
	}
}

func TestFileReplace(t *testing.T) {
	// 创建临时测试文件
	dir := t.TempDir()
	inputPath := filepath.Join(dir, "input.txt")
	outputPath := filepath.Join(dir, "output.txt")

	// 测试数据
	input := []byte("hello world hello world")
	err := os.WriteFile(inputPath, input, 0644)
	if err != nil {
		t.Fatalf("创建测试文件失败: %v", err)
	}

	// 测试替换
	count, err := FileReplace(inputPath, outputPath, "world", "there")
	if err != nil {
		t.Fatalf("FileReplace 失败: %v", err)
	}

	if count != 2 {
		t.Errorf("期望替换 2 处, 实际替换了 %d 处", count)
	}

	// 验证输出
	output, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatalf("读取输出文件失败: %v", err)
	}

	expected := []byte("hello there hello there")
	if !bytes.Equal(output, expected) {
		t.Errorf("期望得到 %q, 实际得到 %q", expected, output)
	}
}
