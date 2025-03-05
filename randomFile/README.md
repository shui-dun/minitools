# randomFile

一个用于生成指定大小和内容类型的文件的命令行工具。

## 功能

- 生成指定大小的文件
- 支持多种内容模式：
  - 随机内容
  - 全0填充
  - 全1填充
  - 字母表循环(abcd...xyz 循环)
- 支持多种配置来源：
  - 命令行参数
  - setting.json 配置文件
  - 交互式控制台询问

## 使用方法

### 命令行参数

```bash
# 生成10MB的随机内容文件
./randomFile -size 10485760 -filename output.dat -mode random

# 生成1MB的全0文件
./randomFile -size 1048576 -filename zeros.dat -mode zeros

# 生成2MB的字母表循环文件
./randomFile -size 2097152 -filename alphabet.dat -mode alphabet
```

### 配置文件

创建 `setting.json` 文件：

```json
{
    "size": 1048576,
    "filename": "output.dat",
    "mode": "random"
}
```

然后运行程序不带参数：

```bash
./randomFile
```

### 交互式控制台

如果没有提供命令行参数，也没有找到有效的配置文件，程序会通过交互式命令行提示用户输入所需参数。

## 支持的内容模式

- `random` - 随机字节内容
- `zeros` - 所有bit都是0
- `ones` - 所有bit都是1
- `alphabet` - 字母表循环 (a-z 循环重复)

## 构建

```bash
go build
```