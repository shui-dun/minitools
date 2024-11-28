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
	
	renderTasks(pages, allowZeroPriority) {
		let {DateTime} = this.dv.luxon;
		let today = DateTime.local().startOf("day");
		
		let events = [];

		let pushEvent = (p, date) => {
			events.push({
				title: p.file.link,
				priority: p.priority,
				date: date,
				startTime: p.startTime,
				endTime: p.endTime,
				note: p.note,
			})
		}

		let pushError = (p, msg) => {
			events.push({
				title: p.file.link,
				priority: p.priority,
				date: today,
				startTime: "",
				endTime: msg,
				note: p.note,
			})
		}
		
		let formatTime = (e) => {
			if (e.date === null) {
				return ""
			}
			let currentYear = today.year;
			let time = e.date.toFormat(currentYear === e.date.year ? "MM-dd" : "yy-MM-dd");
			if (e.startTime || e.endTime) {
				time += ' '
			}
			if (e.startTime) {
				time += e.startTime
			}
			if (e.endTime) {
				time += '->' + e.endTime
			}
			return `<code>${time}</code>  `
		}

		let highlightTitle = (e) => {
			if (e.priority == null || typeof e.priority !== 'number' || e.priority < 0) {
				e.priority = 0
			}
			if (e.priority > 4) {
				e.priority = 4
			}
			let val = 230 - e.priority * 55;
			let blueVal = 230;
			let innerRadius = e.priority >= 2 ? 0 : 2;
			let note = "";
			if (e.note != null) {
				note = `  ${e.note}`;
			}
			
			return `<svg width="16" height="16" style="vertical-align: middle;">` +
				   `<circle cx="8" cy="8" r="6.5" fill="rgb(${val}, ${val}, ${blueVal})" />` +
				   `<circle cx="8" cy="8" r="${innerRadius}" fill="white" />` +
				   `</svg>  ${formatTime(e)}${e.title}${note}`;
		}
		
		let paddingTime = (time) => {
			if (time == null) {
				return ""
			}
			if (time.length === 4) {
				return "0" + time
			}
			return time
		}

		pages.forEach((p) => {
			try {
				var ans = this.daysOfTask(p);
				ans.forEach((date) => {
					pushEvent(p, date)
				});
				let priorityFilter = allowZeroPriority ? true : (p.priority > 0);
				if (ans.length === 0 && p.priority != null && priorityFilter) {
					pushEvent(p, null)
				}
			} catch (error) {
				pushError(p, error.message)
			}
		});

		events.sort((a, b) => {
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

		this.dv.table([""], events.map((e) => [highlightTitle(e)]));
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
	
	// 生成Mermaid图表代码
	generateMermaidCode(curTask) {
		this.curTask = curTask;
		// 重新计算缓存
		this.rebuildCache();
		const rootTask = this.getRootTask(curTask);

		// 如果任务没有子任务和依赖任务，直接返回空字符串
		if (!this.hasAnyRelation(rootTask)) {
			return '';
		}

		let code = this.dfsGenerateMermaidCode(rootTask) + '\n' + [...this.drawnLinesCache].join("\n") + '\n';

		// 高亮curTask
		code += `style ${this.sanitizeId(curTask.file.path)} fill:#fab27b\n`;

		return '```mermaid\nflowchart\n' + code + '```';
	}

	// 重新计算缓存
	rebuildCache() {
		let path = '"计划"';
		// 缓存所有任务的子任务
		this.subTasksCache = new Map();
		this.dv.pages(path).forEach(p => {
			this.subTasksCache.set(p.file.path, []);
		});
		this.dv.pages(path).forEach(p => {
			const superTask = p.superTask;
			if (superTask && this.dv.page(superTask)) {
				this.subTasksCache.get(superTask.path)?.push(p);
			}
		});
		// 缓存所有任务的依赖关系
		this.dependentOnCache = new Map();
		this.dv.pages(path).forEach(p => {
			this.dependentOnCache.set(p.file.path, []);
		});
		this.dv.pages(path).forEach(p => {
			const beforeTasks = p.beforeTasks;
			if (beforeTasks) {
				beforeTasks.forEach(t => {
					if (!this.dv.page(t)) return;
					this.dependentOnCache.get(t.path)?.push(p);
				});
			}
		});
		// 缓存所有依赖的绘制线
		this.drawnLinesCache = new Set();
	}

    // 生成Mermaid图表代码
    dfsGenerateMermaidCode(startTask) {
        let code = [];
        let subTasks = this.getSubTasks(startTask);
        
        if (subTasks.length > 0) {
            code.push(`subgraph ${this.sanitizeId(startTask.file.path)}[${this.formatTitle(startTask)}]`);
            
            // 将子任务分为有依赖关系和无依赖关系两组
            const [tasksWithRelation, tasksWithoutRelation] = this.separateTasksByRelation(subTasks);
            
            // 处理无关系的任务（使用紧凑模式）
            if (tasksWithoutRelation.length > 0) {
                code.push(this.generateCompactNode(tasksWithoutRelation));
            }
            
            // 处理有关系的任务（常规模式）
            tasksWithRelation.forEach(task => {
                code.push(this.dfsGenerateMermaidCode(task));
            });
            
            code.push('end');
        } else {
            code.push(this.generateNodeCode(startTask));
        }
        
        // 添加依赖关系
        this.getDependencies(startTask).forEach(dep => {
			let str = `${this.generateNodeCode(dep)} --> ${this.generateNodeCode(startTask)}`;
			this.drawnLinesCache.add(str);
        });

        this.getDependentOnTasks(startTask).forEach(dep => {
			let str = `${this.generateNodeCode(startTask)} --> ${this.generateNodeCode(dep)}`;
			this.drawnLinesCache.add(str);
        });
        
        return code.join('\n');
    }
    
    // 获取任务的根任务
    getRootTask(task) {
        if (!task.superTask) return task;
        return this.dv.page(task.superTask) || task;
    }

    // 获取任务的所有子任务
    getSubTasks(task) {
        return this.subTasksCache.get(task.file.path);
    }

    // 获取依赖当前任务的任务
    getDependentOnTasks(task) {
        return this.dependentOnCache.get(task.file.path);
    }

    // 获取当前任务依赖的任务
    getDependencies(task) {
        return task?.beforeTasks ? task.beforeTasks.map(t => this.dv.page(t)).filter(t => t) : [];
    }
	
	// 将任务分为有依赖关系或子任务和无依赖关系两组
    separateTasksByRelation(tasks) {
		// 含有依赖关系 或 子任务 的任务
        const tasksWithRelation = [];
        const tasksWithoutRelation = [];
        
        tasks.forEach(task => {
            if (this.hasAnyRelation(task)) {
                tasksWithRelation.push(task);
            } else {
                tasksWithoutRelation.push(task);
            }
        });
        
        return [tasksWithRelation, tasksWithoutRelation];
    }
	
	// 检查任务是否有任何依赖关系（包括被依赖和依赖其他）或者子任务
    hasAnyRelation(task) {
        return this.getDependentOnTasks(task).length > 0 || this.getDependencies(task).length > 0 || this.getSubTasks(task).length > 0;
    }

    // 生成紧凑模式的节点
    generateCompactNode(tasks) {
        const links = tasks.map(task => 
            `<a class="internal-link" href="${task.file.path}">${task.file.name}</a>`
        ).join('<br><br>');
		// 如果节点中包含 curTask，则将ID设置为 curTask 的 ID
		let ind = 0;
		for (let i = 0; i < tasks.length; i++) {
			if (tasks[i].file.path === this.curTask.file.path) {
				ind = i;
				break;
			}
		}
        return `${this.sanitizeId(tasks[ind].file.path)}(${links}<br><br><br>)`;
    }

    // 生成单个节点的代码
    generateNodeCode(task) {
        return `${this.sanitizeId(task.file.path)}(${this.formatTitle(task)})`;
    }

    // 格式化标题，包含链接和日期
    formatTitle(task) {
        let title = `<a class="internal-link" href="${task.file.path}">${task.file.name}</a>`;
		let days = this.daysOfTask(task);
		let date = '';
        if (days.length > 0) {
            date += ` ${days[0].toFormat("yy-MM-dd")}`;
        }
		if (task.startTime || task.endTime) {
			date += ' '
		}
		if (task.startTime) {
			date += task.startTime
		}
		if (task.endTime) {
			date += '->' + task.endTime
		}
		if (date) {
			title += ` <code>${date}</code>&emsp;`;
		}
        return title;
    }

    // 清理ID中的特殊字符
    sanitizeId(str) {
		let hash = 0;
		for (let i = 0; i < str.length; i++) {
			const char = str.charCodeAt(i);
			hash = (hash << 5) - hash + char; // hash * 31 + char
			hash |= 0; // Convert to 32bit integer
		}
		return hash;
    }
}