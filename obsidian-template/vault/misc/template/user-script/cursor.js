function cursor(n) {
	if (!app.isMobile) {
		return `<% tp.file.cursor(${n}) %>`;
	}
	return "";
}

module.exports = cursor