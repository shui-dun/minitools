```dataviewjs
const {WaitLoading, Utils, Habit} = await cJS();
Habit.init(dv, this.container);
await WaitLoading.wait();

// 获取开始日期和结束日期
let {startDate, endDate} = Habit.defaultPeriod(dv.current().startDate, dv.current().endDate);

let todayInfo = Habit.todayHabitInfo(dv.current());
let periodInfo = Habit.habitInfoBetween(dv.current(), startDate, endDate);

dv.paragraph(Utils.container(
	Utils.button(`今日打卡`, async () => {
		let file = app.workspace.getActiveFile();
		await Habit.clock(file);
	}), 
	`${Utils.num(todayInfo.clockCounts)} 次,`,
	`本周打卡 ${Utils.num(periodInfo.clockCounts)} / ${Utils.num(periodInfo.finalTarget)},`,
	`获得积分 ${Utils.num(periodInfo.clockPoints)}`
))
```