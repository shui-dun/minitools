<%*
const {Note} = await cJS();
Note.init(app.plugins.plugins.dataview.api); // 这个其实比dataviewjs里面获得的dv差了很多功能，例如 .current() 等
await Note.randomNote();
tR = tp.file.selection(); // 避免选中的文本被删除
%>