```dataviewjs
const {WaitLoading, Beautify, Habit} = await cJS();

await WaitLoading.wait(dv);

// 获取开始日期和结束日期
let {startDate, endDate} = Habit.defaultPeriod(dv, dv.current().startDate, dv.current().endDate);

let todayInfo = Habit.todayHabitInfo(dv, dv.current());
let periodInfo = Habit.habitInfoBetween(dv, dv.current(), startDate, endDate);

dv.paragraph(`今日打卡 ${Beautify.num(todayInfo.clockCounts)} 次，本周打卡 ${Beautify.num(periodInfo.clockCounts)} / ${Beautify.num(periodInfo.finalTarget)}，获得积分 ${Beautify.num(periodInfo.clockPoints)}`);
```
```meta-bind-button
label: 打卡
icon: badge-check
hidden: false
class: ""
tooltip: ""
id: "clock"
style: primary
actions:
  - type: command
    command: templater-obsidian:misc/template/shortcut/habit_clock.md
```
