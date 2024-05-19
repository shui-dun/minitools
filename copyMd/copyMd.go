package main

import (
	"bufio"
	"fmt"
	"io"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

func main() {
	// 处理命令行参数
	if len(os.Args) != 3 {
		fmt.Println("Usage: copyMd /source/path/to/mdfile /dest/directory")
		return
	}

	sourcePath := os.Args[1]
	destDir := os.Args[2]

	err := copyMarkdownAndImages(sourcePath, destDir)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	}
}

func copyMarkdownAndImages(mdFilePath string, destDir string) error {
	// 复制md文件
	err := copyFile(mdFilePath, destDir)
	if err != nil {
		return fmt.Errorf("copying markdown file: %w", err)
	}

	mdFile, err := os.Open(mdFilePath)
	if err != nil {
		return fmt.Errorf("opening markdown file: %w", err)
	}
	defer mdFile.Close()

	scanner := bufio.NewScanner(mdFile)
	imagePattern := regexp.MustCompile(`!\[.*?\]\((.*?)\)`)

	for scanner.Scan() {
		line := scanner.Text()
		matches := imagePattern.FindAllStringSubmatch(line, -1)
		for _, match := range matches {
			imagePath := urlDecode(match[1])
			if isRelativePath(imagePath) {
				imageFilePath := filepath.Join(filepath.Dir(mdFilePath), imagePath)
				destImageFileDir := filepath.Join(destDir, filepath.Dir(imagePath))
				err := copyFile(imageFilePath, destImageFileDir)
				if err != nil {
					fmt.Printf("Error copying image file %s: %v\n", imageFilePath, err)
				}
			}
		}
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("scanning markdown file: %w", err)
	}

	return nil
}

// 复制文件
// src: 源文件路径
// dst: 目标文件夹路径（注意：不是目标文件路径）
func copyFile(src string, dstFolder string) error {
	srcFile, err := os.Open(src)
	if err != nil {
		return fmt.Errorf("opening source file: %w", err)
	}
	defer srcFile.Close()

	// 创建目标文件夹
	err = os.MkdirAll(dstFolder, os.ModePerm)
	if err != nil {
		return fmt.Errorf("creating destination directory: %w", err)
	}

	dst := filepath.Join(dstFolder, filepath.Base(src))

	destFile, err := os.Create(dst)
	if err != nil {
		return fmt.Errorf("creating destination file: %w", err)
	}
	defer destFile.Close()

	_, err = io.Copy(destFile, srcFile)
	if err != nil {
		return fmt.Errorf("copying file: %w", err)
	}

	return nil
}

// 判断是否是相对路径的文件
func isRelativePath(path string) bool {
	// 如果以 / 开头，说明是绝对路径
	if strings.HasPrefix(path, "/") {
		return false
	}
	// windows 下的绝对路径
	if len(path) > 2 && path[1] == ':' {
		return false
	}
	// 如果包含 ://，说明是URL
	if strings.Contains(path, "://") {
		return false
	}
	return true
}

// url解码
func urlDecode(str string) string {
	s, _ := url.QueryUnescape(str)
	return s
}
