---
filterStatus: 
page: 0
---
## 西西弗斯
^p1
```meta-bind-button
label: ""
icon: "search"
hidden: true
class: ""
tooltip: ""
id: "refresh"
style: primary
actions:
  - type: command
    command: dataview:dataview-force-refresh-views
  - type: open
    link: "[p1](#^p1)"
    newTab: false
```
```meta-bind-button
label: ""
icon: "chevron-left"
hidden: true
class: ""
tooltip: ""
id: prepage
style: default
actions:
  - type: updateMetadata
    bindTarget: page
    evaluate: true
    value: "x > 0 ? x - 1 : 0"
  - type: sleep
    ms: 300
  - type: command
    command: dataview:dataview-force-refresh-views
  - type: open
    link: "[p1](#^p1)"
    newTab: false
```
```meta-bind-button
label: ""
icon: "chevron-right"
hidden: true
class: ""
tooltip: ""
id: nextpage
style: default
actions:
  - type: updateMetadata
    bindTarget: page
    evaluate: true
    value: x + 1
  - type: sleep
    ms: 300
  - type: command
    command: dataview:dataview-force-refresh-views
  - type: open
    link: "[p1](#^p1)"
    newTab: false
```
状态 `INPUT[inlineSelect(option(null),option(待测评),option(待笔试),option(待AI面),option(待1面),option(待2面),option(待3面),option(待HR面),option(待offer),option(offer),option(再说),option(不投)):filterStatus]` `INPUT[number:page]` `BUTTON[refresh]` 
```dataviewjs
const {WaitLoading, Beautify, Habit, Task} = await cJS();
Beautify.app = app;
await WaitLoading.wait(dv);

let filterStatus = dv.current().filterStatus || "";
let notes = dv
  .pages('"job/jobList"')
  .where(x => 
    (!filterStatus || x.status === filterStatus))
  .sort(x => {
    // 不投的排在投的后面
    const deliverySortValue = x.status === '不投' ? 1 : 0;
    // 按照endTime排序
    const endTimeSortValue = x.endTime == null ? Infinity : x.endTime;
    // 再说的排在其他的前面
    const statusSortValue = x.status === '再说' ? 0 : 1;
    // 按照ctime排序
    const ctimeSortValue = x.ctime == null ? Infinity : x.ctime;
    return [deliverySortValue, endTimeSortValue, statusSortValue, ctimeSortValue];
  });

const itemsPerPage = 50;
const nPages = Math.ceil(notes.length / itemsPerPage);
const summary = `**\`page: ${dv.current().page} / ${nPages - 1}, ${notes.length} items\`**`;
dv.paragraph(summary);
dv.table(["名称", "结束时间", "状态", "备注", "创建时间", "地点"], notes
  .slice(itemsPerPage * dv.current().page, itemsPerPage * (dv.current().page + 1))
  .map(x => [x.file.link, x.endTime, x.status, Beautify.textArea(x, 'note'), x.ctime,  x.locations?.join(',')])
);
dv.paragraph(summary);
```
`BUTTON[prepage]` `INPUT[number:page]` `BUTTON[nextpage]` `BUTTON[refresh]` 

## 事项

```meta-bind-embed
[复习事项](复习事项.md)
```

## 统计

```dataviewjs
let notes = dv.pages('"job/jobList"');

let statusCounts = notes
  .groupBy(x => x.status)
  .map(group => ({ status: group.key, count: group.rows.length }))
  .array(); 
const labels = statusCounts.map(item => item.status == null ? "" : item.status);
const data = statusCounts.map(item => item.count);
let totalCount = statusCounts.reduce((sum, item) => sum + item.count, 0);
const chartData = {  
    type: 'bar',
    data: {
        labels: labels,
        datasets: [{
            label: `公司总数：${totalCount}`,
            data: data,
        }]
    }
}
window.renderChart(chartData, this.container);

// 绘制桑基图
// 定义状态映射
const statusMap = {
  'Start': 'Start',
  '待测评': 'ToEvaluate',
  '再说': 'Pending',
  '不投': 'NoDelivery',
  '待发通知': 'WaitNotification',
  '待笔试': 'ToTest',
  '待AI面': 'ToAIInterview',
  '待1面': 'To1stInterview',
  '待2面': 'To2ndInterview',
  '待3面': 'To3rdInterview',
  '待HR面': 'ToHRInterview',
  '待offer': 'WaitingOffer',
  'offer': 'Offer'
};

// 定义状态转换图（有向无环图）
const graph = {
  'Start': ['ToEvaluate', 'Pending', 'NoDelivery', 'WaitNotification'],
  'ToEvaluate': ['ToTest'],
  'ToTest': ['ToAIInterview'],
  'ToAIInterview': ['To1stInterview'],
  'To1stInterview': ['To2ndInterview'],
  'To2ndInterview': ['To3rdInterview'],
  'To3rdInterview': ['ToHRInterview'],
  'ToHRInterview': ['WaitingOffer'],
  'WaitingOffer': ['Offer']
};

// 拓扑排序（反向）
function topologicalSort(graph) {
  const visited = new Set();
  const temp = new Set();
  const order = [];
  
  function visit(node) {
    if (temp.has(node)) return;
    if (visited.has(node)) return;
    
    temp.add(node);
    
    const neighbors = graph[node] || [];
    for (const neighbor of neighbors) {
      visit(neighbor);
    }
    
    temp.delete(node);
    visited.add(node);
    order.push(node); // 添加到末尾，这样最终态会在前面
  }
  
  for (const node in graph) {
    if (!visited.has(node)) {
      visit(node);
    }
  }
  
  return order;
}

// 统计每个状态的原始数量
const rawCounts = {};
notes.forEach(note => {
  const status = statusMap[note.status || 'Start'] || note.status;
  rawCounts[status] = (rawCounts[status] || 0) + 1;
});

// 获取拓扑排序（从终态开始）
const sortedStatuses = topologicalSort(graph);

// 计算累积数量
const cumulativeCounts = {...rawCounts};
for (const status of sortedStatuses) {
  const nextNodes = graph[status] || [];
  for (const next of nextNodes) {
    cumulativeCounts[status] = (cumulativeCounts[status] || 0) + (cumulativeCounts[next] || 0);
  }
}

// 构建桑基图数据
let mermaidCode = 
  "```mermaid\n" +
  "%%{init: {'themeCSS': '.node{fill: #ccc;}'}}%%\n" +
  "sankey-beta\n\n";

// 使用累积数量构建转换关系
for (const from in graph) {
  const nextNodes = graph[from];
  for (const to of nextNodes) {
    if (cumulativeCounts[to] > 0) {
      mermaidCode += `${from},"${to}",${cumulativeCounts[to]}\n`;
    }
  }
}

mermaidCode += "```";

dv.paragraph(mermaidCode);
```
