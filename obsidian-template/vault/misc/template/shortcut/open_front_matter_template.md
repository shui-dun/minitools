<%*
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
// tR = tp.file.selection(); // 避免选中的文本被删除，但对于有文件被打开的情况，不需要加上这句话
%>