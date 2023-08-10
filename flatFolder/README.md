# flatFolder

递归地读取文件夹下的所有文件，将其转化为一个大文件，以便于与Claude2等LLM通话。

例如，对于如下的文件夹结构：

```
.
├── a.txt
└── folder1
    └── b.txt
```

生成如下文件：

```
file [a.txt]:

[content of a.txt]

file [folder1/b.txt]:

[content of folder1/b.txt]
```