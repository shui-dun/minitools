class Task {
	init(dv) {
		this.dv = dv;
	}

	daysOfTask(p) {
		let {DateTime} = this.dv.luxon;
		let today = DateTime.local().startOf("day");
		let endDate = today.plus({
			days: 13
		});
		
		let isNotNullOrEmptyArray = (variable) => {
			return (variable !== null && variable !== undefined && Array.isArray(variable) && variable.length > 0)
		}

		let nextMonth = (year, month) => {
			month++;
			if (month > 12) {
				year++;
				month = 1
			}
			return [year, month]
		}
		
		let handleLoopWeeks = (p) => {
			if (!isNotNullOrEmptyArray(p.loopWeeks)) {
				return []
			}
			let ans = [];
			p.loopWeeks.forEach((weekDay) => {
				if (weekDay < 1 || weekDay > 7) {
					throw new Error("Invalid weekday value");
				}
				let dayOffset = weekDay - today.weekday;
				if (dayOffset < 0) dayOffset += 7;
				while (true) {
					let nextOccurrence = today.plus({
						days: dayOffset
					});
					dayOffset += 7;
					if (nextOccurrence <= endDate) {
						ans.push(nextOccurrence)
					} else {
						break
					}
				}
			});
			return ans
		}

		let handleLoopMonths = (p) => {
			if (!isNotNullOrEmptyArray(p.loopMonths)) {
				return []
			}
			let ans = [];
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
						[year, month] = nextMonth(year, month)
					} else if (nextOccurrence <= endDate) {
						ans.push(nextOccurrence);
						[year, month] = nextMonth(year, month)
					} else {
						break
					}
				}
			});
			return ans
		}

		let handleLoopMonths2 = (p) => {
			if (!isNotNullOrEmptyArray(p.loopMonths2)) {
				return []
			}
			let ans = [];
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
						nextOccurrence = firstDayOfTheMonth.plus({
							days: dayOffset
						}).plus({
							weeks: week - 1
						})
					} else {
						let [yearOfNextMonth, monthOfNextMonth] = nextMonth(year, month);
						let lastDayOfTheMonth = DateTime.fromObject({
							year: yearOfNextMonth,
							month: monthOfNextMonth,
							day: 1,
						}).minus({
							days: 1
						});
						let dayOffset = weekday - lastDayOfTheMonth.weekday;
						if (dayOffset > 0) dayOffset -= 7;
						nextOccurrence = lastDayOfTheMonth.plus({
							days: dayOffset
						}).plus({
							weeks: week + 1
						})
					}
					if (nextOccurrence < today || nextOccurrence.month !== month) {
						[year, month] = nextMonth(year, month)
					} else if (nextOccurrence <= endDate) {
						[year, month] = nextMonth(year, month);
						ans.push(nextOccurrence)
					} else {
						break
					}
				}
			});
			return ans
		}

		let handleLoopYears = (p) => {
			if (!isNotNullOrEmptyArray(p.loopYears)) {
				return []
			}
			let ans = [];
			p.loopYears.forEach(([month, day]) => {
				let year = today.year;
				while (true) {
					let nextOccurrence = DateTime.fromObject({
						year: year,
						month: month,
						day: day,
					});
					if (year > endDate.year) {
						break
					}
					if (!nextOccurrence.isValid || nextOccurrence < today) {
						year++
					} else if (nextOccurrence <= endDate) {
						ans.push(nextOccurrence);
						year++
					} else {
						break
					}
				}
			});
			return ans
		}

		let handleLoopYears2 = (p) => {
			if (!isNotNullOrEmptyArray(p.loopYears2)) {
				return []
			}
			let ans = [];
			p.loopYears2.forEach(([month, week, weekday]) => {
				let year = today.year;
				while (true) {
					let firstDayOfThisMonth = DateTime.fromObject({
						year: year,
						month: month,
						day: 1
					});
					let nextOccurrence;
					if (week > 0) {
						let dayOffset = (weekday - firstDayOfThisMonth.weekday + 7) % 7;
						nextOccurrence = firstDayOfThisMonth.plus({
							days: dayOffset
						}).plus({
							weeks: week - 1
						})
					} else {
						let lastDayOfMonth = firstDayOfThisMonth.plus({
							months: 1
						}).minus({
							days: 1
						});
						let dayOffset = (lastDayOfMonth.weekday - weekday + 7) % 7;
						nextOccurrence = lastDayOfMonth.minus({
							days: dayOffset
						}).minus({
							weeks: -week - 1
						})
					}
					if (year > endDate.year) {
						break
					}
					if (!nextOccurrence.isValid || nextOccurrence < today) {
						year++
					} else if (nextOccurrence <= endDate) {
						ans.push(nextOccurrence);
						year++
					} else {
						break
					}
				}
			});
			return ans
		}

		let handleSpecificDate = (p) => {
			if (!isNotNullOrEmptyArray(p.specificDate)) {
				return []
			}
			let isLunarFestival = p.specificDate.length > 50;
			var ans = [];
			p.specificDate.forEach((dateString) => {
				let date = DateTime.fromISO(dateString);
				if (!date.isValid) {
					throw new Error("Invalid specific date");
				}
				if (isLunarFestival && (date < today || date > endDate)) {
					return
				}
				ans.push(date)
			});
			return ans
		}

		let ans = [
			...handleLoopWeeks(p),
			...handleLoopMonths(p),
			...handleLoopMonths2(p),
			...handleLoopYears(p),
			...handleLoopYears2(p),
			...handleSpecificDate(p)
		];
		
		ans = ans
			.filter(date => p.startDate == null || date >= p.startDate)
			.sort((a, b) => a.ts - b.ts);
		
		return ans;
	}
	
	async showTasks(rootPath) {
		const { Files } = await cJS();
		if (!Files.isFolderNote(rootPath)) {
			console.log("请在Folder Note中使用该命令");
			return;
		}

		let {DateTime} = this.dv.luxon;
		let today = DateTime.local().startOf("day");

		let findTasks = (rootPath) => {
			let tasks = [];

			let pushTask = (p, date) => {
				tasks.push({
					key: p.file.path,
					title: p.file.link,
					priority: p.priority,
					date: date,
					startTime: p.startTime,
					endTime: p.endTime,
					note: p.note,
					priorityContributors: [], // 高优先级的子任务
					dateContributors: [], // 早截止日期的子任务
				})
			}

			let pushError = (p, msg) => {
				tasks.push({
					key: p.file.path,
					title: p.file.link,
					priority: p.priority,
					date: today,
					startTime: "",
					endTime: msg,
					note: p.note,
					priorityContributors: [],
					dateContributors: [],
				})
			}

			// 获取所有子页面
			let rootFolderPath = Files.getParentPath(rootPath);
			let pages = this.dv.pages(`"${rootFolderPath}"`)
						.where(p => !p.file.path.split('/').includes('archive'))
						.where(p => p.file.path !== rootPath);

			pages.forEach((p) => {
				try {
					var ans = this.daysOfTask(p);
					ans.forEach((date) => {
						pushTask(p, date)
					});
					let priorityFilter = (p.priority > 0);
					if (ans.length === 0 && p.priority != null && priorityFilter) {
						pushTask(p, null)
					}
				} catch (error) {
					pushError(p, error.message)
				}
			});
			return tasks;
		}

		// 一个任务的优先级将是其自身和其所有子孙任务优先级中的最大值。
		// 一个任务的截止日期将是其自身和其所有子孙任务截止日期中的最早值。
		// 在任务的备注中，会清晰地标示出提供重要子任务（高优先级或者早截止日期）的具体任务链接。
		let processTasks = (tasks, rootPath) => {
			// 筛选出所有 rootPath 的直接子页面/任务
			let directChildrenTasks = tasks.filter(t => {
				return Files.getParentFolderNote(t.key) === rootPath;
			});
	
			const processedTasks = [];
	
			// 为每一个直接子任务聚合其所有后代任务的属性
			// 这个时间复杂度有点高可以降低但先就这样吧
			directChildrenTasks.forEach(task => {
				// 只有foldernote含有子任务
				if (!Files.isFolderNote(task.key)) {
					processedTasks.push(task);
					return;
				}
				let taskFolderPath = Files.getParentPath(task.key);
				// 筛选出当前任务的子孙任务
				const descTasks = tasks.filter(descTask => {
					return descTask.key !== task.key && descTask.key.startsWith(taskFolderPath + '/');
				});
	
				// 进行聚合计算
				let taskPriority = task.priority || 0;
				let maxPriority = taskPriority;
				let taskDate = task.date || null;
				let minDate = taskDate;
				let taskStartTime = task.startTime || null;
				let minStartTime = taskStartTime;
				let taskEndTime = task.endTime || null;
				let minEndTime = taskEndTime;
	
				descTasks.forEach(descTask => {
					// 聚合最高优先级
					const currentPriority = descTask.priority || 0;
					if (currentPriority >= taskPriority) {
						task.priorityContributors.push(descTask);
						if (currentPriority > maxPriority) {
							maxPriority = currentPriority;
						}
					}
	
					// 聚合最早日期
					const currentDate = descTask.date;
					const currentStartTime = descTask.startTime || null;
					const currentEndTime = descTask.endTime || null;
					if (currentDate) {
						task.dateContributors.push(descTask);
						if (!minDate || currentDate < minDate || (currentDate.equals(minDate) && 
							taskStartTime && currentStartTime && currentStartTime < minStartTime)) {
							minDate = currentDate;
							minStartTime = currentStartTime;
							minEndTime = currentEndTime;
						}
					}
				});
	
				task.priority = maxPriority;
				task.date = minDate;
				task.startTime = minStartTime;
				task.endTime = minEndTime;

				processedTasks.push(task);
			});
	
			return processedTasks;
		}

		let sortTasks = (tasks) => {
			let paddingTime = (time) => {
				if (time == null) {
					return ""
				}
				if (time.length === 4) {
					return "0" + time
				}
				return time
			}

			tasks.sort((a, b) => {
				let urgentEndDate = today.plus({
					days: 6
				});
				let isUrgentA = a.date != null && a.date <= urgentEndDate;
				let isUrgentB = b.date != null && b.date <= urgentEndDate;
				if (isUrgentA && !isUrgentB) return -1;
				if (!isUrgentA && isUrgentB) return 1;
				if (isUrgentA && isUrgentB) {
					let dateDiff = a.date - b.date;
					if (dateDiff !== 0) return dateDiff;
					if (a.startTime != null && b.startTime != null) {
						let timeDiff = paddingTime(a.startTime).localeCompare(paddingTime(b.startTime));
						if (timeDiff !== 0) return timeDiff
					}
					let aEndTime = paddingTime(a.endTime || "23:59");
					let bEndTime = paddingTime(b.endTime || "23:59");
					return aEndTime.localeCompare(bEndTime)
				}
				let aPriority = a.priority || 0;
				let bPriority = b.priority || 0;
				return bPriority - aPriority
			});

			return tasks;
		}

		let printTasks = (t) => {
			let formatTime = (t) => {
				if (t.date === null) {
					return ""
				}
				let currentYear = today.year;
				let time = t.date.toFormat(currentYear === t.date.year ? "MM-dd" : "yy-MM-dd");
				if (t.startTime || t.endTime) {
					time += ' '
				}
				if (t.startTime) {
					time += t.startTime
				}
				if (t.endTime) {
					time += '->' + t.endTime
				}
				return `<code>${time}</code>  `
			}

			if (t.priority == null || typeof t.priority !== 'number' || t.priority < 0) {
				t.priority = 0
			}
			if (t.priority > 4) {
				t.priority = 4
			}
			let val = 230 - t.priority * 55;
			let blueVal = 230;
			let innerRadius = t.priority >= 2 ? 0 : 2;
			let note = "";
			if (t.note != null) {
				note = `  ${t.note}`;
			}

			// 将贡献者信息添加到备注中
			let extraNotes = [];
			for (let priorityContributor of t.priorityContributors) {
				extraNotes.push(`\`${priorityContributor.priority}:\` ${priorityContributor.title}`);
			}
			for (let dateContributor of t.dateContributors) {
				extraNotes.push(`\`${dateContributor.date.toFormat("MM-dd")}:\` ${dateContributor.title}`);
			}
			note = '  ' + extraNotes.join('  ');
			
			return `<svg width="16" height="16" style="vertical-align: middle;">` +
				   `<circle cx="8" cy="8" r="6.5" fill="rgb(${val}, ${val}, ${blueVal})" />` +
				   `<circle cx="8" cy="8" r="${innerRadius}" fill="white" />` +
				   `</svg>  ${formatTime(t)}${t.title}${note}`;
		}
		
		let tasks = findTasks(rootPath);

		tasks = processTasks(tasks, rootPath);

		tasks = sortTasks(tasks);

		if (tasks.length === 0) {
			return;
		}
		this.dv.table([""], tasks.map((e) => [printTasks(e)]));
	}

	async skip(p) {
		let days = this.daysOfTask(p);
		if (days.length == 0) {
			return;
		}
		let file = app.vault.getAbstractFileByPath(p.file.link.path);
		await app.fileManager.processFrontMatter(file, (frontmatter) => {
			frontmatter.startDate = days[0].plus({days: 1}).toFormat("yyyy-MM-dd");
		});
		// 刷新界面
		setTimeout(function() {
			app.commands.executeCommandById('dataview:dataview-force-refresh-views')
		}, 300);
	}
}