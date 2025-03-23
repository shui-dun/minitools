class Ai {
    async getDailyQuote(model="huihui_ai/qwen2.5-abliterate:1.5b") {
        const apiUrl = "http://localhost:11434/api/generate";
        const prompt = "生成一句格言，激励人心且富有哲理。";
        try {
            const response = await fetch(apiUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: model,
                    prompt: prompt,
                    max_tokens: 50,
                    stream: false
                })
            });
            
            if (!response.ok) throw new Error(`HTTP错误 ${response.status}`);
            
            const data = await response.json();
            // 如果两侧都是双引号，则去掉
            return data.response.replace(/^"(.*)"$/, '$1');
            
        } catch (error) {
            return `获取格言失败: ${error.message}`;
        }
    }
}