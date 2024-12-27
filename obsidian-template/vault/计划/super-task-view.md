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

// mermaid画图已被废弃，因为不够灵活，不能手动排序等
// let mermaid = Task.generateMermaidCode(dv.current());
// if (mermaid !== '') {
// 	dv.paragraph(Utils.wrapInCalloutIfLarge(mermaid, 10, '任务视图'));
// }

// due的待办事项
let path = dv.current().file.path;
if (Files.isFolderNote(path)) {
    path = dv.current().file.folder;
}

function sortDue(due) {
    if (typeof due === 'number') { return [1, -due]; }
    return [0, due];
}

const tasks = dv.pages(`"${path}"`)
    .file.tasks
    .where(t => t.due && !t.completed)
    // due的值可以是0~4的数字，数字越大优先级越大
    // 也可以是日期，如 2021-12-31
    // 日期排在数字之前
    // 日期升序排序，数字降序排序
    .sort(t => sortDue(t.due));

if (tasks.length > 0) {
    dv.taskList(tasks);
}
```
