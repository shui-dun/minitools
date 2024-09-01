package main

import (
	"flag"
	"fmt"
	"io"
	"math/rand/v2"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

func main() {
	var memSize int
	cpuFlag := flag.Bool("cpu", false, "Stress CPU")
	flag.IntVar(&memSize, "mem", 0, "Memory to be allocated in MB")
	ioFlag := flag.Bool("io", false, "Stress I/O")
	flag.Parse()

	if memSize < 0 {
		fmt.Println("内存大小不能为负数")
		return
	}

	if !*cpuFlag && memSize == 0 && !*ioFlag {
		fmt.Println("请指定至少一个选项: -cpu, -mem, 或 -io")
		flag.PrintDefaults()
		return
	}

	if *cpuFlag {
		go stressCPU()
	}
	if memSize > 0 {
		go stressMemory(memSize)
	}
	if *ioFlag {
		go stressIO()
	}

	// 保持主程序运行
	select {}
}

func stressCPU() {
	// 获取CPU核心数
	numCPU := runtime.NumCPU()

	for i := 0; i < numCPU; i++ {
		go func() {
			i := 0
			for {
				i++
			}
		}()
	}
}

func stressMemory(sizeMB int) {
	mem := make([]byte, sizeMB*1024*1024)

	for {
		// 写入一些数据，确保它被实际分配到物理内存中
		val := rand.Int()
		for i := 0; i < len(mem); i += 1024 {
			mem[i] = byte(val)
		}
		time.Sleep(5 * time.Second)
	}
}

func stressIO() {
	for {
		// 使用匿名函数来确保在当前循环结束时关闭和删除文件
		func() {
			// 创建一个临时文件
			tmpFile, err := os.Create(filepath.Join(os.TempDir(), "stress_io_76D451B34463"))
			if err != nil {
				fmt.Println("创建临时文件失败:", err)
				return
			}

			defer os.Remove(tmpFile.Name())
			defer tmpFile.Close()

			// 写入数据
			data := make([]byte, 10*1024*1024)
			if _, err := tmpFile.Write(data); err != nil {
				fmt.Println("写入文件失败:", err)
				return
			}

			// 读取数据
			if _, err := tmpFile.Seek(0, io.SeekStart); err != nil {
				fmt.Println("设置文件指针失败:", err)
				return
			}
			if _, err := io.ReadAll(tmpFile); err != nil {
				fmt.Println("读取文件失败:", err)
				return
			}
		}()
	}
}
