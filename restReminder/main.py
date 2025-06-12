from pydub import AudioSegment
import os
import time
from sha256 import sha256
from openai_tts import tts

class AudioGenerator:
    def __init__(self):
        self.prelude = AudioSegment.from_mp3("prelude.mp3")[:8000] # 前8s
        self.miniBreak = AudioSegment.from_mp3("prelude.mp3")[:40000]
        self.longBreak = AudioSegment.from_mp3("prelude.mp3")
        self.audio = AudioSegment.empty()
        self.cacheRoot = "cache/"
        # 如果不存在cache目录，则生成
        if not os.path.exists(self.cacheRoot):
            os.mkdir(self.cacheRoot)

    def addText(self, text):
        # 计算文本的sha256值
        textHash = sha256(text)
        # 缓存文件
        cacheFile = os.path.join(self.cacheRoot, textHash + ".mp3")
        # 如果不存在，则调用tts生成
        if not os.path.exists(cacheFile):
            tts(text, cacheFile)
            time.sleep(15)
        else:
            print("cache hit: " + text)
        # 读取缓存文件
        add = AudioSegment.from_mp3(cacheFile)
        self.audio = self.audio + self.prelude
        self.audio = self.audio + add
        return self

    def addSilent(self, delay):
        """
        :param delay: 延迟，单位秒
        """
        silent = AudioSegment.silent(duration=int(delay * 1000))
        self.audio = self.audio + silent
        return self
    
    def addMiniBreak(self):
        self.audio = self.audio + self.miniBreak
        return self

    def addLongBreak(self):
        for _ in range(2):
            self.audio = self.audio + self.longBreak
        return self
        
    def export(self, outputPath, format="mp3"):
        # 压缩，算了这压缩效果不好，还是用现成的压缩工具
        # self.audio = self.audio.set_frame_rate(22050).set_channels(1).set_sample_width(1)
        self.audio.export(outputPath, format=format)

AudioGenerator()\
    .addText("开始计时")\
    .addSilent(30 * 60)\
    .addText("距离休息还有30分钟")\
    .addSilent(15 * 60)\
    .addText("距离休息还有15分钟")\
    .addSilent(10 * 60)\
    .addText("距离休息还有5分钟")\
    .addSilent(5 * 60)\
    .addLongBreak()\
    .export("gameAlarm.mp3")

AudioGenerator()\
    .addText("开始计时")\
    .addSilent(20 * 60)\
    .addText("距离休息还有40分钟")\
    .addMiniBreak()\
    .addSilent(20 * 60)\
    .addText("距离休息还有20分钟")\
    .addMiniBreak()\
    .addSilent(20 * 60)\
    .addText("开始休息")\
    .addLongBreak()\
    .export("bookAlarm.mp3")
