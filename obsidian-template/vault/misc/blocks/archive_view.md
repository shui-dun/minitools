```dataviewjs
const {WaitLoading, Files} = await cJS();
await WaitLoading.wait();

let isArchive = (f) => {
	let path = f.file.path.split('/');
	return path[path.length - 3] == 'archive' && path[path.length - 1] == path[path.length - 2] + '.md';
};

let pages = dv.pages(`"${dv.current().file.folder}"`)
	.where(isArchive)
    .sort(f => f.file.name, 'desc');

dv.table(["本目录归档文件"], pages.map(p => [p.file.link]));

let pages2 = dv.pages(`"${Files.getParentPath(dv.current().file.folder)}"`)
	.where(isArchive)
    .sort(f => f.file.name, 'desc');

let grandFather = (p) => {
	let path = Files.getParentPath(Files.getParentPath(p.file.folder));
	let name = Files.getFileName(path);
	path = `${path}/${name}`;
	return `[[${path}|${name}]]`;
};

dv.table(["子目录归档文件", "目录名"], pages2.map(p => [p.file.link, grandFather(p)]));
```
