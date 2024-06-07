package main

import (
	"bufio"
	"fmt"
	"golang.org/x/xerrors"
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

	if err := copyMarkdownAndImages(sourcePath, destDir); err != nil {
		fmt.Printf("Error %+v\n", xerrors.Errorf("copying markdown and images: %w", err))
	}
}

func copyMarkdownAndImages(mdFilePath string, destDir string) error {
	// 复制md文件
	if err := copyFile(mdFilePath, destDir); err != nil {
		return xerrors.Errorf("copying markdown file: %w", err)
	}

	mdFile, err := os.Open(mdFilePath)
	if err != nil {
		return xerrors.Errorf("opening markdown file: %w", err)
	}
	defer mdFile.Close()

	scanner := bufio.NewScanner(mdFile)
	imagePattern := regexp.MustCompile(`!\[.*?\]\((.*?)\)`)

	for scanner.Scan() {
		line := scanner.Text()
		matches := imagePattern.FindAllStringSubmatch(line, -1)
		for _, match := range matches {
			// 解码 URL 编码的字符串
			imagePath, _ := url.QueryUnescape(match[1])
			if isRelativePath(imagePath) {
				imageFilePath := filepath.Join(filepath.Dir(mdFilePath), imagePath)
				destImageFileDir := filepath.Join(destDir, filepath.Dir(imagePath))
				if err := copyFile(imageFilePath, destImageFileDir); err != nil {
					fmt.Printf("Error %+v\n", xerrors.Errorf("copying image file: %w", err))
				}
			}
		}
	}

	if err := scanner.Err(); err != nil {
		return xerrors.Errorf("scanning markdown file: %w", err)
	}

	return nil
}

// 复制文件
// src: 源文件路径
// dst: 目标文件夹路径（注意：不是目标文件路径）
func copyFile(src string, dstFolder string) error {
	srcFile, err := os.Open(src)
	if err != nil {
		return xerrors.Errorf("opening source file: %w", err)
	}
	defer srcFile.Close()

	// 创建目标文件夹
	if err = os.MkdirAll(dstFolder, os.ModePerm); err != nil {
		return xerrors.Errorf("creating destination directory: %w", err)
	}

	dst := filepath.Join(dstFolder, filepath.Base(src))

	destFile, err := os.Create(dst)
	if err != nil {
		return xerrors.Errorf("creating destination file: %w", err)
	}
	defer destFile.Close()

	if _, err = io.Copy(destFile, srcFile); err != nil {
		return xerrors.Errorf("copying file: %w", err)
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
