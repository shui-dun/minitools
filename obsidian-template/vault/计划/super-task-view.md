```dataviewjs
async function waitForVaultLoading(){while(dv.current()===undefined){await new Promise(resolve=>setTimeout(resolve,200))}return dv.current()}await waitForVaultLoading();

// 查看父任务
let superTask = dv.current().superTask;
if (superTask != null) {
	dv.paragraph("父任务：" + dv.current().superTask);
}

// 查看子任务
let subTasks = dv.pages('"计划"')
	.filter(p => p.superTask && p.superTask.path == dv.current().file.link.path);

if (subTasks.length != 0) {
	await dv.view('misc/dataview-scripts/calendar', {"pages": subTasks, "allowZeroPriority": true});
}
```
