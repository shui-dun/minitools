```dataviewjs
const {WaitLoading, Note, Beautify} = await cJS();
Note.app = app;
Note.dv = dv;
await WaitLoading.wait(dv);

dv.paragraph(Beautify.container(
	Beautify.button('简单', async () => {
		await Note.reviewEasy();
	}),
	Beautify.button('不错', async () => {
		await Note.reviewGood();
	}),
	Beautify.button('困难', async () => {
		await Note.reviewHard();
	}),
	Beautify.button('推迟', async () => {
		await Note.reviewDelay();
	}),
	Beautify.button('下篇', async () => {
		await Note.nextNote();
	}),
	Beautify.button('随机', async () => {
		await Note.randomNote();
	}),
));
```