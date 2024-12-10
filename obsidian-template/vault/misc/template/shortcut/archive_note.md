<%*
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
const {Files} = await cJS();
await Files.archiveNote(app.workspace.getActiveFile());
tR = tp.file.selection(); // 避免选中的文本被删除
%>