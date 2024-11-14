class WaitLoading {
	async wait(dv, ...files) {
		async function waitForVaultLoading() {
			while (true) {
				let flag = true;
				for (let file of files) {
					if (dv.page(file) === undefined) {
						flag = false;
						break;
					}
				}
				if (dv.current() === undefined) {
					flag = false;
				}
				if (flag) {
					break;
				} else {
					await new Promise(resolve => setTimeout(resolve, 200));
				}
			}
			return;
		}
		await waitForVaultLoading();
	}
}