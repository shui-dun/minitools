class WaitLoading {
	async wait() {
		if (app.plugins.plugins.dataview.api.index.initialized) {
			return;
		}
		// 这块如果不了解JS会有点绕
		// promise 接收一个函数作为参数，这个函数有两个参数，resolve 和 reject
		// resolve 是一个函数，resolve被调用时，Promise 的状态会变为完成
		// 下述代码中，当 dataview:index-ready 发生时，resolve 会被调用，Promise 就会完成
		return new Promise(resolve => {
			app.metadataCache.on("dataview:index-ready", resolve);
		});
	}
}