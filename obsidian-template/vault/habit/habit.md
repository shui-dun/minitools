---
startDate: ""
endDate: ""
startDate2: ""
endDate2: ""
habitFilter: "[[早睡]]"
---
```dataviewjs
const {WaitLoading, Utils, Habit} = await cJS();
Habit.init(dv, this.container);
await WaitLoading.wait();

dv.paragraph(
  Utils.container(
    Utils.date(dv.current(), 'startDate'),
    `<code>-></code>`,
    Utils.date(dv.current(), 'endDate'),
    Utils.button('搜', null, true)
  )
);

// 获取开始日期和结束日期
let {startDate, endDate} = Habit.defaultPeriod(dv.current().startDate, dv.current().endDate);

let habits = dv.pages('"habit" and -"habit/habit_history"')
	.where(habit => habit.id)
	.map(habit => {
		return {
			habit: habit,
			todayInfo: Habit.todayHabitInfo(habit),
			periodInfo: Habit.habitInfoBetween(habit, startDate, endDate),
		}
	})
    // .sort(habit => habit.periodInfo.progress);
    .sort(habit => [-habit.habit.target * habit.habit.pointsPerClock, habit.habit.file.name]);

// 计算本周总积分
let totalPoints = habits.values.reduce((acc, habit) => acc + habit.periodInfo.clockPoints, 0);
dv.paragraph(`\`${startDate.toFormat("yy-MM-dd")}\` 至 \`${endDate.toFormat("yy-MM-dd")}\` 的总积分: ${Utils.num(totalPoints)}`);

let progressStick = (habit) => {
	let width = app.isMobile ? 25 : 100;
	return Utils.progress(habit.periodInfo.progress, width);
} 

function clockButton(habit, decimalPlaces) {
	return Utils.button(Utils.num2(habit.todayInfo.clockCounts, decimalPlaces), async () => {
	    await Habit.clock(app.vault.getAbstractFileByPath(habit.habit.file.link.path));
    });
}

dv.table(["习惯", "今日", "进度", "", "积分"], 
    habits.map(habit => {
		let decimalPlaces = habit.habit.decimalPlaces;
		if (decimalPlaces == null) {
			decimalPlaces = 2;
		}
	    return [
		    habit.habit.file.link, 
		    clockButton(habit, decimalPlaces),
		    `\`${Utils.num2(habit.periodInfo.clockCounts, decimalPlaces)}/${Utils.num2(habit.periodInfo.finalTarget, decimalPlaces)}\``,
		    progressStick(habit),
		    Utils.num(habit.periodInfo.clockPoints)
	    ];
    })
);
```
```dataviewjs
const {Ai} = await cJS();
dv.paragraph("✨ ​**今日格言**  \n" + await Ai.getDailyQuote());
```
### 趋势
```dataviewjs
const {WaitLoading, Utils, Habit} = await cJS();
Habit.init(dv, this.container);
await WaitLoading.wait();

let refreshTarget = dv.current().file.name + "#趋势";

dv.paragraph(Utils.container(
	Utils.select(dv.current(), 'habitFilter',
		`dv.pages('"habit" and -"habit/habit_history"').map(p => "[[" + p.file.name + "]]")`, 
		false),
	Utils.date(dv.current(), 'startDate2'),
	'<code>-></code>',
	Utils.date(dv.current(), 'endDate2'),
	Utils.button('查询', null, refreshTarget),
));
if (dv.current().habitFilter) {
	Habit.habitTrend(dv.page(dv.current().habitFilter), dv.current().startDate2, dv.current().endDate2);
}
```
