<%*
// 生成日期
async function generateDate() {
    const dayOfWeek = moment().day();
	const dateFormat = "YYYY-MM-DD";

	const NO_DATE = "NO_DATE";
	const MANUAL = "MANUAL";
	
	const suggestions = new Map();
	suggestions.set("不输入日期", NO_DATE);
	suggestions.set("today", moment());
	suggestions.set("tomorrow", moment().add(1, 'days'));
	suggestions.set("manual", MANUAL);
	suggestions.set("next monday", moment().add(1, 'weeks').day(1));
	suggestions.set(dayOfWeek >= 2 ? "next tuesday" : "tuesday",
	                dayOfWeek >= 2 ? moment().add(1, 'weeks').day(2) : moment().day(2)
	);
	suggestions.set(dayOfWeek >= 3 ? "next wednesday" : "wednesday",
	                dayOfWeek >= 3 ? moment().add(1, 'weeks').day(3) : moment().day(3)
	);
	suggestions.set(dayOfWeek >= 4 ? "next thursday" : "thursday",
	                dayOfWeek >= 4 ? moment().add(1, 'weeks').day(4) : moment().day(4)
	);
	suggestions.set(dayOfWeek >= 5 ? "next friday" : "friday",
	                dayOfWeek >= 5 ? moment().add(1, 'weeks').day(5) : moment().day(5)
	);
	suggestions.set(dayOfWeek >= 6 ? "next saturday" : "saturday",
	                dayOfWeek >= 6 ? moment().add(1, 'weeks').day(6) : moment().day(6)
	);
	suggestions.set(dayOfWeek == 0 ? "next sunday" : "sunday",
	                dayOfWeek >= 0 ? moment().add(1, 'weeks').day(0) : moment().day(0)
	);
	
	const selection = await tp.system.suggester(
	    [...suggestions].map(([k, v]) => (v !== NO_DATE && v !== MANUAL) ? k + " (" + v.format(dateFormat) + ")" : k),
	    Array.from(suggestions.values())
	);

	if (selection === NO_DATE) {
		return false;
	}
	
	let resultDate = null;
	if (selection == MANUAL) {
	    inputDate = await tp.system.prompt("Type a date (DD MM? YY?):");
	    resultDate = moment(inputDate, "DD MM YY");
	    if (!resultDate.isValid()) {
			throw new Error("无效的日期");
	    }
	} else if (selection == null) {
		throw new Error("无效的日期");
	} else {
	    resultDate = selection;
	}
	return resultDate.format(dateFormat);
}

// 生成时间
async function generateTime() {
    const hourFormat = "HH:mm";

	// 获取当前时间
	const now = moment();
	const currentHour = now.hour();
	const currentMinute = now.minute();
	
	// 创建小时选择建议，从当前小时开始
	let hourSuggestions = [{
		"label": "不选择时间",
		"value": false,
	}];
	hourSuggestions = hourSuggestions.concat(Array.from({ length: 24 }, (_, i) => {
	    const hour = (currentHour + i) % 24; // 从当前小时开始
	    return {
	        label: `${hour.toString().padStart(2, '0')}点`,
	        value: hour,
	    };
	}));
	
	// 提供选择小时的提示
	const selectedHour = await tp.system.suggester(
	    hourSuggestions.map(h => h.label),
	    hourSuggestions.map(h => h.value)
	);

	if (selectedHour === false) {
		return false;
	}

	if (selectedHour == null) {
		throw new Error("无效的小时数");
	}
	
	// 创建分钟选择建议，从当前分钟开始
	let selectedTime;
	const minuteSuggestions = Array.from({ length: 60 }, (_, i) => {
		const minute = (currentMinute + i) % 60; // 从当前分钟开始
		return {
			label: `${minute.toString().padStart(2, '0')}分`,
			value: minute,
		};
	});

	const selectedMinute = await tp.system.suggester(
		minuteSuggestions.map(m => m.label),
		minuteSuggestions.map(m => m.value)
	);

	if (selectedMinute == null) {
		throw new Error("无效的分钟数");
	}

	selectedTime = moment().hour(selectedHour).minute(selectedMinute);
	return selectedTime.format(hourFormat);
}

let ans = '';

const date = await generateDate();
const time = await generateTime();
if (date === false && time === false) {
	return;
} else if (date === false) {
	ans = time;
} else if (time === false) {
	ans = date;
} else {
	ans = `${date}T${time}`;
}
tp.file.cursor_append(ans);
app.workspace.activeLeaf.view.editor.focus();
%>