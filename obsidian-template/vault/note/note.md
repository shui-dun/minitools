---
ctimeFilter: ""
excludedTags:
  - 数学
  - 科学
  - Paper
  - CS
page: 0
---
```dataviewjs
const {WaitLoading, Beautify, Note} = await cJS();
Note.dv = dv;
Beautify.app = app;

await WaitLoading.wait(dv);

let noteInfo = Note.noteInfo();

dv.paragraph(
  Beautify.container(
    Beautify.multiselect(dv.current(), 'excludedTags', '[]'),
    Beautify.date(dv.current(), 'ctimeFilter'),
    Beautify.incButton('上', dv.current(), 'page', 0, null, -1, true),
    Beautify.numInput(dv.current(), 'page'),
    Beautify.incButton('下', dv.current(), 'page', 0, null, 1, true),
    Beautify.button('搜', null, true),
    `<b><code>${noteInfo.waitReviewCount}+${noteInfo.todayReviewedCount}(${noteInfo.todayReviewedSize}KB)</code></b>`
  )
);

// 待复习笔记的列表
dv.table(["notes", "size"], noteInfo.toBeReviewedNotes
  .sort(x => x.sr[2])
  .slice(10 * dv.current().page, 10 * (dv.current().page + 1))
  .map(x => [x.file.link, (x.file.size / 1024).toFixed(1)])
);
```
