---
startDate: ""
endDate: ""
habitFilter: "[[水果]]"
startDate2: 2024-11-27
endDate2: 2024-11-30
---
```meta-bind-button
label: ""
icon: "search"
hidden: true
class: ""
tooltip: ""
id: "refresh"
style: primary
actions:
  - type: command
    command: dataview:dataview-force-refresh-views
```
`INPUT[date:startDate]` `->` `INPUT[date:endDate]` `BUTTON[refresh]` 
```dataviewjs
const {WaitLoading, Beautify, Habit} = await cJS();

await WaitLoading.wait(dv);

// 获取开始日期和结束日期
let {startDate, endDate} = Habit.defaultPeriod(dv, dv.current().startDate, dv.current().endDate);

let habits = dv.pages('"habit" and -"habit/habit_history"')
	.where(habit => habit.id)
	.map(habit => {
		return {
			habit: habit,
			todayInfo: Habit.todayHabitInfo(dv, habit),
			periodInfo: Habit.habitInfoBetween(dv, habit, startDate, endDate),
		}
	})
    // .sort(habit => habit.periodInfo.progress);
    .sort(habit => [-habit.habit.target * habit.habit.pointsPerClock, habit.habit.file.name]);

// 计算本周总积分
let totalPoints = habits.values.reduce((acc, habit) => acc + habit.periodInfo.clockPoints, 0);
dv.paragraph(`\`${startDate.toFormat("yy-MM-dd")}\` 至 \`${endDate.toFormat("yy-MM-dd")}\` 的总积分: ${Beautify.num(totalPoints)}`);

let progressStick = (habit) => {
	let width = app.isMobile ? 25 : 100;
	return Beautify.progress(habit.periodInfo.progress, width);
} 

function clockButton(habit) {
	return Beautify.button(Beautify.num2(habit.todayInfo.clockCounts), async () => {
	    await Habit.clock(app.vault.getAbstractFileByPath(habit.habit.file.link.path));
    });
}

dv.table(["习惯", "今日", "进度", "", "积分"], 
    habits.map(habit => [
	    habit.habit.file.link, 
	    clockButton(habit),
	    `\`${Beautify.num2(habit.periodInfo.clockCounts, 2)}/${Beautify.num2(habit.periodInfo.finalTarget)}\``,
    progressStick(habit),
    Beautify.num(habit.periodInfo.clockPoints)])
);
```
```dataviewjs
const {WaitLoading, Beautify, Habit} = await cJS();
Beautify.app = app;
await WaitLoading.wait(dv);

dv.paragraph(Beautify.container(
	Beautify.select(dv.current(), 'habitFilter',
		`dv.pages('"habit" and -"habit/habit_history"').map(p => "[[" + p.file.name + "]]")`, 
		false),
	Beautify.date(dv.current(), 'startDate2'),
	'<code>-></code>',
	Beautify.date(dv.current(), 'endDate2'),
	Beautify.button('查询', null, true),
));
```
