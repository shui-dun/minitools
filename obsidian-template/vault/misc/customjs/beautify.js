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
	
	button(text, onclick) {
		let button = document.createElement('button');
		button.textContent = text;
		button.onclick = onclick;
		return button;
	}
	
	container(...elements) {
		let container = document.createElement('div');

		// 设置容器的样式
		container.style.display = 'flex';
		container.style.flexWrap = 'wrap'; // 支持换行
		container.style.gap = '10px'; // 元素间的间距
		container.style.justifyContent = 'flex-start'; // 从左到右排列
		container.style.alignItems = 'center'; // 垂直方向居中
		container.style.width = '100%'; // 设置容器宽度

		// 将传入的元素添加到容器中
		elements.forEach(element => {
			container.appendChild(element);
		});

		return container;
	}
}