<%*
/* 获取当前习惯文件的信息 */
let file = app.workspace.getActiveFile();
const {Habit} = await cJS();
await Habit.clock(file);
tR = tp.file.selection(); // 避免选中的文本被删除
%>