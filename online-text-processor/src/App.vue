<template>
  <div id="app">
    <!-- 标题和图片 -->
    <div class="header-container">
      <img src="@/assets/logo.png" alt="Text Processor" class="header-image">
      <h3>TextProcessor</h3>
    </div>
    <div class="container">
      <!-- 文本输入和输出框 -->
      <div class="textarea-container">
        <textarea v-model="inputText" placeholder="输入文本" class="textarea"></textarea>
        <textarea v-model="outputText" placeholder="输出文本" class="textarea"></textarea>
      </div>
      <!-- 按钮区 -->
      <div class="button-container">
        <button v-for="action in actions" :key="action.label" @click="processText(action.func)" class="button">
          {{ action.label }}
        </button>
        <button @click="applyOutput" class="button apply-button">应用</button>
      </div>
      <!-- 文本比较区 -->
      <div class="diff-container">
        <Diff :prev="inputText" :current="outputText" :mode="diffMode" theme="light" language="plaintext" />
      </div>
    </div>
  </div>
</template>

<script>
import { Diff } from 'vue-diff';

export default {
  name: 'App',
  components: {
    Diff
  },
  data() {
    return {
      inputText: '',
      outputText: '',
      diffMode: 'split',
      actions: [
        {
          label: '替换公式风格',
          func: (text) => {
            // 替换行内数学公式
            text = text.replace(/\\\(\s*(.{0,}?)\s*\\\)/g, '$$$1$$');
            // 替换块级数学公式
            text = text.replace(/\\\[(\s*[\s\S]*?\s*)\\\]/g, '$$$$$1$$$$');
            return text;
          }
        },
        {
          label: '隐藏Markdown标题',
          func: (text) => {
            // 遍历每一行，检测是否以# 开头，如果是，只将#用``包裹
            return text.split('\n').map(line => {
              if (/^#+\s+/.test(line)) {
                return line.replace(/^(#+)\s+/, '`$1` ');
              }
              return line;
            }).join('\n');
          }
        },
        {
          label: '移除Markdown标签',
          func: (text) => {
            // 移除markdown中的特定标签
            text = text.replace(/`<ignore-until-end\/>`/g, '');
            text = text.replace(/`<todo>`[\s\S]*?`<\/todo>`/g, '');
            text = text.replace(/`<comment>`[\s\S]*?`<\/comment>`/g, '');
            // 超过两个换行符替换为两个换行符
            text = text.replace(/\n([ \t]*\n[ \t]*)+\n/g, '\n\n');
            return text;
          },
        },
        {
          label: '去除粗体',
          func: (text) => {
            // 移除markdown中的粗体标记
            return text.replace(/\*\*(.*?)\*\*/g, '$1').replace(/__(.*?)__/g, '$1');
          }
        },
        { label: '转换为大写', func: (text) => text.toUpperCase() },
        { label: '转换为小写', func: (text) => text.toLowerCase() }
      ]
    };
  },
  mounted() {
    if (/Mobi|Android|iPhone|iPad|iPod/.test(navigator.userAgent)) {
      this.diffMode = 'unified';
    }
  },
  methods: {
    processText(func) {
      this.outputText = func(this.inputText);
    },
    applyOutput() {
      this.inputText = this.outputText;
    }
  }
}
</script>

<style>
#app {
  text-align: center;
}

.header-container {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.header-image {
  width: 70px;
  height: auto;
  margin-right: 10px;
}

.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.textarea-container {
  display: flex;
  width: 100%;
  justify-content: space-between;
  margin-bottom: 20px;
}

.textarea {
  width: 45%;
  height: 200px;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 10px;
  font-size: 14px;
  transition: box-shadow 0.3s ease-in-out;
}

.textarea:focus {
  box-shadow: 0 0 8px rgba(0, 123, 255, 0.5);
}

.button-container {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.button {
  padding: 10px 20px;
  font-size: 14px;
  border: none;
  border-radius: 4px;
  background: #007bff;
  color: white;
  cursor: pointer;
  transition: background 0.3s ease-in-out;
}

.button:hover {
  background: #0056b3;
}

.apply-button {
  background: #28a745;
}

.apply-button:hover {
  background: #218838;
}

.diff-container {
  width: 100%;
  margin-top: 20px;
}

@media (max-width: 600px) { /* 当设备的视口宽度不超过 600 像素时，应用特定的样式规则 */
  .textarea-container {
    flex-direction: column;
  }
  .textarea {
    width: 90%;
    margin-bottom: 10px;
  }
  .button-container {
    flex-direction: column;
    width: 100%;
  }
  .button {
    font-size: 12px;
    padding: 8px 16px;
    width: 90%;
    margin: 5px auto;
  }
}
</style>
