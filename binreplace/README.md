# binreplace

在二进制文件中执行字符串或数值替换，同时保持文件大小不变。

## 参数说明

- `-i` 输入文件路径
- `-o` 输出文件路径（可选，如果不指定则只执行搜索）
- `-old` 要查找的值
- `-new` 新值（可选，如果不指定则只执行搜索）
- `-type` 值的类型：string（字符串）/dec（十进制）/hex（十六进制），默认为string
- `-endian` 字节序：big（大端）/little（小端），在type=string和type=hex时不要指定
- `-len` 字节长度，在type=string和type=hex时不要指定

## 使用示例

1. 安装
```
go test ./...
go install
```

2. 查看值的十六进制表示：
```
binreplace -type dec -endian big -len 4 -old 12345678
binreplace -type hex -old ff00ff
binreplace -type string -old "Hello"
```

3. 搜索文件中的值：
```
binreplace -i a.data -type dec -endian little -len 4 -old 12345678
binreplace -i a.data -type hex -old ff00ff
binreplace -i a.data -type string -old "Hello"
```

4. 替换文件中的值：
```
binreplace -i a.data -o b.data -type dec -endian little -len 4 -old 12345678 -new 12876543
binreplace -i a.data -o b.data -type hex -old ff00ff -new 00ff00
binreplace -i a.data -o b.data -type string -old "Hello" -new "World"
```
