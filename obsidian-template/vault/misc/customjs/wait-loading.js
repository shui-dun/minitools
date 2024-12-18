class WaitLoading {
	// 等待加载完成
	// folders 表示需要等待加载完成的文件夹列表
	// files 表示需要等待加载完成的文件列表
	async wait(dv, folders) {
		this.dv = dv;
		this.folders = folders || [];
		while (!this.isLoaded()) {
			// 这块如果不了解JS会有点绕
			// promise 接收一个函数作为参数，这个函数有两个参数，resolve 和 reject
			// resolve 是一个函数，resolve被调用时，Promise 的状态会变为完成
			await new Promise(resolve => setTimeout(resolve, 200));
		}
	}

	// 是否加载完成
	isLoaded() {
		if (app?.plugins?.plugins?.dataview?.api?.index?.initialized) {
			return true;
		}
		if (!this.dv.current()) {
			return false;
		}
		// 如果folders为空，则认为需要加载所有文件夹
		if (this.folders.length === 0) {
			return false;
		}
		for (const folder of this.folders) {
			let cacheLen = this.dv.pages(`"${folder}"`).length;
			let realLen = this.getMarkdownFileCountInFolder(folder);
			console.log(`folder: ${folder}, cacheLen: ${cacheLen}, realLen: ${realLen}`);
			if (cacheLen < realLen) {
				return false;
			}
		}
		return true;
	}

	getMarkdownFileCountInFolder(folderPath) {
		const abstractFile = app.vault.getAbstractFileByPath(folderPath);
		if (!abstractFile) {
			console.log(`无法找到文件夹 "${folderPath}"，请检查路径是否正确。`);
			return 0;
		}

		function countMdFiles(fileOrFolder) {
			// 如果有 children 属性则表明是一个文件夹对象
			if ("children" in fileOrFolder && Array.isArray(fileOrFolder.children)) {
				let count = 0;
				for (const child of fileOrFolder.children) {
					count += countMdFiles(child);
				}
				return count;
			} else {
				// 没有 children 属性则为文件对象
				// 若 extension 为 'md' 则计数1，否则0
				if ("extension" in fileOrFolder && fileOrFolder.extension === "md") {
					return 1;
				}
				return 0;
			}
		}

		const mdFileCount = countMdFiles(abstractFile);
		return mdFileCount;
	}
}