// 当仓库没有加载完成时，等待
async function waitForVaultLoading() {
  while (dv.current() === undefined) {
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  return dv.current();
}

await waitForVaultLoading();

// 从 DateTime 对象中获取本地日期时间
let { DateTime } = dv.luxon;

// 获取今天的0时
let today = DateTime.local().startOf("day");

// 获取一周后的日期
let oneWeekLater = today.plus({ days: 6 });

// 初始化一个空的事件数组
let events = [];

// 检查变量是否为非空数组
function isNotNullOrEmptyArray(variable) {
  return (
    variable !== null &&
    variable !== undefined &&
    Array.isArray(variable) &&
    variable.length > 0
  );
}

// 获取下一个月的年份和月份
function nextMonth(year, month) {
  month++; // 月份增加
  if (month > 12) { // 如果月份大于 12，则增加年份并将月份设置为 1
    year++;
    month = 1;
  }
  return [year, month];
}

// 将事件添加到事件数组的函数
function pushEvent(p, date) {
  events.push({
    title: p.file.link,
    date: date,
    startTime: p.startTime,
    endTime: p.endTime,
  });
}

// 将错误信息添加到事件数组的函数
function pushError(p, msg) {
  events.push({ title: p.file.link, date: today, startTime: "", endTime: msg });
}

// 处理loopWeeks
function handleLoopWeeks(p) {
  if (!isNotNullOrEmptyArray(p.loopWeeks)) {
    return [];
  }
  let ans = [];
  p.loopWeeks.forEach((weekDay) => {
    if (weekDay < 1 || weekDay > 7) { // 检查星期几的值是否有效
      throw new Error("Invalid weekday value");
    }
    let dayOffset = weekDay - today.weekday; // 计算星期几的偏移量
    if (dayOffset < 0) dayOffset += 7; // 如果偏移量小于 0，则加上 7
    while (true) {
      let nextOccurrence = today.plus({ days: dayOffset }); // 计算下一个发生日期
      dayOffset += 7; // 更新偏移量
      if (nextOccurrence <= oneWeekLater) { // 如果下一个发生日期在一周内
        ans.push(nextOccurrence);
      } else {
        break; // 否则退出循环
      }
    }
  });
  return ans;
}

// 处理loopMonths
function handleLoopMonths(p) {
  if (!isNotNullOrEmptyArray(p.loopMonths)) {
    return [];
  }
  let ans = [];
  p.loopMonths.forEach((day) => {
    if (day < 1 || day > 31) { // 检查天数的值是否有效
      throw new Error("Invalid day value");
    }
    let nextOccurrence;
    let year = today.year; // 获取当前年份
    let month = today.month; // 获取当前月份
    while (true) {
      nextOccurrence = DateTime.fromObject({
        year: year,
        month: month,
        day: day,
      }); // 根据年份、月份和天数生成事件下一次发生日期
      if (!nextOccurrence.isValid || nextOccurrence < today) { // 如果日期无效或早于今天
        [year, month] = nextMonth(year, month); // 获取下一个月
      } else if (nextOccurrence <= oneWeekLater) { // 如果日期在一周内
        ans.push(nextOccurrence);
        [year, month] = nextMonth(year, month); // 获取下一个月
      } else {
        break; // 否则退出循环
      }
    }
  });
  return ans;
}

// 处理loopMonths2
function handleLoopMonths2(p) {
  if (!isNotNullOrEmptyArray(p.loopMonths2)) {
    return [];
  }
  let ans = [];
  p.loopMonths2.forEach(([week, weekday]) => {
    // 检查 week 和 weekday 的值是否在有效范围内
    if (week < -5 || week > 5 || weekday < 1 || weekday > 7) {
      throw new Error("Invalid week or weekday value");
    }
    let nextOccurrence; // 定义下一个发生的日期变量
    let month = today.month; // 获取当前月份
    let year = today.year; // 获取当前年份
    while (true) {
      if (week > 0) { // 如果 week 是正数
        let firstDayOfTheMonth = DateTime.fromObject({
          year: year,
          month: month,
          day: 1,
        }); // 获取本月的第一天
        let dayOffset = weekday - firstDayOfTheMonth.weekday; // 计算星期几的偏移量
        if (dayOffset < 0) dayOffset += 7; // 如果偏移量小于 0，则加上 7
        nextOccurrence = firstDayOfTheMonth
          .plus({ days: dayOffset })
          .plus({ weeks: week - 1 }); // 计算下一个发生日期
      } else { // 如果 week 是负数
        let [yearOfNextMonth, monthOfNextMonth] = nextMonth(year, month); // 获取下个月的年份和月份
        let lastDayOfTheMonth = DateTime.fromObject({
          year: yearOfNextMonth,
          month: monthOfNextMonth,
          day: 1,
        }).minus({ days: 1 }); // 获取本月的最后一天
        let dayOffset = weekday - lastDayOfTheMonth.weekday; // 计算星期几的偏移量
        if (dayOffset > 0) dayOffset -= 7; // 如果偏移量大于 0，则减去 7
        nextOccurrence = lastDayOfTheMonth
          .plus({ days: dayOffset })
          .plus({ weeks: week + 1 }); // 计算下一个发生日期
      }
      if (nextOccurrence < today || nextOccurrence.month !== month) { // 如果日期早于今天或月份不同
        [year, month] = nextMonth(year, month); // 获取下一个月
      } else if (nextOccurrence <= oneWeekLater) { // 如果日期在一周内
        [year, month] = nextMonth(year, month); // 获取下一个月
        ans.push(nextOccurrence);
      } else {
        break; // 否则退出循环
      }
    }
  });
  return ans;
}

// 处理loopYears
function handleLoopYears(p) {
  if (!isNotNullOrEmptyArray(p.loopYears)) {
    return [];
  }
  let ans = [];
  p.loopYears.forEach(([month, day]) => {
    let year = today.year; // 获取当前年份
    while (true) {
      let nextOccurrence = DateTime.fromObject({
        year: year,
        month: month,
        day: day,
      }); // 根据年份、月份和天数生成日期
      if (year > oneWeekLater.year) { // 如果年份大于一周后的年份
        break; // 退出循环
      }
      if (!nextOccurrence.isValid || nextOccurrence < today) { // 如果日期无效或早于今天
        year++; // 增加年份
      } else if (nextOccurrence <= oneWeekLater) { // 如果日期在一周内
        ans.push(nextOccurrence);
        year++; // 增加年份
      } else {
        break; // 否则退出循环
      }
    }
  });
  return ans;
}

// 处理loopYears2
function handleLoopYears2(p) {
  if (!isNotNullOrEmptyArray(p.loopYears2)) {
    return [];
  }
  let ans = [];
  p.loopYears2.forEach(([month, week, weekday]) => {
    let year = today.year; // 获取当前年份
    while (true) {
      // 获取当前月份的第一天
      let firstDayOfThisMonth = DateTime.fromObject({ year: year, month: month, day: 1 });
      let nextOccurrence; // 初始化目标日期变量

      if (week > 0) {
        // 如果 week 是正数：计算从月初开始的第 week 个指定 weekday
        let dayOffset = (weekday - firstDayOfThisMonth.weekday + 7) % 7; // 计算星期几的偏移量，确保为非负值
        nextOccurrence = firstDayOfThisMonth.plus({ days: dayOffset }).plus({ weeks: week - 1 }); // 计算目标日期
      } else {
        // 如果 week 是负数：计算从月末开始的倒数第 |week| 个指定 weekday
        let lastDayOfMonth = firstDayOfThisMonth.plus({ months: 1 }).minus({ days: 1 }); // 获取当前月份的最后一天
        let dayOffset = (lastDayOfMonth.weekday - weekday + 7) % 7; // 计算星期几的偏移量，确保为非负值
        nextOccurrence = lastDayOfMonth.minus({ days: dayOffset }).minus({ weeks: -week - 1 }); // 计算目标日期
      }

      if (year > oneWeekLater.year) { // 如果年份大于一周后的年份
        break; // 退出循环
      }
      if (!nextOccurrence.isValid || nextOccurrence < today) { // 如果日期无效或早于今天
        year++; // 增加年份
      } else if (nextOccurrence <= oneWeekLater) { // 如果日期在一周内
        ans.push(nextOccurrence);
        year++; // 增加年份
      } else {
        break; // 否则退出循环
      }
    }
  });
  return ans;
}

// 处理特定日期的事件
function handleSpecificDate(p) {
  if (!isNotNullOrEmptyArray(p.specificDate)) {
    return [];
  }
  var ans = [];
  p.specificDate.forEach((dateString) => {
    let date = DateTime.fromISO(dateString);
    if (!date.isValid) {
      throw new Error("Invalid specific date");
    }
    if (date >= today && date <= oneWeekLater) {
      ans.push(date);
    }
  });
  return ans;
}

// 遍历指定路径下的每个页面
dv.pages(`"${dv.current().file.folder}"`).forEach((p) => {
  try {
    var ans = [];
    ans = ans.concat(handleLoopWeeks(p));
    ans = ans.concat(handleLoopMonths(p));
    ans = ans.concat(handleLoopMonths2(p));
    ans = ans.concat(handleLoopYears(p));
    ans = ans.concat(handleLoopYears2(p));
    ans = ans.concat(handleSpecificDate(p));
    ans.forEach((date) => {
      pushEvent(p, date); // 将事件添加到事件数组
    });
  } catch (error) {
    pushError(p, error.message); // 如果发生错误，记录错误信息
  }
});

// 将事件数组按日期排序
events.sort((a, b) => {
  let dateDiff = a.date - b.date;
  if (dateDiff !== 0) return dateDiff; // 如果日期不同，返回日期差异
  if (a.startTime != null && b.startTime != null) {
    let timeDiff = a.startTime.localeCompare(b.startTime);
    if (timeDiff !== 0) return timeDiff; // 如果开始时间不同，返回时间差异
  }
  let aEndTime = a.endTime || "23:59"; // 如果没有结束时间，设置为 23:59
  let bEndTime = b.endTime || "23:59";
  return aEndTime.localeCompare(bEndTime); // 比较结束时间
});

// 格式化日期和时间
function formatTime(e) {
  let time = e.date.toFormat("MM-dd");
  if (e.startTime || e.endTime) {
    time += ' ';
  }
  if (e.startTime) {
    time += e.startTime;
  }
  if (e.endTime) {
    time += '->' + e.endTime;
  }
  return `<code>${time}</code>`;
}

// 使用 dv.table 显示事件数组
dv.table(
  ["", ""], // 表头为空
  events.map((e) => [
    e.title, // 事件标题
    formatTime(e), // 事件时间
  ])
);
