class WaitLoading {
	async wait() {
		while (!app?.plugins?.plugins?.dataview?.api?.index?.initialized) {
			// 这块如果不了解JS会有点绕
			// promise 接收一个函数作为参数，这个函数有两个参数，resolve 和 reject
			// resolve 是一个函数，resolve被调用时，Promise 的状态会变为完成
			await new Promise(resolve => setTimeout(resolve, 100));
		}
	}
}