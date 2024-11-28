```dataviewjs
const {WaitLoading, Note, Utils} = await cJS();
Note.init(dv);
await WaitLoading.wait(dv);

dv.paragraph(Utils.container(
	Utils.button('简单', async () => {
		await Note.reviewEasy();
	}),
	Utils.button('不错', async () => {
		await Note.reviewGood();
	}),
	Utils.button('困难', async () => {
		await Note.reviewHard();
	}),
	Utils.button('推迟', async () => {
		await Note.reviewDelay();
	}),
	Utils.button('下篇', async () => {
		await Note.nextNote();
	}),
	Utils.button('随机', async () => {
		await Note.randomNote();
	}),
));
```