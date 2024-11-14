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
async function waitForVaultLoading(){while(dv.current()===undefined){await new Promise(resolve=>setTimeout(resolve,200))}return dv.current()}await waitForVaultLoading();

function filterNotesByTags(tags) {
    // 定义被排除的标签前缀
    const excludedPrefixes = dv.current().excludedTags.map(tag => `#${tag}`);
    // 检查是否有任何一个标签不是以被排除的前缀开头，如果有则返回true
    for (let tag of tags) {
        if (!excludedPrefixes.some(prefix => tag.startsWith(prefix))) {
            return true;
        }
    }
    // 如果所有标签都以被排除的前缀开头，则返回false
    return false;
}

// 基础过滤得到的笔记
let basicNotes = dv
  .pages('"note" and -"note/assets"')
  .where(x => x.sr)
  .where(x => filterNotesByTags(x.file.tags))
  .where(x => x.ctime >= dv.current().ctimeFilter);

// 待复习的笔记
let toBeReviewedNotes = basicNotes
  .where(x => x.sr[2] <= dv.date('today'));

// 今日复习的笔记
let todayReviewedNotes = basicNotes
  // .where(x => x.ctime - 0 != dv.date('today') || x.sr[2] - 0 != dv.date('tomorrow')) // 不是今天创建的笔记
  .where(x => x.sr[2] == dv.duration(`${Math.ceil(x.sr[1])}day`) + dv.date('today'));

// 待复习笔记的数目
let waitReviewCount = toBeReviewedNotes
  .values
  .reduce((sum, x) => sum + 1, 0);

// 今日复习的笔记的数目
let todayReviewedCount = todayReviewedNotes
  .values
  .reduce((sum, x) => sum + 1, 0);

// 今日复习的笔记的大小（KB）
let todayReviewedSize = (todayReviewedNotes
  .values
  .reduce((sum, x) => sum + x.file.size, 0) / 1024).toFixed(0);

let paragraph = dv.paragraph(`**<code>>> ${waitReviewCount} + ${todayReviewedCount} (${todayReviewedSize}KB)</code>**`);

let showSurprise = false;
paragraph.addEventListener("click", (evt) => {
    if (!showSurprise) {
        paragraph.innerHTML += " <b><code>ヽ(´▽`)/</code></b>";
        showSurprise = true;
    }
});

// 待复习笔记的列表
dv.table(["notes", "size"], toBeReviewedNotes
  .sort(x => x.sr[2])
  .slice(10 * dv.current().page, 10 * (dv.current().page + 1))
  .map(x => [x.file.link, (x.file.size / 1024).toFixed(1)])
);
```
