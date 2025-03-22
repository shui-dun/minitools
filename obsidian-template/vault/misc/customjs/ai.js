class Ai {
    async getDailyQuote(model="goekdenizguelmez/josiefied-qwen2.5-7b-abliterated-v2") {
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
            return data.response;
            
        } catch (error) {
            return `获取格言失败: ${error.message}`;
        }
    }
}