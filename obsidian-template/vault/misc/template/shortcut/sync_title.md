<%*
// 获取当前文件的引用
let file = app.workspace.getActiveFile();
// 其实 let file = tp.file.find_tfile(tp.file.path(true)); 也是一样的
if (!file) {
	console.error("No active file.");
	return;
}

// 读取文件内容
let fileText = await app.vault.read(file);

// 获取文件名并去掉扩展名
let fileNameWithoutExtension = file.basename;

// 定义正则表达式匹配 front-matter 和一级标题
const frontMatterRegex = /^---[\s\S]+?---\n/m;
const titleRegex = /^# .+/m;

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
if (titleRegex.test(content)) {
	content = content.replace(titleRegex, `# ${fileNameWithoutExtension}`);
} else {
	// 如果没有一级标题，则在 front-matter 后添加标题
	content = `# ${fileNameWithoutExtension}\n` + content;
}

// 将 front-matter 和更新后的正文重新组合
let updatedFileText = frontMatter + content;

// 将修改后的文本写回文件
await app.vault.modify(file, updatedFileText);

// 通知替换成功
new Notice(`Title replaced with: ${fileNameWithoutExtension}`);
tR = tp.file.selection(); // 避免选中的文本被删除
%>