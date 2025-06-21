package main

import (
	"flag"
	"fmt"
	"os"

	"bireplace/convert"
	"bireplace/replace"
)

func main() {
	inputFile := flag.String("i", "", "Input file path")
	outputFile := flag.String("o", "", "Output file path")
	oldStr := flag.String("old", "", "Value to replace")
	newStr := flag.String("new", "", "New value")
	valueType := flag.String("type", "string", "Value type: string/dec/hex")
	endian := flag.String("endian", "", "Byte order: big/little (required for decimal type)")
	length := flag.Int("len", 0, "Length in bytes (required for decimal type)")
	flag.Parse()

	// 解析值类型
	vType, err := convert.ParseValueType(*valueType)
	if err != nil {
		fmt.Printf("Error parsing value type: %v, using default 'string'\n", err)
	}

	// 解析字节序
	endianness, err := convert.ParseEndianness(*endian)
	if err != nil {
		fmt.Printf("Error parsing endianness: %v, using default none\n", err)
		os.Exit(1)
	}

	// 将旧值转换为字节
	oldConfig := convert.Config{
		Value:  *oldStr,
		Type:   vType,
		Endian: endianness,
		Length: *length,
	}

	oldBytes, err := convert.ToBytes(oldConfig)
	if err != nil {
		fmt.Printf("Error converting old value: %v\n", err)
		os.Exit(1)
	}

	// 预览旧值的十六进制表示
	fmt.Printf("old value in hex: %x\n", oldBytes)

	// 如果未指定输入文件，则预览后退出
	if *inputFile == "" {
		os.Exit(0)
	}

	// 如果提供了新值，则将其转换为字节
	var newBytes []byte
	if *newStr != "" {
		newConfig := convert.Config{
			Value:  *newStr,
			Type:   vType,
			Endian: endianness,
			Length: *length,
		}

		newBytes, err = convert.ToBytes(newConfig)
		if err != nil {
			fmt.Printf("Error converting new value: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("New value hex: %x\n", newBytes)
	}

	// 如果没有输出文件，则仅搜索并计数
	if *outputFile == "" {
		count, err := replace.FileSearch(*inputFile, oldBytes)
		if err != nil {
			fmt.Printf("Error: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("Found %d occurrences\n", count)
		os.Exit(0)
	}

	// 验证旧值和新值的长度是否一致
	if len(oldBytes) != len(newBytes) {
		fmt.Println("Error: Old and new values must have the same length for binary replacement")
		os.Exit(1)
	}

	// 执行文件替换操作
	count, err := replace.FileReplace(*inputFile, *outputFile, oldBytes, newBytes)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Replaced %d occurrences\n", count)
}
