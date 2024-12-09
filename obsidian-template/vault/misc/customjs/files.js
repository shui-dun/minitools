class Files {
    // 同步标题
    // 已知的bug：python的注释 `# ` 会被误判为标题，由于目前使用正则而非语法树进行匹配，暂时无法解决
	async syncHeader(file, force) {
        if (!file) {
            console.error("No active file.");
            return;
        }

        if (file.extension !== 'md') {
            return;
        }
        
        // 读取文件内容
        let fileText = await app.vault.read(file);
        
        // 获取文件名并去掉扩展名
        let fileNameWithoutExtension = file.basename;
        
        // 定义正则表达式匹配 front-matter 和一级标题
        const frontMatterRegex = /^---[\s\S]+?---\n/m;
        // 一级标题不能为 # EOF
        // ?! 是负向前瞻断言，\b 是单词边界，即\w和\W之间的位置
        const titleRegex = /^# (?!EOF\b).+/m;
        
        // 分割文件，判断是否有 front-matter
        let frontMatterMatch = fileText.match(frontMatterRegex);
        let frontMatter = "";
        let content = fileText;
        
        if (frontMatterMatch) {
            // 提取 front-matter 部分和正文部分
            frontMatter = frontMatterMatch[0];
            content = fileText.slice(frontMatter.length);
        }

        // 在正文部分查找并替换第一个一级标题
        let oldTitle = "";
        let titleMatch = content.match(titleRegex);
        if (titleMatch) {
            oldTitle = titleMatch[0].substring(2); // 移除 "# " 前缀
        }
        
        if (titleMatch) {
            content = content.replace(titleRegex, `# ${fileNameWithoutExtension}`);
        } else {
            // 如果没有一级标题
            // 如果是强制模式，在 front-matter 后添加标题
            if (force) {
                content = `# ${fileNameWithoutExtension}\n` + content;
            } else {
                // 直接返回什么都不做
                return;
            }
        }
        
        // 将 front-matter 和更新后的正文重新组合
        let updatedFileText = frontMatter + content;
        
        // 将修改后的文本写回文件
        await app.vault.modify(file, updatedFileText);
        
        // 通知替换成功
        new Notice(`Title replaced: ${oldTitle} -> ${fileNameWithoutExtension}`);
    }

    // 在指定文件所在目录创建folder note
    async createFolderNote(parent) {
        if (!parent) {
            console.error("No active file.");
            return;
        }

        // 获取文件所在目录
        let parentDir = parent.parent.path;

        // 弹出对话框，输入 folder note 的名称
		const modalForm = app.plugins.plugins.modalforms.api;
        let folderNoteName = await modalForm.openForm({
            title: "Create Folder Note",
            fields: [
                {
                    name: "folderNoteName",
                    label: "Folder Note Name",
                    description: "The name of the folder note.",
                    input: { type: "text" },
                },
            ],
        });

        if (folderNoteName.status == 'ok') {
            folderNoteName = folderNoteName.folderNoteName.value;
        } else {
            return;
        }

        // 创建 folder note 文件夹
        let folderNotePath = parentDir + '/' + folderNoteName;

        // 如果文件夹已存在，直接返回
        if (await app.vault.adapter.exists(folderNotePath)) {
            new Notice(`Folder note already exists: ${folderNoteName}`);
            return;
        }

        await app.vault.createFolder(folderNotePath);

        // 创建 folder note 文件
        let folderNoteFilePath = folderNotePath + '/' + folderNoteName + '.md';
        let folderNoteFile = await app.vault.create(folderNoteFilePath, '');

        // 打开 folder note 文件
        app.workspace.activeLeaf.openFile(folderNoteFile);
    }
}