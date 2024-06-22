<template>
  <div id="app">
    <div class="container">
      <!-- 文本输入和输出框 -->
      <div class="textarea-container">
        <textarea v-model="inputText" placeholder="输入文本" class="textarea"></textarea>
        <textarea v-model="outputText" placeholder="输出文本" class="textarea"></textarea>
      </div>
      <!-- 按钮区 -->
      <div class="button-container">
        <button @click="processText('uppercase')">转换为大写</button>
        <button @click="processText('lowercase')">转换为小写</button>
        <!-- 可以添加更多按钮 -->
      </div>
      <!-- 文本比较区 -->
      <div class="diff-container">
      <Diff :prev="inputText" :current="outputText" mode="split" theme="light" language="plaintext" />
      </div>
    </div>
  </div>
</template>

<script>
import { Diff } from 'vue-diff';
import 'vue-diff/dist/index.css';

export default {
  name: 'App',
  components: {
    Diff
  },
  data() {
    return {
      inputText: '',
      outputText: ''
    };
  },
  methods: {
    processText(type) {
      if (type === 'uppercase') {
        this.outputText = this.inputText.toUpperCase();
      } else if (type === 'lowercase') {
        this.outputText = this.inputText.toLowerCase();
      }
      // 添加更多处理逻辑
    }
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  margin-top: 60px;
}

.container {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.textarea-container {
  display: flex;
  width: 100%;
  max-width: 800px;
  justify-content: space-between;
  margin-bottom: 20px;
}

.textarea {
  width: 45%;
  height: 200px;
}

.button-container {
  display: flex;
  gap: 10px;
}

.diff-container {
  width: 100%;
  max-width: 800px;
  margin-top: 20px;
}

@media (max-width: 600px) {
  .textarea-container {
    flex-direction: column;
  }
  .textarea {
    width: 90%;
    margin-bottom: 10px;
  }
}
</style>
