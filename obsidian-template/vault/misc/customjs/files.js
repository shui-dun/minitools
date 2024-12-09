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
        if (!file) {
            console.error("No active file.");
            return;
        }

        let fileName = file.basename.split('.').shift();
        let parentDir = file.parent.path;
        let parentDirName = parentDir.split('/').pop();

        return fileName == parentDirName;
    }

    // 把一个文件转化为folder note
    async convertToFolderNote(file) {
        if (!file) {
            console.error("No active file.");
            return;
        }

        let fileName = file.basename.split('.').shift();
        let parentDir = file.parent.path;
        let parentDirName = parentDir.split('/').pop();

        // 如果文件名和文件夹名相同，直接返回
        if (fileName == parentDirName) {
            return;
        }

        // 创建文件夹
        let folderPath = parentDir + '/' + fileName;
        await app.vault.createFolder(folderPath);

        // 移动文件
        let newFilePath = folderPath + '/' + fileName + '.md';
        await app.vault.rename(file, newFilePath);

        // 将链接的附件全部移动到新的文件夹的assets目录下
        let cache = app.metadataCache.getFileCache(file);
        let attachmentsLinks = [];
        if (cache) {
            // 添加 embeds，links，frontmatterLinks
            attachmentsLinks = cache.embeds.concat(cache.links).concat(cache.frontmatterLinks);
            attachmentsLinks = attachmentsLinks.map(attachment => attachment.link);
        }

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
        let attachmentsToMove = attachments.filter(attachment => {
            let backlinks = app.metadataCache.getBacklinksForFile(attachment);
            return backlinks.data.size == 1;
        });

        let assetsPath = folderPath + '/assets';
        await app.vault.createFolder(assetsPath);

        for (let attachment of attachmentsToMove) {
            let attachmentPath = attachment.path;
            let newAttachmentPath = assetsPath + '/' + attachmentPath.split('/').pop();
            await app.vault.rename(attachment, newAttachmentPath);
        }
    }
}