from pydub import AudioSegment
import os
import time
from sha256 import sha256
from openai_tts import tts

class AudioGenerator:
    def __init__(self):
        self.prelude = AudioSegment.from_mp3("prelude.mp3")[:8000].fade_out(1000) # 前8s，最后1s淡出
        self.miniBreak = AudioSegment.from_mp3("prelude.mp3")[:50000].fade_out(1000) - 10
        self.longBreak = AudioSegment.from_mp3("alarm.mp3").fade_in(15000) - 1 # 前15s淡入；整体分贝减1
        self.audio = AudioSegment.empty()
        self.cacheRoot = "cache/"
        # 如果不存在cache目录，则生成
        if not os.path.exists(self.cacheRoot):
            os.mkdir(self.cacheRoot)

    def addText(self, text):
        if text == "":
            self.audio = self.audio + self.prelude
            return self
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
        for _ in range(3):
            self.audio = self.audio + self.longBreak
        return self
        
    def export(self, outputPath, format="mp3"):
        # 压缩，算了这压缩效果不好，还是用现成的压缩工具
        # self.audio = self.audio.set_frame_rate(22050).set_channels(1).set_sample_width(1)
        self.audio.export(outputPath, format=format)

AudioGenerator()\
    .addText("")\
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
    .addText("")\
    .addSilent(20 * 60)\
    .addText("即将开始小憩")\
    .addSilent(20)\
    .addMiniBreak()\
    .addSilent(20 * 60)\
    .addText("即将开始小憩")\
    .addSilent(20)\
    .addMiniBreak()\
    .addSilent(20 * 60)\
    .addText("即将开始休息")\
    .addSilent(20)\
    .addLongBreak()\
    .export("bookAlarm.mp3")
