import requests
import json
import os
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(5), wait=wait_fixed(15))
# 最多重试5次，每次等待15秒
def tts(input, outputPath):
    print("tts: " + input)
    headers = {
        'Authorization': f'Bearer {os.environ["OPENAI_API_KEY"]}',
        'Content-Type':'application/json'
    }
    url = f"{os.environ['OPENAI_BASE_URL']}/v1/audio/speech"
    query = {
        "model": "tts-1",
        # "model": "tts-1-hd", # 这个模型的效果更好，但是速度更慢
        "voice": "nova",
        "input": input,
        "speed": 0.9,
        "response_format": "mp3",
    }
    response = requests.post(url=url, data=json.dumps(query), headers=headers)
    if response.status_code != 200:
        raise Exception(f"API调用失败: {response.status_code} - {response.text}")
    # 保存文件
    with open(outputPath, "wb") as f:
        f.write(response.content)