<%*
const {Note} = await cJS();
Note.app = app;
Note.dv = app.plugins.plugins.dataview.api;
await Note.randomNote();
tR = tp.file.selection(); // 避免选中的文本被删除
%>