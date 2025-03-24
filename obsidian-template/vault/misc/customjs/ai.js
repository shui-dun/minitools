class Ai {
    lastDailyQuote = null;
    lastDailyQuoteTime = 0;

    async getDailyQuote() {
        const {Secret} = await cJS();
        const apiKey = Secret.DEEPSEEK_API_KEY;
        const apiUrl = "https://api.lkeap.cloud.tencent.com/v1/chat/completions";
        let fileText = await app.vault.read(app.vault.getAbstractFileByPath("领域/心理健康.md"));
        // 找出所有以- 开头的行
        const lines = fileText.split('\n').filter(line => line.trim().startsWith('- '));
        // 随机选择一行
        fileText = lines[Math.floor(Math.random() * lines.length)];
        const prompt = "根据以下内容生成一句30字左右的格言：\n" + fileText;

        // 缓存机制
        if (this.lastDailyQuote && (Date.now() - this.lastDailyQuoteTime < 1000 * 60 * 5)) {
            return this.lastDailyQuote;
        }

        try {
            // obsidian提供的requestUrl类似fetch，但是绕过了CORS限制
            const { requestUrl } = require('obsidian');
            const response = await requestUrl({
                url: apiUrl,
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer " + apiKey
                },
                body: JSON.stringify({
                    model: "deepseek-v3",
                    messages: [{ role: "user", content: prompt }],
                    stream: false
                })
            });
            let data = JSON.parse(response.text)["choices"][0]["message"]["content"];
            // 去掉换行符
            data = data.replace(/[\r\n]/g, '');
            // 去掉双引号
            data = data.replace(/^"(.*)"$/, '$1');
            // 去掉中文引号
            data = data.replace(/^“(.*)”$/, '$1');
            // 去掉粗体
            data = data.replace(/\*\*/g, '');

            this.lastDailyQuote = data;
            this.lastDailyQuoteTime = Date.now();

            return data;
        } catch (error) {
            return "网络问题，无法获取格言";
        }
    }
}