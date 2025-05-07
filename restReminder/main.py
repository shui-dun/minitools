from pydub import AudioSegment
import os
import time
from sha256 import sha256
from openai_tts import tts

audio = AudioSegment.empty()
# 前8s
prelude = AudioSegment.from_mp3("prelude.mp3")[:8000]
alarm = AudioSegment.from_mp3("prelude.mp3")
cacheRoot = "cache/"

def addText(text):
    global audio
    # 如果不存在cache目录，则生成
    if not os.path.exists(cacheRoot):
        os.mkdir(cacheRoot)
    # 计算文本的sha256值
    textHash = sha256(text)
    # 缓存文件
    cacheFile = os.path.join(cacheRoot, textHash + ".mp3")
    # 如果不存在，则调用tts生成
    if not os.path.exists(cacheFile):
        tts(text, cacheFile)
        time.sleep(15)
    else:
        print("cache hit: " + text)
    # 读取缓存文件
    add = AudioSegment.from_mp3(cacheFile)
    audio = audio + prelude
    audio = audio + add

def addSilent(delay):
    global audio
    """
    :param delay: 延迟，单位秒
    """
    silent = AudioSegment.silent(duration=int(delay * 1000))
    audio = audio + silent

def addAlarm():
    global audio
    for _ in range(2):
        audio = audio + alarm

addSilent(30 * 60)
addText("距离休息还有30分钟")
addSilent(15 * 60)
addText("距离休息还有15分钟")
addSilent(10 * 60)
addText("距离休息还有5分钟")
addSilent(5 * 60)
addAlarm()
# 压缩，算了这压缩效果不好，还是用现成的压缩工具
# audio = audio.set_frame_rate(22050).set_channels(1).set_sample_width(1)
audio.export("restReminder.mp3", format="mp3")