package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

const (
	ParSize     = "size"
	ParFilename = "filename"
	ParMode     = "mode"

	ModeRandom   = "random"
	ModeZeros    = "zeros"
	ModeOnes     = "ones"
	ModeAlphabet = "alphabet"

	BufferSize = 8192
)

var paramDescriptions = map[string]string{
	ParSize:     "文件大小(字节)",
	ParFilename: "文件名",
	ParMode:     "内容模式: random, zeros, ones, alphabet",
}

var params = []string{ParSize, ParFilename, ParMode}

var modeDescriptions = map[string]string{
	ModeRandom:   "随机内容",
	ModeZeros:    "全0填充",
	ModeOnes:     "全1填充",
	ModeAlphabet: "字母表循环",
}

var modes = []string{ModeRandom, ModeZeros, ModeOnes, ModeAlphabet}

type Config struct {
	Size     int64  `json:"size"`
	Filename string `json:"filename"`
	Mode     string `json:"mode"`
}

func main() {
	r := rand.New(rand.NewSource(time.Now().UnixNano()))
	// 首先从配置文件加载默认配置
	config, _ := readConfigFile()

	// 解析命令行参数
	cmdConfig := parseCommandLine()

	// 应用有效的命令行参数
	if cmdConfig.Size != 0 {
		config.Size = cmdConfig.Size
	}
	if cmdConfig.Filename != "" {
		config.Filename = cmdConfig.Filename
	}
	if cmdConfig.Mode != "" {
		config.Mode = cmdConfig.Mode
	}

	// 如果配置不完整，通过控制台询问缺失的配置项
	promptConfig(&config)

	// 生成文件
	err := generateFile(r, &config)
	if err != nil {
		fmt.Printf("生成文件失败: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("文件 %s 已生成，大小: %d 字节，模式: %s\n", config.Filename, config.Size, config.Mode)
}

// parseCommandLine 解析命令行参数
func parseCommandLine() Config {
	size := flag.Int64(ParSize, 0, paramDescriptions[ParSize])
	filename := flag.String(ParFilename, "", paramDescriptions[ParFilename])
	mode := flag.String(ParMode, "", paramDescriptions[ParMode])

	flag.Parse()

	config := Config{
		Size:     *size,
		Filename: *filename,
		Mode:     *mode,
	}

	return config
}

func readConfigFile() (Config, bool) {
	var config Config

	configPath := "random_file_setting.json"
	data, err := os.ReadFile(configPath)
	if err != nil {
		return config, false
	}

	err = json.Unmarshal(data, &config)
	if err != nil {
		fmt.Printf("配置文件解析错误: %v\n", err)
		return config, false
	}

	fmt.Println("已从配置文件加载设置")
	return config, true
}

func promptConfig(config *Config) {
	reader := bufio.NewReader(os.Stdin)

	type promptStep struct {
		isValid    func(*Config) bool
		promptText string
		parseInput func(string, *Config)
	}

	buildModePromptText := func() string {
		var sb strings.Builder
		for i, mode := range modes {
			sb.WriteString(fmt.Sprintf("%d. %s (%s)\n", i+1, modeDescriptions[mode], mode))
		}
		return sb.String()
	}

	steps := []promptStep{
		{
			isValid: func(c *Config) bool { return c.Size > 0 },
			promptText: fmt.Sprintf("请输入合法的%s: ", paramDescriptions[ParSize]),
			parseInput: func(input string, c *Config) {
				size, err := strconv.ParseInt(input, 10, 64)
				if err == nil {
					c.Size = size
				}
			},
		},
		{
			isValid: func(c *Config) bool { return c.Filename != "" },
			promptText: fmt.Sprintf("请输入合法的%s: ", paramDescriptions[ParFilename]),
			parseInput: func(input string, c *Config) {
				c.Filename = input
			},
		},
		{
			isValid: func(c *Config) bool {
				for _, m := range modes {
					if m == c.Mode {
						return true
					}
				}
				return false
			},
			promptText: "请选择内容模式:\n" + buildModePromptText() + fmt.Sprintf("请输入选择(1-%d): ", len(modes)),
			parseInput: func(input string, c *Config) {
				idx, err := strconv.Atoi(input)
				if err == nil && idx >= 1 && idx <= len(modes) {
					c.Mode = modes[idx-1]
				}
			},
		},
	}

	for _, step := range steps {
		for !step.isValid(config) {
			fmt.Print(step.promptText)
			input, _ := reader.ReadString('\n')
			input = strings.TrimSpace(input)
			step.parseInput(input, config)
		}
	}
}

// generateFile 生成指定内容的文件
func generateFile(r *rand.Rand, config *Config) error {
	// 确保目录存在，不存在则递归创建
	dir := filepath.Dir(config.Filename)
	err := os.MkdirAll(dir, os.ModePerm)
	if err != nil {
		return err
	}

	// 创建文件
	file, err := os.Create(config.Filename)
	if err != nil {
		return err
	}
	defer file.Close()

	// 根据模式生成内容
	writer := bufio.NewWriter(file)
	defer writer.Flush()

	// 定义内容生成函数映射
	contentGenerators := map[string]func([]byte, int){
		ModeRandom: func(buffer []byte, n int) {
			for i := 0; i < n; i++ {
				buffer[i] = byte(r.Intn(256))
			}
		},
		ModeZeros: func(buffer []byte, n int) {
			for i := 0; i < n; i++ {
				buffer[i] = 0
			}
		},
		ModeOnes: func(buffer []byte, n int) {
			for i := 0; i < n; i++ {
				buffer[i] = 0xff
			}
		},
		ModeAlphabet: func(buffer []byte, n int) {
			static := 0
			for i := 0; i < n; i++ {
				buffer[i] = 'a' + byte(static%26)
				static++
			}
		},
	}

	// 获取对应的内容生成函数
	generator, ok := contentGenerators[config.Mode]
	if !ok {
		return fmt.Errorf("不支持的模式: %s", config.Mode)
	}

	// 直接写入内容
	buffer := make([]byte, BufferSize)
	for remaining := config.Size; remaining > 0; {
		n := BufferSize
		if remaining < int64(BufferSize) {
			n = int(remaining)
		}

		// 使用提供的函数填充缓冲区
		generator(buffer, n)

		written, err := writer.Write(buffer[:n])
		if err != nil {
			return err
		}

		remaining -= int64(written)
	}

	return nil
}
