class Note {
	noteInfo() {
		let page = this.dv.page("note/note.md");
		let filterNotesByTags = (tags) => {
			// 定义被排除的标签前缀
			const excludedPrefixes = page.excludedTags.map(tag => `#${tag}`);
			// 检查是否有任何一个标签不是以被排除的前缀开头，如果有则返回true
			for (let tag of tags) {
				if (!excludedPrefixes.some(prefix => tag.startsWith(prefix))) {
					return true;
				}
			}
			// 如果所有标签都以被排除的前缀开头，则返回false
			return false;
		}
		
		// 所有笔记
		let allNotes = this.dv.pages('"note" and -"note/assets"');

		// 基础过滤得到的笔记
		let basicNotes = allNotes
		  .where(x => x.sr)
		  .where(x => filterNotesByTags(x.file.tags))
		  .where(x => x.ctime >= page.ctimeFilter);

		// 待复习的笔记
		let toBeReviewedNotes = basicNotes
		  .where(x => x.sr[2] <= this.dv.date('today'));

		// 今日复习的笔记
		let todayReviewedNotes = basicNotes
		  // .where(x => x.ctime - 0 != this.dv.date('today') || x.sr[2] - 0 != this.dv.date('tomorrow')) // 不是今天创建的笔记
		  .where(x => x.sr[2] == this.dv.duration(`${Math.ceil(x.sr[1])}day`) + this.dv.date('today'));

		// 待复习笔记的数目
		let waitReviewCount = toBeReviewedNotes
		  .values
		  .reduce((sum, x) => sum + 1, 0);

		// 今日复习的笔记的数目
		let todayReviewedCount = todayReviewedNotes
		  .values
		  .reduce((sum, x) => sum + 1, 0);

		// 今日复习的笔记的大小（KB）
		let todayReviewedSize = (todayReviewedNotes
		  .values
		  .reduce((sum, x) => sum + x.file.size, 0) / 1024).toFixed(0);

		return {
			allNotes,
			basicNotes,
			toBeReviewedNotes,
			todayReviewedNotes,
			waitReviewCount,
			todayReviewedCount,
			todayReviewedSize,
		}
	}
	
    async reviewEasy() {
        await this.updateReviewInFrontMatterOfCurrentFile((ease, interval, date) => {
            let newEase = ease * 1.2;
            let newInterval = interval * newEase * 1.3;
            return [newEase, newInterval, this.nextReviewDate(newInterval)];
        });
    }
	
    async reviewGood() {
        await this.updateReviewInFrontMatterOfCurrentFile((ease, interval, date) => {
            let newEase = ease;
            let newInterval = interval * newEase;
            return [newEase, newInterval, this.nextReviewDate(newInterval)];
        });
    }
	
    async reviewHard() {
        await this.updateReviewInFrontMatterOfCurrentFile((ease, interval, date) => {
            let newEase = ease * 0.85 < 1.3 ? 1.3 : ease * 0.85;
            let newInterval = interval * 0.5 < 1.0 ? 1.0 : interval * 0.5;
            return [newEase, newInterval, this.nextReviewDate(newInterval)];
        });
    }
	
    async reviewDelay() {
        await this.updateReviewInFrontMatterOfCurrentFile((ease, interval, date) => {
            return [ease, interval, this.nextReviewDate(7.0)];
        });
    }
	
	async nextNote() {
		let info = this.noteInfo();
		let notes = info.toBeReviewedNotes.sort(x => x.sr[2]);
		if (notes.length == 0) {
			new Notice("没有待复习的笔记");
			return;
		}
		let note = notes[0];
		await this.app.workspace.openLinkText(note.file.link.path, "", false);
	}
	
	async randomNote() {
		let info = this.noteInfo();
		let notes = info.toBeReviewedNotes;
		if (notes.length == 0) {
			new Notice("没有待复习的笔记");
			return;
		}
		let getRandomInt = (min, max) => {
			// 包含 min 和 max 的整数
			return Math.floor(Math.random() * (max - min + 1)) + min;
		}
		let ind = getRandomInt(0, notes.length - 1);
		let note = notes[ind];
		await this.app.workspace.openLinkText(note.file.link.path, "", false);
	}
	
