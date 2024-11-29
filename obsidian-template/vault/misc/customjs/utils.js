class Utils {
	num(num, digit) {
		return `<code>${this.num2(num, digit)}</code>`;
	}

	// 不带代码块的格式化
	num2(num, digit) {
		if (digit === undefined) {
			digit = 1;
		}
		
		// 先按指定位数处理
		let result = parseFloat(num.toFixed(digit));
		
		// 如果结果为0但原始数不为0，则逐步增加精度直到找到非0值
		if (result === 0 && num !== 0) {
			let d = digit;
			while (result === 0 && d < 10) { // 设置最大精度为10位
				d++;
				result = parseFloat(num.toFixed(d));
			}
		}
		
		let resultStr = result.toString();
		
		// 如果是0.xx格式，转换为.xx
		if (result > 0 && result < 1) {
			resultStr = '.' + resultStr.split('.')[1];
		}
		
		return resultStr;
	}

	progress(val, width) {
		if (width === undefined) {
			width = 100;
		}
		return `<progress value=${val} max=1 style="width:${width}px;"></progress>`
	}

	button(text, onclick, refresh) {
		let button = document.createElement('button');
		button.textContent = text;
		button.onclick = async () => {
			if (onclick) {
				await onclick();
			}
			if (refresh) {
				await this.refresh();
			}
		}
		return button;
	}

	incButton(text, page, attribute, minVal, maxVal, offset, refresh, onchange) {
		let button = document.createElement('button');
		button.textContent = text;
		button.onclick = async () => {
			let val = page[attribute] || 0;
			val = val + offset;
			if (maxVal != null && val > maxVal) {
				val = maxVal;
			}
			if (minVal != null && val < minVal) {
				val = minVal;
			}
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = val;
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		}
		return button;
	}

	select(page, attribute, query, refresh, onchange) {
		let button = this.button(this.extractWikiLink(page[attribute]), async () => {
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
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = val;
				button.textContent = this.extractWikiLink(val);
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		});
		return button;
	}

	multiselect(page, attribute, query, refresh, onchange) {
		let button = this.button(this.compactArray(page[attribute]), async () => {
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
			}, { values: { select: page[attribute]?.map(x => x.toString()) || []} });
			if (ans.status != 'ok') {
				return;
			}
			let val = ans.select.value;
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = val;
				button.textContent = this.compactArray(val);
				page[attribute] = val;
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		});
		return button;
	}

	date(page, attribute, refresh, onchange) {
		let input = document.createElement('input');
		input.type = 'date';
		if (page[attribute]?.toFormat) {
			input.value = page[attribute].toFormat('yyyy-MM-dd');
		}
		input.onchange = async () => {
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.value;
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		};
		return input;
	}

	time(page, attribute, refresh, onchange) {
		let input = document.createElement('input');
		input.type = 'time';
		input.value = page[attribute];
		input.onchange = async () => {
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.value;
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		};
		return input;
	}

	datetime(page, attribute, refresh, onchange) {
		let input = document.createElement('input');
		input.type = 'datetime-local';
		if (page[attribute]?.toFormat) {
			input.value = page[attribute].toFormat('yyyy-MM-dd\'T\'HH:mm');
		}
		input.onchange = async () => {
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.value;
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		};
		return input;
	}

	input(page, attribute, refresh, onchange) {
		let input = document.createElement('input');
		input.type = 'text';
		input.value = page[attribute] || '';
		input.onchange = async () => {
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.value;
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		};
		return input;
	}

	textArea(page, attribute, refresh, onchange) {
		let textArea = document.createElement('textarea');
		textArea.value = page[attribute] || '';
		
		// 基本样式设置
		textArea.style.width = '100%';
		textArea.style.minWidth = '150px';
		textArea.style.resize = 'none';
		textArea.style.lineHeight = '1.5';
		textArea.style.overflow = 'hidden'; // 隐藏滚动条

		// 自适应高度函数
		const autoResize = () => {
			textArea.style.height = 'auto';  // 重置高度
			const height = textArea.scrollHeight;
			textArea.style.height = height + 'px';
		};
		
		// 绑定事件
		textArea.addEventListener('input', autoResize);
		
		// 使用MutationObserver监听元素被添加到DOM
		const observer = new MutationObserver((mutations, obs) => {
			if (textArea.isConnected) {
				autoResize();
				obs.disconnect(); // 只需要执行一次
			}
		});
		
		observer.observe(document.body, {
			childList: true,
			subtree: true
		});
		
		textArea.onchange = async () => {
			await app.fileManager.processFrontMatter(
				app.vault.getAbstractFileByPath(page.file.path), 
				(frontmatter) => {
					frontmatter[attribute] = textArea.value;
				}
			);
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		};
		
		return textArea;
	}

	checkbox(page, attribute, refresh, onchange) {
		let input = document.createElement('input');
		input.type = 'checkbox';
		input.checked = page[attribute] || false;
		input.onchange = async () => {
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = input.checked;
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		};
		return input;
	}

	numInput(page, attribute, refresh, onchange) {
		let input = document.createElement('input');
		input.type = 'number';
		input.value = page[attribute] || '';
		input.onchange = async () => {
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = this.convertToNumber(input.value);
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
			}
		};
		return input;
	}

	slider(page, attribute, min, max, step, refresh, onchange) {
		let input = document.createElement('input');
		input.type = 'range';
		input.min = min;
		input.max = max;
		input.step = step;
		input.value = page[attribute] || '';
		input.onchange = async () => {
			await app.fileManager.processFrontMatter(app.vault.getAbstractFileByPath(page.file.path), (frontmatter) => {
				frontmatter[attribute] = this.convertToNumber(input.value);
			});
			if (onchange) {
				onchange();
			}
			if (refresh) {
				await this.refresh();
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
			// 如果是字符串，则创建一个 p 元素
			if (typeof element === 'string') {
				const span = document.createElement('span');
				span.innerHTML = element;
				element = span;
			}
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

	async refresh() {
		setTimeout(function() {
			app.commands.executeCommandById('dataview:dataview-force-refresh-views')
		}, 300);
	}

	compactArray(array) {
		if (!array) {
			return '';
		}
		return array.map(item => {
			item = item.toString();
			item = this.extractWikiLink(item);
			return item;
		})
		.join(', ');
	}

	// 将 [[some/path/水果.md|水果]] 或 [[some/path/水果.md]] 或 [[水果.md]] 或 [[水果]] 转化为水果
	extractWikiLink(text) {
		if (text == null) {
			return '';
		}
		text = text.toString();
		// Match wiki link pattern with or without alias
		const wikiLinkRegex = /\[\[(.*?)\]\]/;
		const match = text.match(wikiLinkRegex);
		
		if (!match) return text;
		
		// Get the content inside [[]]
		const inner = match[1];
		
		// Split by | to handle alias
		const parts = inner.split('|');
		
		if (parts.length > 1) {
		  // Return alias if exists
		  return parts[1];
		}
		
		// Handle path
		const pathParts = parts[0].split('/');
		const fileName = pathParts[pathParts.length - 1];
		
		// Remove .md extension if exists
		return fileName.replace(/\.md$/, '');
	  }
}