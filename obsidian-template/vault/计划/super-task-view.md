```dataviewjs
const {WaitLoading, Task, Beautify} = await cJS();
Task.dv = dv;
Task.app = app;

await WaitLoading.wait(dv);

// 任务的执行日期
let dates = Task.daysOfTask(dv.current());
if (dates.length > 0) {
	// 跳过下一次任务
	dv.paragraph(Beautify.container(
		Beautify.button('跳过下次', async () => {
			await Task.skip(dv.current());
		}),
	));
	dv.paragraph(dates);
}

let mermaid = Task.generateMermaidCode(dv.current());
if (mermaid !== '') {
	dv.paragraph(Beautify.wrapInCalloutIfLarge(mermaid, 10, '任务视图'));
}
```