    dateFormat(fmt, date) {
        let ret;
        const opt = {
            "Y+": date.getFullYear().toString(), // 年
            "m+": (date.getMonth() + 1).toString(), // 月
            "d+": date.getDate().toString(), // 日
            "H+": date.getHours().toString(), // 时
            "M+": date.getMinutes().toString(), // 分
            "S+": date.getSeconds().toString() // 秒
        };
        for (let k in opt) {
            ret = new RegExp("(" + k + ")").exec(fmt);
            if (ret) {
                fmt = fmt.replace(ret[1], (ret[1].length == 1) ? (opt[k]) : (opt[k].padStart(ret[1].length, "0")));
            }
            ;
        }
        ;
        return fmt;
    }
	
    async updateReviewInFrontMatterOfCurrentFile(foo) {
        let file = this.app.workspace.getActiveFile();
        if (!file) {
            console.error("obsidian-review: No active file to update review.");
            return;
        }
        await this.updateReviewInFrontMatter(file, foo);
    }
	
    // 更新frontmatter中的review属性
    async updateReviewInFrontMatter(file, foo) {
        // 获得frontmatter
        let frontmatter = this.app.metadataCache.getFileCache(file).frontmatter;
        // 读取文件内容
        let fileText = await this.app.vault.read(file);
        // 从frontmatter中读取复习的难易度和复习间隔
        let [originEase, originInterval, originDate] = frontmatter["sr"];
        originDate = new Date(originDate);
        // 更新复习的难易度和复习间隔，easy、good、hard、start over的策略各不相同
        let [destEase, destInterval, destDate] = foo(originEase, originInterval, originDate);
        // 只保留1位小数
        destEase = Number(destEase).toFixed(1);
        destInterval = Number(destInterval).toFixed(1);
        // 格式化时间
        destDate = this.dateFormat("YYYY-mm-dd", destDate);
        // 更新frontmatter
        fileText = fileText.replace(/(\-\-\-[\s\S]+?sr:\s+\[\s*)[\.\d]+\s*,\s*[\.\d]+\s*,\s*\d{4}\-\d{2}\-\d{2}\s*(\][\s\S]+?\-\-\-)/, `$1${destEase},${destInterval},${destDate}$2`);
        // 写入文件
        this.app.vault.modify(file, fileText);
        // 弹出通知
        new Notice(`ease: from ${originEase} to ${destEase}\ninterval: from ${originInterval} to ${destInterval}`);
    }
	
    // 得到新的下次复习日期
    nextReviewDate(interval) {
        // 修复有时候当天复习笔记却显示为下一天复习的笔记的bug：
        // 只保留1位小数，以与updateReviewInFrontMatter中的destEase = Number(destEase).toFixed(1);相一致
        // 例如，7.01在此时应该先被转化为7.0，否则Math.ceil(interval)会向上取整为8而非7
        interval = parseFloat(Number(interval).toFixed(1));
        let newDate = new Date();
        newDate.setDate(newDate.getDate() + Math.ceil(interval));
        return newDate;
    }
	
	// 该方法已废弃，没有被调用
    async jumpToReviewList() {
        let previousFilePath = this.app.workspace.getLastOpenFiles()[0];
        // 如果上一个文件名不包含“review.md” 或者 “note.md”，则返回
        if (!previousFilePath.includes("review.md") && !previousFilePath.includes("note.md")) {
            new Notice("Jump Disabled", 500);
            return;
        }
        // 等待一段时间使得索引更新，不然跳转回文件复习列表之后文件复习列表还是旧的
        await new Promise(resolve => setTimeout(resolve, 200));
        let previousFile = this.app.vault.getAbstractFileByPath(previousFilePath);
        if (!(previousFile instanceof TFile)) {
            console.error("obsidian-review: The last opened file is not found or not a TFile.");
            return;
        }
        // 获取当前活动的leaf（leaf是指标签页）
        let activeLeaf = this.app.workspace.activeLeaf;
        if (!activeLeaf) {
            console.error("obsidian-review: No active leaf to open the file in.");
            return;
        }
        await activeLeaf.openFile(previousFile);
    }
}
