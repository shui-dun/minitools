```dataviewjs
const {WaitLoading, Files} = await cJS();
await WaitLoading.wait();

let pages = dv.pages('"'+Files.getFolderPath(dv.current().file.path)+'"')
    // 只获得直接的folder note
	.where(f => {
        let path = f.file.path.split('/');
        return path[path.length - 3] == 'archive' && path[path.length - 1] == path[path.length - 2] + '.md';
    })
    .sort(f => f.file.name, 'desc');

dv.table([""], pages.map(p => [p.file.link]));
```
