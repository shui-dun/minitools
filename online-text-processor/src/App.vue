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
        <button @click="processText('uppercase')" class="button">转换为大写</button>
        <button @click="processText('lowercase')" class="button">转换为小写</button>
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
  text-align: center;
  margin-top: 60px;
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
  max-width: 800px;
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
  gap: 10px;
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
