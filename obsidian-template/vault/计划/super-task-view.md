```dataviewjs
const {WaitLoading, Task, Utils, Files} = await cJS();
Task.init(dv);

await WaitLoading.wait();

// 任务的执行日期
let dates = Task.daysOfTask(dv.current());
if (dates.length > 0) {
	// 跳过下一次任务
	dv.paragraph(Utils.container(
		Utils.button('跳过下次', async () => {
			await Task.skip(dv.current());
		}),
		...dates.map(t => t.toFormat("yy-MM-dd"))
	));
}

await Task.showTasks(dv.current().file.path);
```
