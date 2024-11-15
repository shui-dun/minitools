---
ctimeFilter: ""
excludedTags:
  - 数学
  - 科学
  - Paper
page: 0
---
```meta-bind-button
label: 搜索
icon: ""
hidden: true
class: ""
tooltip: ""
id: "refresh"
style: primary
actions:
  - type: command
    command: dataview:dataview-force-refresh-views

```
```meta-bind-button
label: 上
icon: ""
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
    ms: 200
  - type: command
    command: dataview:dataview-force-refresh-views

```
```meta-bind-button
label: 下
icon: ""
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
    ms: 200
  - type: command
    command: dataview:dataview-force-refresh-views

```
`INPUT[inlineList:excludedTags]` `INPUT[date:ctimeFilter]` `BUTTON[prepage]` `INPUT[number:page]` `BUTTON[nextpage]` `BUTTON[refresh]` 
```dataviewjs
const {WaitLoading, Note} = await cJS();

await WaitLoading.wait(dv);

Note.dv = dv;
let noteInfo = Note.noteInfo();

let paragraph = dv.paragraph(`**<code>>> ${noteInfo.waitReviewCount} + ${noteInfo.todayReviewedCount} (${noteInfo.todayReviewedSize}KB)</code>**`);

let showSurprise = false;
paragraph.addEventListener("click", (evt) => {
    if (!showSurprise) {
        paragraph.innerHTML += " <b><code>ヽ(´▽`)/</code></b>";
        showSurprise = true;
    }
});

// 待复习笔记的列表
dv.table(["notes", "size"], noteInfo.toBeReviewedNotes
  .sort(x => x.sr[2])
  .slice(10 * dv.current().page, 10 * (dv.current().page + 1))
  .map(x => [x.file.link, (x.file.size / 1024).toFixed(1)])
);
```
