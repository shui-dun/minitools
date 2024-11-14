class Habit {
	defaultPeriod(dv, startDate, endDate) {
		startDate = startDate || dv.date('sow').minus(dv.duration('1 days')); // 默认从周日开始
		endDate = endDate || startDate.plus({ days: 6 }); // 默认是一周
		return {startDate, endDate};
	}

	habitInfoBetween(dv, habit, startDate, endDate) {
		let diff = Math.floor((endDate - startDate) / (24 * 60 * 60 * 1000)) + 1;

		let historyFile = dv.page(`habit/habit_history/${habit.id}`);
		let clockCounts = 0;
		if (historyFile && historyFile.historyDates && historyFile.historyCounts) {
			for (let i = historyFile.historyDates.length - 1; i >= 0; i--) {
				let date = historyFile.historyDates[i];
				if (date >= startDate && date <= endDate) {
					clockCounts += historyFile.historyCounts[i];
				} else if (date < startDate) {
					break;
				}
			}
		}
		let finalTarget = habit.target * diff / 7;
		let progress = clockCounts / finalTarget;
		let clockPoints = clockCounts * habit.pointsPerClock;
		return { clockCounts, finalTarget, progress, clockPoints};
	}

	todayHabitInfo(dv, habit) {
		let today = dv.date('today');
		let historyFile = dv.page(`habit/habit_history/${habit.id}`);
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
		return {clockCounts};
	}
	
	async clock(file) {
		const modalForm = app.plugins.plugins.modalforms.api;
		const fileName = file.basename;
		const habitID = app.metadataCache.getFileCache(file)?.frontmatter.id;

		/* 获取当前日期 */
		let todayDate = moment().format("YYYY-MM-DD");
		const iswalk = (fileName == '走路');
		const isSleep = (fileName == '早睡');
		if (iswalk) {
			todayDate = moment().subtract(3, 'days').format("YYYY-MM-DD");
			new Notice(`对于走路，打卡时间被设置为3天前，即${todayDate}`);
		}

		/* 让用户输入打卡次数 */
		let count = 0;
		if (isSleep) {
			const currentTime = moment();
			let startTime = moment("22:30", "HH:mm");
			let endTime = moment("23:30", "HH:mm");
			if (currentTime.isAfter(endTime) || currentTime.isBefore(moment("12:00", "HH:mm"))) {
				count = 0;
			} else if (currentTime.isBetween(startTime, endTime)) {
				const  minutesSinceStartTime = currentTime.diff(startTime, 'minutes');
				count = 1 - (minutesSinceStartTime / endTime.diff(startTime, 'minutes')); // 从1逐渐降到0
			} else {
				count = 1;
			}
			count = parseFloat(count.toFixed(2));
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
		if (count == 0) {
			return;
		}

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
				frontmatter["historyDates"].push(todayDate);
				frontmatter["historyCounts"].push(count);
				newCount = count;
			} else {
				// 如果今天已有记录，则累加或减少打卡次数
				if (isSleep) {
					frontmatter["historyCounts"][todayIndex] = 0;
				}
				frontmatter["historyCounts"][todayIndex] += count;
				newCount = frontmatter["historyCounts"][todayIndex];
				// 如果打卡次数为零或负数，删除该日期记录
				if (frontmatter["historyCounts"][todayIndex] <= 0) {
					newCount = 0;
					frontmatter["historyDates"].splice(todayIndex, 1);
					frontmatter["historyCounts"].splice(todayIndex, 1);
				}
			}
		});

		/* 提示打卡完成 */
		new Notice(`打卡${count}次，今日共打卡${newCount}次`);

		// 刷新界面
		setTimeout(function() {
			app.commands.executeCommandById('dataview:dataview-force-refresh-views')
		}, 300);
	}
}
