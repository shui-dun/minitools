package replace

import (
	"bytes"
	"os"
	"path/filepath"
	"testing"
)

var input = []byte{0xAB, 0xC7, 0x2D, 0xEF, 0x65, 0x89, 0xC7, 0x2D, 0xBC}
var old = []byte{0xC7, 0x2D}
var new = []byte{0xF3, 0x4A}
var expected = []byte{0xAB, 0xF3, 0x4A, 0xEF, 0x65, 0x89, 0xF3, 0x4A, 0xBC}
var expectedCount = 2

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
			name: "hex pattern",
			input:    input,
			old:      old,
			new:      new,
			expected: expected,
			count: expectedCount,
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
	err := os.WriteFile(inputPath, input, 0644)
	if err != nil {
		t.Fatalf("创建测试文件失败: %v", err)
	}

	// 测试替换
	count, err := FileReplace(inputPath, outputPath, old, new)
	if err != nil {
		t.Fatalf("FileReplace 失败: %v", err)
	}

	if count != expectedCount {
		t.Errorf("期望替换 次数 %d, 实际得到 %d", expectedCount, count)
	}

	// 验证输出
	output, err := os.ReadFile(outputPath)
	if err != nil {
		t.Fatalf("读取输出文件失败: %v", err)
	}

	if !bytes.Equal(output, expected) {
		t.Errorf("期望得到 %v, 实际得到 %v", expected, output)
	}
}

func TestFileSearch(t *testing.T) {
	// 创建临时测试文件
	dir := t.TempDir()
	inputPath := filepath.Join(dir, "input.txt")

	// 测试数据
	err := os.WriteFile(inputPath, input, 0644)
	if err != nil {
		t.Fatalf("创建测试文件失败: %v", err)
	}

	// 测试搜索
	count, err := FileSearch(inputPath, old)
	if err != nil {
		t.Fatalf("FileSearch 失败: %v", err)
	}

	if count != expectedCount {
		t.Errorf("期望找到 %d 次, 实际找到 %d 次", expectedCount, count)
	}
}
