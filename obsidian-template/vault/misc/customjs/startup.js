class StartUp {
    async invoke() {
        const { Files } = await cJS();

        app.vault.on('rename', (file, oldPath) => {
            Files.syncHeader(file, false);
        });

        app.commands.addCommand({
            id: 'shuidun:randomNote',
            name: 'shuidun:randomNote',
            callback: async () => {
                const { Note } = await cJS();
                Note.init(app.plugins.plugins.dataview.api); // 这个其实比dataviewjs里面获得的dv差了很多功能，例如 .current() 等
                await Note.randomNote();
            }
        });
        app.commands.addCommand({
            id: 'shuidun:moveNote',
            name: 'shuidun:moveNote',
            callback: async () => {
                const { Files } = await cJS();
                await Files.moveNote();
            }
        });
        app.commands.addCommand({
            id: 'shuidun:openLinkFolderUnderCursor',
            name: 'shuidun:openLinkFolderUnderCursor',
            callback: async () => {
                const { Files } = await cJS();
                let link = await Files.openLinkFolderUnderCursor();
            }
        });
        app.commands.addCommand({
            id: 'shuidun:refresh',
            name: 'shuidun:refresh',
            callback: async () => {
                await app.workspace.activeLeaf.rebuildView();
            }
        });
        app.commands.addCommand({
            id: 'shuidun:archiveNote',
            name: 'shuidun:archiveNote',
            callback: async () => {
                // 询问是否归档当前文档
                const modalForm = app.plugins.plugins.modalforms.api;
                let ans = await modalForm.openForm({
                    title: "是否归档当前文档",
                    fields: [
                    ],
                });

                if (ans.status != 'ok') {
                    return;
                }
                const { Files } = await cJS();
                await Files.archiveNote(app.workspace.getActiveFile());
            }
        });
        app.commands.addCommand({
            id: 'shuidun:addSubNote',
            name: 'shuidun:addSubNote',
            callback: async () => {
                const { Files } = await cJS();
                await Files.addSubNote(app.workspace.getActiveFile());
            }
        });
        app.commands.addCommand({
            id: 'shuidun:convertExternalLinkFromClipboard',
            name: 'shuidun:convertExternalLinkFromClipboard',
            callback: async () => {
                const { Files } = await cJS();
                let link = await Files.convertExternalLinkFromClipboard();
                Files.insertText(link);
            }
        });
        app.commands.addCommand({
            id: 'shuidun:syncHeader',
            name: 'shuidun:syncHeader',
            callback: async () => {
                // 获取当前文件的引用
                let file = app.workspace.getActiveFile();
                // 其实 let file = tp.file.find_tfile(tp.file.path(true)); 也是一样的
                const { Files } = await cJS();
                await Files.syncHeader(file, true);
            }
        });
        app.commands.addCommand({
            id: 'shuidun:openFrontMatterTemplate',
            name: 'shuidun:openFrontMatterTemplate',
            callback: async () => {
                const currentFile = app.workspace.getActiveFile();
                if (!currentFile) {
                    new Notice("No active file.");
                    return;
                }

                // 获取当前文件路径，去掉文件名，得到当前文件所在的目录
                const currentDir = currentFile.parent.path;
                // 模板文件路径
                const templateFileName = currentDir.replace(/\//g, ".");
                const templateFilePath = `misc/front-matter-template/${templateFileName}.md`;

                // 创建并打开文件
                let templateFile = app.vault.getAbstractFileByPath(templateFilePath);
                if (!templateFile) {
                    await app.vault.create(templateFilePath, '');
                }
                await app.workspace.openLinkText(templateFilePath, "", false);
            }
        });
        app.commands.addCommand({
            id: 'shuidun:deleteNote',
            name: 'shuidun:deleteNote',
            callback: async () => {
                const modalForm = app.plugins.plugins.modalforms.api;
                let ans = await modalForm.openForm({
                    title: "是否删除当前文档",
                    fields: [
                    ],
                });

                if (ans.status != 'ok') {
                    return;
                }
                const { Files } = await cJS();
                await Files.deleteNote(app.workspace.getActiveFile());
            }
        });
        app.commands.addCommand({
            id: 'shuidun:openParent',
            name: 'shuidun:openParent',
            callback: async () => {
                const { Files } = await cJS();
                await Files.openParent();
            }
        });
    }
}