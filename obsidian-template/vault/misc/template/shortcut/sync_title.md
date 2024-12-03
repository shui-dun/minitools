<%*
// 获取当前文件的引用
let file = app.workspace.getActiveFile();
// 其实 let file = tp.file.find_tfile(tp.file.path(true)); 也是一样的
const {Files} = await cJS();
await Files.syncHeader(file, true);
tR = tp.file.selection(); // 避免选中的文本被删除
%>