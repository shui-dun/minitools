<%*
const {Files} = await cJS();
let link = await Files.openLinkFolderUnderCursor();
tR = tp.file.selection(); // 避免选中的文本被删除
%>