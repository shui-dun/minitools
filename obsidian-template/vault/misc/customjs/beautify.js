class Beautify {
	num(num, digit) {
		if (digit === undefined) {
			digit = 1;
		}
		return `\`${parseFloat(num.toFixed(digit))}\``;
	}
	
	// 不带代码块的格式化
	num2(num, digit) {
		if (digit === undefined) {
			digit = 1;
		}
		return parseFloat(num.toFixed(digit));
	}
	
	progress(val, width) {
		if (width === undefined) {
			width = 100;
		}
		return `<progress value=${val} max=1 style="width:${width}px;"></progress>`
	}
}