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

	select(page, attribute, query, onchange) {
		let button = this.button(page[attribute], async () => {
			const modalForm = app.plugins.plugins.modalforms.api;
			let ans = await modalForm.openForm({
				"fields": [
					{
						"name": "select",
						"label": "",
						"description": `for '${attribute}' of ${page.file.name}`,
						"input": {
							"type": "dataview",
							"allowUnknownValues": true,
							"query": query,
						},
					},
				],
			});
			if (ans.status != 'ok') {
				return;
			}
			let val = this.convertToNumber(ans.select.value);
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = val;
				button.textContent = val;
			});
			if (onchange) {
				onchange();
			}
		});
		return button;
	}

	multiselect(page, attribute, query, onchange) {
		let button = this.button(page[attribute]?.join(', '), async () => {
			const modalForm = app.plugins.plugins.modalforms.api;
			let ans = await modalForm.openForm({
				"fields": [
					{
						"name": "select",
						"label": "",
						"description": `for '${attribute}' of ${page.file.name}`,
						"input": {
							"type": "multiselect",
							"allowUnknownValues": true,
							"query": query,
							"source": "dataview",
						},
					},
				],
			}, { values: { select: page[attribute].map(x => x.toString())} });
			if (ans.status != 'ok') {
				return;
			}
			let val = ans.select.value;
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = val;
				button.textContent = val?.join(', ');
				page[attribute] = val;
			});
			if (onchange) {
				onchange();
			}
		});
		return button;
	}

	date(page, attribute, onchange) {
		let input = document.createElement('input');
		input.type = 'date';
		input.value = page[attribute]?.toFormat('yyyy-MM-dd');
		input.onchange = async () => {
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.value;
			});
			if (onchange) {
				onchange();
			}
		};
		return input;
	}

	time(page, attribute, onchange) {
		let input = document.createElement('input');
		input.type = 'time';
		input.value = page[attribute];
		input.onchange = async () => {
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.value;
			});
			if (onchange) {
				onchange();
			}
		};
		return input;
	}

	datetime(page, attribute, onchange) {
		let input = document.createElement('input');
		input.type = 'datetime-local';
		input.value = page[attribute]?.toFormat('yyyy-MM-dd\'T\'HH:mm');
		input.onchange = async () => {
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.value;
			});
			if (onchange) {
				onchange();
			}
		};
		return input;
	}

	input(page, attribute, onchange) {
		let input = document.createElement('input');
		input.type = 'text';
		input.value = page[attribute] || '';
		input.onchange = async () => {
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.value;
			});
			if (onchange) {
				onchange();
			}
		};
		return input;
	}

	checkbox(page, attribute, onchange) {
		let input = document.createElement('input');
		input.type = 'checkbox';
		input.checked = page[attribute] || false;
		input.onchange = async () => {
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.checked;
			});
			if (onchange) {
				onchange();
			}
		};
		return input;
	}

	numInput(page, attribute, onchange) {
		let input = document.createElement('input');
		input.type = 'number';
		input.value = page[attribute] || '';
		input.onchange = async () => {
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = this.convertToNumber(input.value);
			});
			if (onchange) {
				onchange();
			}
		};
		return input;
	}

	slider(page, attribute, min, max, step, onchange) {
		let input = document.createElement('input');
		input.type = 'range';
		input.min = min;
		input.max = max;
		input.step = step;
		input.value = page[attribute] || '';
		input.onchange = async () => {
			await this.app.fileManager.processFrontMatter(this.app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = this.convertToNumber(input.value);
			});
			if (onchange) {
				onchange();
			}
		}
		return input;
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

	wrapInCallout(inputText, title) {
		const lines = inputText.split('\n');
		const wrappedLines = lines.map(line => `> ${line}`);
		wrappedLines.unshift('> [!note]- ' + title);
		return wrappedLines.join('\n');
	}

	// 大于指定行数，包裹在 callout 中
	wrapInCalloutIfLarge(inputText, lineCount, title) {
		const lines = inputText.split('\n');
		if (lines.length > lineCount) {
			return this.wrapInCallout(inputText, title);
		}
		return inputText;
	}

	// 如果该字符串可以转换为数字，则转换为数字，否则返回原字符串
	convertToNumber(input) {
		const num = Number(input);
		return isNaN(num) ? input : num;
	}
}