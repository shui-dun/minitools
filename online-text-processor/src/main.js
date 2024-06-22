import { createApp } from 'vue';
import App from './App.vue';
import Diff from 'vue-diff';
import 'vue-diff/dist/index.css';

const app = createApp(App);
app.use(Diff);
app.mount('#app');
