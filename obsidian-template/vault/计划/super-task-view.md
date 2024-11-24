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

// 查看父任务
let superTask = dv.current().superTask;
if (superTask != null) {
	dv.paragraph("父任务：" + superTask);
}

// 查看依赖的任务
let beforeTasks = dv.current().beforeTasks;
if (beforeTasks != null && beforeTasks.length != 0) {
	dv.paragraph("依赖于：" + beforeTasks);
}

// 查看子任务
let subTasks = dv.pages('"计划"')
	.filter(p => p.superTask && p.superTask.path == dv.current().file.link.path);

if (subTasks.length != 0) {
	// await dv.view('misc/dataview-scripts/calendar', {"pages": subTasks, "allowZeroPriority": true});
	Task.renderTasks(subTasks, true);
}
```
