<%*
const {Files} = await cJS();

app.vault.on('rename', (file, oldPath) => {
	Files.syncHeader(file, false);
});
%>