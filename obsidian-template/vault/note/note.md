---
ctimeFilter: ""
excludedTags:
  - 数学
  - 科学
  - Paper
  - CS
page: 0
openNextNote: random
---
```dataviewjs
const {WaitLoading, Utils, Note} = await cJS();
Note.init(dv);

await WaitLoading.wait(dv);

let noteInfo = Note.noteInfo();

dv.paragraph(
  Utils.container(
    Utils.multiselect(dv.current(), 'excludedTags', '[]'),
    Utils.date(dv.current(), 'ctimeFilter'),
    Utils.incButton('上', dv.current(), 'page', 0, null, -1, true),
    Utils.numInput(dv.current(), 'page'),
    Utils.incButton('下', dv.current(), 'page', 0, null, 1, true),
    Utils.button('搜', null, true),
    `<b><code>${noteInfo.waitReviewCount}+${noteInfo.todayReviewedCount}(${noteInfo.todayReviewedSize}KB)</code></b>`,
  )
);

// 待复习笔记的列表
dv.table(["notes", "size"], noteInfo.toBeReviewedNotes
  .sort(x => x.sr[2])
  .slice(10 * dv.current().page, 10 * (dv.current().page + 1))
  .map(x => [x.file.link, (x.file.size / 1024).toFixed(1)])
);
dv.paragraph(Utils.container(
	Utils.button('随机', async () => {
		await Note.randomNote();
	}),
	'复习后',
	Utils.select(dv.current(), 'openNextNote', `['no', 'random', 'next']`),
))
```
