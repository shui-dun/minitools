<%*
const {Files} = await cJS();
await Files.convertToFolderNote(app.workspace.getActiveFile());
tR = tp.file.selection(); // 避免选中的文本被删除
%>