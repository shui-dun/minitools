class Habit {
	init(dv, container) {
		this.dv = dv;
		this.container = container;
	}

	// 周视图的默认时间段
	defaultPeriod(startDate, endDate) {
		const today = this.dv.date('today');
		let weekDay = today.weekday; // 1=Monday, 7=Sunday
		if (weekDay === 1) {
			// 今天是周一，取上一个周一
			startDate = startDate || today.minus({ days: 7 });
		} else {
			// 否则，取本周周一
			startDate = startDate || today.minus({ days: weekDay - 1 });
		}
		endDate = endDate || startDate.plus({ days: 6 }); // 默认是一周
		return { startDate, endDate };
	}

	// 月视图的默认时间段
	defaultMonthPeriod(startDate, endDate) {
		// 默认从30天前开始
		startDate = startDate || this.dv.date('today').minus(this.dv.duration('30 days'));
		endDate = endDate || startDate.plus({ days: 30 }); // 默认是一个月，但不能超过今天
		if (endDate > this.dv.date('today')) {
			endDate = this.dv.date('today');
		}
		return { startDate, endDate };
	}

	habitInfoBetween(habit, startDate, endDate, needClockDetails = false) {
		let diff = Math.floor((endDate - startDate) / (24 * 60 * 60 * 1000)) + 1;

		let historyFile = this.dv.page(`habit/habit_history/${habit.id}`);
		let clockCounts = 0;
		let clockDetails = new Map();
		if (historyFile && historyFile.historyDates && historyFile.historyCounts) {
			for (let i = historyFile.historyDates.length - 1; i >= 0; i--) {
				let date = historyFile.historyDates[i];
				if (date >= startDate && date <= endDate) {
					clockCounts += historyFile.historyCounts[i];
					if (needClockDetails) {
						clockDetails.set(date.toFormat('yyyy-MM-dd'), historyFile.historyCounts[i]);
					}
				} else if (date < startDate) {
					break;
				}
			}
		}
		let finalTarget = habit.target * diff / 7;
		let progress = clockCounts / finalTarget;
		let initPointsPerDay = (habit.initPoints ?? 0) / 7;
		let clockPoints = clockCounts * habit.pointsPerClock + initPointsPerDay * diff;
		return { clockCounts, finalTarget, progress, clockPoints, clockDetails };
	}

	todayHabitInfo(habit) {
		let today = this.dv.date('today');
		let historyFile = this.dv.page(`habit/habit_history/${habit.id}`);
		let clockCounts = 0;
		if (historyFile && historyFile.historyDates && historyFile.historyCounts) {
			let i = historyFile.historyDates.length - 1;
			if (i >= 0) {
				let date = historyFile.historyDates[i];
				if (today.ts == date.ts) {
					clockCounts = historyFile.historyCounts[i];
				}
			}
		}
		return { clockCounts };
	}

	// 时间趋势展示
	// 随着时间变化，打卡情况的变化折线图（横坐标是日期，纵坐标是打卡次数）
	habitTrend(habit, startDate, endDate) {
		if (habit == null) {
			return;
		}
		({ startDate, endDate } = this.defaultMonthPeriod(startDate, endDate));
		let { clockCounts, finalTarget, progress, clockPoints, clockDetails } = this.habitInfoBetween(habit, startDate, endDate, true);
		// 生成折线图数据
		let labels = [];
		let data = [];
		let targets = [];
		let target = finalTarget / ((endDate - startDate) / (24 * 60 * 60 * 1000) + 1);

		let currentDate = startDate;
		while (currentDate <= endDate) {
			labels.push(currentDate.toFormat('yyyy-MM-dd'));
			if (clockDetails.has(currentDate.toFormat('yyyy-MM-dd'))) {
				data.push(clockDetails.get(currentDate.toFormat('yyyy-MM-dd')));
			} else {
				data.push(0);
			}
			targets.push(target);
			currentDate = currentDate.plus({ days: 1 });
		}
		const chartData = {
			type: 'line',
			data: {
				labels: labels,
				datasets: [{
					label: '打卡次数',
					data: data,
					fill: false,
					borderColor: 'rgb(68,138,242)',
					tension: 0.1
				}, {
					label: '目标次数',
					data: targets,
					fill: false,
					borderColor: 'rgb(192, 75, 192)',
					tension: 0.1
				}]
			},
		};
		window.renderChart(chartData, this.container);
	}

	// 习惯打卡
	// refresh: 是否刷新界面
	async clock(file, refresh = true) {
		const modalForm = app.plugins.plugins.modalforms.api;
		const fileName = file.basename;
		const fm = app.metadataCache.getFileCache(file)?.frontmatter;
		const habitID = fm.id;

		/* 获取当前日期 */
		let todayDate = null;
		{
			let now = moment(); // 这个now是要被魔改的，为了防止被使用，限制其作用域
			if (now.hour() < 4) {
				now.subtract(1, 'day');
			}
			if (fm.daysOffset != null) {
				now = now.add(fm.daysOffset, 'days');
				new Notice(`打卡时间被设置为${Math.abs(fm.daysOffset)}天${fm.daysOffset > 0 ? '后' : '前'}，即${now.format('YYYY-MM-DD')}`);
			}
			todayDate = now.format("YYYY-MM-DD");
		}

		/* 让用户输入打卡次数 */
		let count = 0;
		if (fileName == '早睡') {
			const currentTime = moment();
			const isWeekend = await this.checkWeekend();
			count = this.timeToNum(currentTime, isWeekend);
			count = parseFloat(count.toFixed(2));
		} else if (fileName == '笔记') {
			// 确保当前笔记含有sr属性
			if (!this.dv.current().sr) {
				count = 0;
				new Notice(`当前笔记没有设置复习属性，无法打卡`);
				return;
			} else {
				// 复习了当前笔记
				// 获得当前笔记的size(10KB)
				count = parseFloat((this.dv.current().file.size / 10240).toFixed(2));
			}
		} else {
			let countInput = await modalForm.openForm({
				title: "",
				fields: [
					{
						name: "count",
						label: "打卡次数",
						description: "负数为取消打卡，不填则表示打卡一次",
						input: { type: "number" },
					},
				],
			});
			if (countInput.status == 'ok') {
				count = countInput.count.value;
				if (count == null) {
					count = 1;
				}
			} else { // 被取消了
				count = 0;
			}
		}
		if (count == 0 && !fm.once) {
			new Notice(`打卡0次`);
			return;
		}
		count = parseFloat(count.toFixed(2));

		/* 定义历史记录文件路径 */
		const historyFilePath = `habit/habit_history/${habitID}.md`;
		let historyFile = app.vault.getAbstractFileByPath(historyFilePath);
		if (!historyFile) {
			await app.vault.create(historyFilePath, '');
			historyFile = app.vault.getAbstractFileByPath(historyFilePath);
		}
		/* 读取历史记录文件中的 frontmatter */
		let newCount = 0; // 今日共打卡次数
		await app.fileManager.processFrontMatter(historyFile, (frontmatter) => {
			/* 初始化历史记录数据 */
			if (!frontmatter["historyDates"]) frontmatter["historyDates"] = [];
			if (!frontmatter["historyCounts"]) frontmatter["historyCounts"] = [];

			/* 查找今天的打卡记录 */
			let lastIndex = frontmatter["historyDates"].length - 1;
			let todayIndex = (lastIndex >= 0 && frontmatter["historyDates"][lastIndex] === todayDate) ? lastIndex : -1;

			/* 更新今日的打卡次数 */
			if (todayIndex === -1) {
				// 如果今天没有记录，则添加新记录
				newCount = count;
				if (!fm.allowNegtive && newCount < 0) {
					newCount = 0;
				}
				if (newCount != 0) {
					frontmatter["historyDates"].push(todayDate);
					frontmatter["historyCounts"].push(count);
				}
			} else {
				// 如果今天已有记录，则累加或减少打卡次数
				if (fm.once) {
					frontmatter["historyCounts"][todayIndex] = 0;
				}
				newCount = frontmatter["historyCounts"][todayIndex] + count;
				newCount = parseFloat(newCount.toFixed(2));
				// 如果打卡次数为零或负数，删除该日期记录
				if (!fm.allowNegtive && newCount <= 0) {
					newCount = 0;
					frontmatter["historyDates"].splice(todayIndex, 1);
					frontmatter["historyCounts"].splice(todayIndex, 1);
				} else {
					frontmatter["historyCounts"][todayIndex] = newCount;
				}
			}
		});

		/* 提示打卡完成 */
		new Notice(`打卡${count}次，今日共打卡${newCount}次`);

		if (refresh) {
			// 刷新界面
			setTimeout(function () {
				app.commands.executeCommandById('dataview:dataview-force-refresh-views')
			}, 400);
		}
	}

	timeToNum(timeStr, isWeekend) {
		let currentTime = timeStr;
		// 如果是字符串类型
		if (typeof timeStr == 'string') {
			currentTime = moment(timeStr, "HH:mm");
		}

		// 定义时间点
		let t0 = moment("12:00", "HH:mm");
		let t1 = moment("22:30", "HH:mm");
		let t2 = moment("23:00", "HH:mm");
		let t3 = moment("00:00", "HH:mm").add(1, 'days');
		// 如果是周末，可以迟点睡觉
		if (isWeekend) {
			t0 = moment("12:00", "HH:mm");
			t1 = moment("23:00", "HH:mm");
			t2 = moment("23:30", "HH:mm");
			t3 = moment("00:30", "HH:mm").add(1, 'days'); // 确保跨午夜比较正确
		}

		// 调整当前时间以处理跨午夜情况
		let adjustedCurrentTime = currentTime;
		if (currentTime.isBefore(t0)) {
			adjustedCurrentTime = currentTime.add(1, 'days');
		}

		let score;

		if (adjustedCurrentTime.isBetween(t0, t1, null, '[]')) {
			// t0-t1: 恒定为1
			score = 1;
		} else if (adjustedCurrentTime.isBetween(t1, t2, null, '[]')) {
			// t1-t2: 1->0
			const progress = (adjustedCurrentTime - t1) / (t2 - t1);
			score = 1 - progress;
		} else if (adjustedCurrentTime.isBetween(t2, t3, null, '[]')) {
			// t2-t3: 0->-1
			const progress = (adjustedCurrentTime - t2) / (t3 - t2);
			score = -progress;
		} else {
			// t3-t0: 恒定为-1
			score = -1;
		}

		return parseFloat(score.toFixed(2));
	}
	// timeToNum 的测试用例：
	// const testCases = [
	// 	// 12:00~22:30 区间测试
	// 	["11:59", -1],    // t0 边界值略小
	// 	["12:00", 1],     // t0 边界值相等
	// 	["12:01", 1],     // t0 边界值略大
	// 	["22:29", 1],     // t1 边界值略小
	// 	["22:30", 1],     // t1 边界值相等
	// 	
	// 	// 22:30~23:30 区间测试
	// 	["22:31", 0.98],  // t1 边界值略大
	// 	["23:00", 0.5],   // 中间值
	// 	["23:29", 0.02],  // t2 边界值略小
	// 	["23:30", 0],     // t2 边界值相等
	// 	
	// 	// 23:30~01:30 区间测试
	// 	["23:31", -0.01], // t2 边界值略大
	// 	["00:30", -0.5],  // 中间值
	// 	["01:29", -0.99], // t3 边界值略小
	// 	["01:30", -1],    // t3 边界值相等
	// 	
	// 	// 01:30~12:00 区间测试
	// 	["01:31", -1],    // t3 边界值略大
	// 	["02:00", -1],
	// 	["11:59", -1]
	// ];
	// 
	// // 运行测试
	// testCases.forEach(([time, expected]) => {
	// 	const result = timeToNum(time);
	// 	console.log(`Time: ${time}, Expected: ${expected}, Got: ${result}, ${result === expected ? '✓' : '✗'}`);
	// });

	// 判断是否是休息日
	// 考虑到请假、节假日等因素，还是让用户手动填写
	async checkWeekend() {
		const modalForm = app.plugins.plugins.modalforms.api;
		let ans = await modalForm.openForm({
			title: "是否是休息日",
			fields: [],
		});
		return ans.status == 'ok';
	}

}
