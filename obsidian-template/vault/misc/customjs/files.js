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

        // 如果以.excalidraw.md结尾，不处理
        if (file.basename.endsWith('.excalidraw')) {
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
            // 如果相同，直接返回
            if (oldTitle == fileNameWithoutExtension) {
                return;
            }
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

    // 判断一个文件是否是folder note
    isFolderNote(file) {
        return file.basename === file.parent.name;
    }

    // 找到仅仅被指定文件引用的附件列表
    findAttachmentsOnlyUsedByFile(file) {
        let cache = app.metadataCache.getFileCache(file);
        // 添加 embeds，links，frontmatterLinks
        let attachmentsLinks = [
            ...(cache?.embeds || []),
            ...(cache?.links || []),
            ...(cache?.frontmatterLinks || []),
          ];
        attachmentsLinks = attachmentsLinks.map(attachment => attachment.link);

        // 获得这些文件
        let attachments = attachmentsLinks.map(link => {
            return app.metadataCache.getFirstLinkpathDest(link, '');
        });

        // 去掉.md文件，但保留.excalidraw.md文件
        attachments = attachments.filter(attachment => {
            if (!attachment) {
                return false;
            }
            if (attachment.path.endsWith('.md') && !attachment.path.endsWith('.excalidraw.md')) {
                return false;
            }
            return true;
        });

        // 只保留只被当前文件引用的附件，如果被多个文件引用，不移动
        return attachments.filter(attachment => {
            let backlinks = app.metadataCache.getBacklinksForFile(attachment);
            return backlinks.data.size == 1;
        });
    }

    // 把一个文件转化为folder note
    async convertToFolderNote(file) {
        if (!file) {
            console.error("No active file.");
            return;
        }

        let fileName = file.basename;
        let folderPath = file.parent.path;

        // 如果文件名和文件夹名不相同，创建文件夹
        if (!this.isFolderNote(file)) {
            // 创建文件夹
            folderPath = folderPath + '/' + fileName;
            await app.vault.createFolder(folderPath);

            // 移动文件
            let newFilePath = folderPath + '/' + fileName + '.md';
            await app.fileManager.renameFile(file, newFilePath);
        }

        // 将链接的附件全部移动到新的文件夹的assets目录下
        let attachmentsToMove = this.findAttachmentsOnlyUsedByFile(file);

        if (attachmentsToMove.length == 0) {
            return folderPath;
        }

        let assetsPath = folderPath + '/assets';
        if (!app.vault.getAbstractFileByPath(assetsPath)) {
            await app.vault.createFolder(assetsPath);
        }

        for (let attachment of attachmentsToMove) {
            let attachmentPath = attachment.path;
            let newAttachmentPath = assetsPath + '/' + attachmentPath.split('/').pop();
            await app.fileManager.renameFile(attachment, newAttachmentPath);
        }

        return folderPath;
    }

    // 为一个页面添加子页面
    async addSubNote(parentFile, defaultSubNoteName) {
        if (!parentFile) {
            console.error("No active file.");
            return;
        }

        const modalForm = app.plugins.plugins.modalforms.api;
        let subNoteName = await modalForm.openForm({
            title: "Create SubNote",
            fields: [
                {
                    name: "subNoteName",
                    label: "subNoteName",
                    description: "The name of the sub note.",
                    input: { type: "text" },
                },
            ],
        }, { values: { subNoteName: defaultSubNoteName || "" } });

        if (subNoteName.status == 'ok') {
            subNoteName = subNoteName.subNoteName.value;
        } else {
            return;
        }

        // 如果是扁平化目录，则创建同级页面，否则是创建子页面
        let flatFolders = [
            "note",
            "habit",
            "领域/job/jobList",
        ];
        let folderPath = this.getParentPath(parentFile.path);
        if (!flatFolders.includes(this.getParentPath(parentFile.path))) {
            folderPath = await this.convertToFolderNote(parentFile);
        }
        let pathOfSubNote = folderPath + '/' + subNoteName + '.md';

        // 如果文件已经存在，不创建
        if (app.vault.getAbstractFileByPath(pathOfSubNote)) {
            new Notice(`SubNote ${subNoteName} already exists.`);
            await this.addSubNote(parentFile, subNoteName);
            return;
        }

        await app.vault.create(pathOfSubNote, '');

        // 如果目录被指定不用插入链接，或者是扁平化目录，则不插入链接，否则插入链接
        let foldersWithoutLinks = [
            "计划",
            "领域",
        ];
        if (!flatFolders.includes(folderPath) && !foldersWithoutLinks.includes(folderPath)) {
            // 插入链接
            let link = `[${subNoteName}](${this.encodeLink(subNoteName)}.md)`;
            await this.insertText(link);
        } else {
            // 打开新创建的文件
            await app.workspace.activeLeaf.openFile(app.vault.getAbstractFileByPath(pathOfSubNote));
        }
    }

    // archive a note
    async archiveNote(file) {
        if (!file) {
            console.error("No active file.");
            return;
        }

        let folderPath = await this.convertToFolderNote(file);
        let parentDir = this.getParentPath(folderPath);

        let archivePath = parentDir + '/archive';
        if (!app.vault.getAbstractFileByPath(archivePath)) {
            await app.vault.createFolder(archivePath);
            // 创建archive文件
            await app.vault.create(archivePath + '/archive.md', '\n```meta-bind-embed\n[[archive_view]]\n```');
        }

        let fileName = file.basename;
        // 今日日期
        let today = this.formatDate(new Date());
        let newFileName = `${today}-${fileName}`;
        let tmpFolder = `${archivePath}/${fileName}`;
        let newFolderPath = `${archivePath}/${newFileName}`;

        // 移动文件夹
        // ob存在bug，ob的app.fileManager.renameFile只有在移动前后文件(夹)名称相同时才会触发链接的更新
        // 因此这里进行2次移动，第一次移动到临时文件夹，第二次移动到新文件夹，而不一次到位
        // 这样才能触发链接的更新
        await app.fileManager.renameFile(app.vault.getAbstractFileByPath(folderPath), tmpFolder);
        await app.fileManager.renameFile(app.vault.getAbstractFileByPath(tmpFolder), newFolderPath);

        // 按理来说，folder notes 插件会自动重命名文件夹的folder note，但有时候没有成功，所以这里为保险起见，手动重命名folder note
        let folderNote = app.vault.getAbstractFileByPath(`${newFolderPath}/${fileName}.md`);
        if (folderNote) {
            await app.fileManager.renameFile(folderNote, `${newFolderPath}/${newFileName}.md`);
        }
    }

    async moveNote() {
        const modalForm = app.plugins.plugins.modalforms.api;

        let currentFile = app.workspace.getActiveFile();
        let defaultSourceNotes = currentFile ? [currentFile.path] : []; // 多选 => 数组
        let defaultTargetFolder = currentFile ? currentFile.parent.path : "/";
    
        const formDefinition = {
            "fields": [
                {
                    "name": "sourceNotes",
                    "label": "Select notes to move",
                    "description": "Choose one or multiple notes to move",
                    "input": {
                        "type": "multiselect",
                        "source": "notes",
                        "folder": "/"
                    },
                    "isRequired": true
                },
                {
                    "name": "targetFolder",
                    "label": "Select the target folder",
                    "description": "Where do you want to move these notes to?",
                    "input": {
                        "type": "folder",
                        "source": "notes"
                    },
                    "isRequired": true
                }
            ]
        };
    
        let result = await modalForm.openForm(formDefinition, {
            values: {
                sourceNotes: defaultSourceNotes,
                targetFolder: defaultTargetFolder
            }
        });
    
        if (result.status !== 'ok') {
            return;
        }
    
        let notesToMove = result.sourceNotes.value;
        let targetFolderPath = result.targetFolder.value;
    
        await this.ensureFolderExists(targetFolderPath);
    
        for (let notePath of notesToMove) {
            let fileToMove = app.metadataCache.getFirstLinkpathDest(notePath, '');
    
            if (this.isFolderNote(fileToMove)) {
                const folderOfNote = fileToMove.parent;
    
                // 如果目标目录恰好是同一个文件夹，则不用移动
                if (folderOfNote.path === targetFolderPath) {
                    new Notice(`"${fileToMove.basename}" 已经在目标文件夹中，无需移动。`);
                    continue;
                }
    
                let newFolderPath = targetFolderPath + '/' + folderOfNote.name;
    
                // 如果这个子文件夹已经存在，则跳过
                let existingFolder = app.vault.getAbstractFileByPath(newFolderPath);
                if (existingFolder) {
                    new Notice(`目标文件夹中已存在名为 "${folderOfNote.name}" 的文件夹，跳过移动。`);
                    continue;
                }
    
                // 执行移动
                await app.fileManager.renameFile(folderOfNote, newFolderPath);
                new Notice(`Folder "${fileToMove.basename}" 已移动到 "${targetFolderPath}"`);
            }
            // 如果不是 folder note，则移动笔记及其附件
            else {
                // 如果目标目录与当前所在目录相同，不跳过，因为这可以当作整理图片的功能（将图片移动到assets文件夹）
                // 移动笔记本身
                let newNotePath = targetFolderPath + '/' + fileToMove.name;
                await app.fileManager.renameFile(fileToMove, newNotePath);
                // 先移动附件
                let attachmentsToMove = this.findAttachmentsOnlyUsedByFile(fileToMove);
                // 目标目录下的子目录 assets，用于存放附件
                let newAssetsPath = targetFolderPath + '/assets';
                await this.ensureFolderExists(newAssetsPath);
    
                for (let attachment of attachmentsToMove) {
                    let newAttachmentPath = newAssetsPath + '/' + attachment.name;
                    await app.fileManager.renameFile(attachment, newAttachmentPath);
                }
                new Notice(`File "${fileToMove.basename}" 已移动到 "${targetFolderPath}"`);
            }
        }
    }

    /**
     * 如果指定路径不存在，则递归创建路径对应的文件夹
     */
    async ensureFolderExists(folderPath) {
        let existingFolder = app.vault.getAbstractFileByPath(folderPath);
        if (existingFolder) {
            return;
        }

        // 递归创建
        let parts = folderPath.split('/');
        for (let i = 1; i <= parts.length; i++) {
            let subPath = parts.slice(0, i).join('/');
            if (!subPath) continue;
            let f = app.vault.getAbstractFileByPath(subPath);
            if (!f) {
                await app.vault.createFolder(subPath);
            }
        }
    }

    async deleteNote(file) {   
        // 如果是 folder note，删除整个文件夹
        if (this.isFolderNote(file)) {
            // 获取对应的文件夹
            const folder = app.vault.getAbstractFileByPath(file.parent.path);
            await this.removeFileOrFolder(folder);
            new Notice(`Folder "${file.basename}" has been deleted.`);
        } else {
            // 如果不是 folder note，则删除笔记文件及只被此笔记引用的附件
            const attachmentsToDelete = this.findAttachmentsOnlyUsedByFile(file);
            for (const attachment of attachmentsToDelete) {
                await this.removeFileOrFolder(attachment);
            }
            await this.removeFileOrFolder(file);
            new Notice(`File "${file.basename}" and its exclusive attachments have been deleted.`);
        }
    }

    async openParent() {
        let currentFile = app.workspace.getActiveFile();
        if (!currentFile) {
            new Notice("No active file.");
            return;
        }
        let parentFile = this.getParentFolderNote(currentFile.path);
        // 如果不存在，就返回
        if (!app.vault.getAbstractFileByPath(parentFile)) {
            new Notice("Parent note does not exist.");
            return;
        }
        await app.workspace.openLinkText(parentFile, "", false);
    }
    
    /**
     * 移除文件或文件夹如果是移动(通过app.isMobile判断），彻底删除，如果是电脑，移动到系统回收站
     */
    async removeFileOrFolder(abstractFile) {
        if (!abstractFile) return;
    
        try {
            if (app.isMobile) {
                await app.vault.delete(abstractFile, true);
            } else {
                await app.vault.trash(abstractFile, true);
            }
        } catch (error) {
            console.error(`Failed to remove file/folder: ${abstractFile.path}`, error);
        }
    }
    

    formatDate(date) {
        const year = date.getFullYear().toString().slice(-2); // 获取年份后两位
        const month = String(date.getMonth() + 1).padStart(2, '0'); // 月份需要加1，补0
        const day = String(date.getDate()).padStart(2, '0'); // 补0
        return `${year}-${month}-${day}`;
    }

    // 得到文件夹路径，例如输入 a/b/c.md 得到 a/b ，输入 a/b 得到 a
    getParentPath(filePath) {
        return filePath.split('/').slice(0, -1).join('/');
    }

    // 打开父folder note
    // 例如对于 a/b/c.md，返回 a/b/b.md
    // 对于 a/b/b.md，返回 a/a.md
    getParentFolderNote(filePath) {
        let file = app.vault.getAbstractFileByPath(filePath);
        if (this.isFolderNote(file)) {
            let parentFolder = this.getParentPath(this.getParentPath(filePath));
            return parentFolder + '/' + this.getFileName(parentFolder) + '.md';
        } else {
            let parentFolder = this.getParentPath(filePath);
            return parentFolder + '/' + this.getFileName(parentFolder) + '.md';
        }
    }

    // 得到文件(夹)名称，例如输入 a/b/c.md 得到 c.md ，输入 a/b 得到 b
    getFileName(filePath) {
        return filePath.split('/').pop();
    }

    // 找到某个文件夹一层的笔记以及folder note，我将folder note定义为文件夹名和文件名相同的文件，例如，对于：
    // a/a.md
    // a/b.md
    // a/c/c.md
    // b.md
    // 返回a/a.md和b.md
    getFolderNotes(folderPath) {
        // 获取指定文件夹
        const folder = app.vault.getAbstractFileByPath(folderPath);
        if (!folder) {
            return [];
        }
        
        const folderNotes = [];
        
        // 只遍历文件夹下一层的文件
        for (const file of folder.children) {
            if (file.extension === 'md') {
                if (this.isFolderNote(file)) {
                    continue;
                }
                folderNotes.push(file.path);
            } else if (!file.extension) {
                // 寻找文件夹下的同名的文件
                let path2 = `${file.path}/${file.name}.md`;
                let file2 = app.vault.getAbstractFileByPath(path2);
                if (file2) {
                    folderNotes.push(file2.path);
                }
            }
        }
        return folderNotes.sort((a,b) => a.localeCompare(b));
    }

    // 编码链接
    // 将 'd e.md' 转化为 'd%20e.md'
    encodeLink(link) {
        return link.replace(/ /g, '%20');
    }

    // 转化外部文件链接
    // 将 '"D:\a\b c\d e.txt"' 转化为 '[d e.txt](D:\a\b%20c\d%20e.txt)'
    convertExternalLink(link) {
        let path = link[0] == '"' ? link.slice(1, -1) : link;
        let fileName = path.split('\\').pop();
        // let encodedPath = encodeURI(path);
        let encodedPath = this.encodeLink(path);
        return `[${fileName}](${encodedPath})`;
    }

    async convertExternalLinkFromClipboard() {
        let link = await navigator.clipboard.readText();
        let convertedLink = this.convertExternalLink(link);
        return convertedLink;
    }

    // 打开光标处的外部链接所在的位置
    openLinkFolderUnderCursor() {
        // Obsidian 的工作区（workspace）是一个树状结构，可以水平或垂直分割成多个子容器，每个子容器最终分割为叶子（leaf），每个 leaf 会被赋予一个 view 用于实际显示内容
        const editor = app.workspace.activeLeaf.view.editor;
        const cursor = editor.getCursor();
        const lineText = editor.getLine(cursor.line);

        const linkRegex = /\[[^\]]*\]\([^)]+\)/g;
        let match;
        while ((match = linkRegex.exec(lineText)) !== null) {
            const startIndex = match.index;
            const endIndex = match.index + match[0].length;
    
            // cursor.ch 表示光标在当前行的位置，我们要找到一个链接，使得光标在链接内部
            if (cursor.ch >= startIndex && cursor.ch <= endIndex) {
                // 从匹配的 [text](url) 中提取 url
                const urlMatch = /\(([^)]+)\)/.exec(match[0]); 
                const url = urlMatch[1];
                this.openFolderForURL(url);
                return;
            }
        }
    
        console.warn("Cursor not inside a markdown link");
    }
    
    openFolderForURL(url) {
        try {
            const { shell } = window.require("electron");
            shell.showItemInFolder(url);
        } catch (error) {
            console.error("Failed to open folder:", error);
        }
    }

    // 在当前坐标处插入文本
    async insertText(text) {
        const editor = app.workspace.activeLeaf.view.editor;
        const cursor = editor.getCursor();
        editor.replaceRange(text, cursor);
    }
}