```dataviewjs
const {WaitLoading, Task, Utils} = await cJS();
Task.init(dv);

await WaitLoading.wait(dv);

// 任务的执行日期
let dates = Task.daysOfTask(dv.current());
if (dates.length > 0) {
	// 跳过下一次任务
	dv.paragraph(Utils.container(
		Utils.button('跳过下次', async () => {
			await Task.skip(dv.current());
		}),
	));
	dv.paragraph(dates);
}

let mermaid = Task.generateMermaidCode(dv.current());
if (mermaid !== '') {
	dv.paragraph(Utils.wrapInCalloutIfLarge(mermaid, 10, '任务视图'));
}
```
