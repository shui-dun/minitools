<%*
const {Files} = await cJS();
await Files.deleteFolderNote(app.workspace.getActiveFile());
tR = tp.file.selection(); // 避免选中的文本被删除
%>