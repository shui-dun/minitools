// loopWeeks: 例如[1, 3, 7]，表示每周1、周3、周7
// loopMonths: 例如[1, 7, 31]，表示每月的1号、7号、31号
// loopMonths2: 例如[[2, 6], [-2, 7]]，表示每月第2个周六和倒数第2个周日
// loopYears: 例如[[1, 31], [3, 2]]，表示每年1月31日和3月2日
// startTime: 开始时分，例如12:00，如果为空表示全天事件
// endTime: 结束时分，例如13:00

let { DateTime } = dv.luxon;
let today = DateTime.local().startOf("day");
let oneWeekLater = today.plus({ days: 6 });
let events = [];
function isNotNullOrEmptyArray(variable) {
  return (
    variable !== null &&
    variable !== undefined &&
    Array.isArray(variable) &&
    variable.length > 0
  );
}
function nextMonth(year, month) {
  month++;
  if (month > 12) {
    year++;
    month = 1;
  }
  return [year, month];
}
function pushEvent(p, date) {
  events.push({
    title: p.file.link,
    date: date,
    startTime: p.startTime,
    endTime: p.endTime,
  });
}
function pushError(p, msg) {
  events.push({ title: p.file.link, date: today, startTime: "", endTime: msg });
}
dv.pages('"计划/loop"').forEach((p) => {
  try {
    if (isNotNullOrEmptyArray(p.loopWeeks)) {
      p.loopWeeks.forEach((weekDay) => {
        if (weekDay < 1 || weekDay > 7) {
          throw new Error("Invalid weekday value");
        }
        let dayOffset = weekDay - today.weekday;
        if (dayOffset < 0) dayOffset += 7;
        while (true) {
          let nextOccurrence = today.plus({ days: dayOffset });
          dayOffset += 7;
          if (nextOccurrence <= oneWeekLater) {
            pushEvent(p, nextOccurrence);
          } else {
            break;
          }
        }
      });
    } else if (isNotNullOrEmptyArray(p.loopMonths)) {
      p.loopMonths.forEach((day) => {
        if (day < 1 || day > 31) {
          throw new Error("Invalid day value");
        }
        let nextOccurrence;
        let year = today.year;
        let month = today.month;
        while (true) {
          nextOccurrence = DateTime.fromObject({
            year: year,
            month: month,
            day: day,
          });
          if (!nextOccurrence.isValid || nextOccurrence < today) {
            [year, month] = nextMonth(year, month);
          } else if (nextOccurrence <= oneWeekLater) {
            pushEvent(p, nextOccurrence);
            [year, month] = nextMonth(year, month);
          } else {
            break;
          }
        }
      });
    } else if (isNotNullOrEmptyArray(p.loopMonths2)) {
      p.loopMonths2.forEach(([week, weekday]) => {
        if (week < -5 || week > 5 || weekday < 1 || weekday > 7) {
          throw new Error("Invalid week or weekday value");
        }
        let nextOccurrence;
        let month = today.month;
        let year = today.year;
        while (true) {
          if (week > 0) {
            let firstDayOfTheMonth = DateTime.fromObject({
              year: year,
              month: month,
              day: 1,
            });
            let dayOffset = weekday - firstDayOfTheMonth.weekday;
            if (dayOffset < 0) dayOffset += 7;
            nextOccurrence = firstDayOfTheMonth
              .plus({ days: dayOffset })
              .plus({ weeks: week - 1 });
          } else {
            let [yearOfNextMonth, monthOfNextMonth] = nextMonth(year, month);
            let lastDayOfTheMonth = DateTime.fromObject({
              year: yearOfNextMonth,
              month: monthOfNextMonth,
              day: 1,
            }).minus({ days: 1 });
            let dayOffset = weekday - lastDayOfTheMonth.weekday;
            if (dayOffset > 0) dayOffset -= 7;
            nextOccurrence = lastDayOfTheMonth
              .plus({ days: dayOffset })
              .plus({ weeks: week + 1 });
          }
          if (nextOccurrence < today || nextOccurrence.month !== month) {
            [year, month] = nextMonth(year, month);
          } else if (nextOccurrence <= oneWeekLater) {
            [year, month] = nextMonth(year, month);
            pushEvent(p, nextOccurrence);
          } else {
            break;
          }
        }
      });
    } else if (isNotNullOrEmptyArray(p.loopYears)) {
      p.loopYears.forEach(([month, day]) => {
        let year = today.year;
        while (true) {
          let nextOccurrence = DateTime.fromObject({
            year: year,
            month: month,
            day: day,
          });
          if (year > oneWeekLater.year) {
            break;
          }
          if (!nextOccurrence.isValid || nextOccurrence < today) {
            year++;
          } else if (nextOccurrence <= oneWeekLater) {
            pushEvent(p, nextOccurrence);
            year++;
          } else {
            break;
          }
        }
      });
    }
  } catch (error) {
    pushError(p, error.message);
  }
});
events.sort((a, b) => {
  let dateDiff = a.date - b.date;
  if (dateDiff !== 0) return dateDiff;
  if (a.startTime != null && b.startTime != null) {
    let timeDiff = a.startTime.localeCompare(b.startTime);
    if (timeDiff !== 0) return timeDiff;
  }
  let aEndTime = a.endTime || "23:59";
  let bEndTime = b.endTime || "23:59";
  return aEndTime.localeCompare(bEndTime);
});
dv.table(
  ["", ""],
  events.map((e) => [
    e.title,
    `<code>${e.date.toFormat("yyyy-MM-dd")} ${e.startTime || ""}->${
      e.endTime || ""
    }</code>`,
  ])
);
