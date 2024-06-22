# 迷你工具箱

一系列迷你工具，不想一个个单独做成仓库，于是放在了一起

## 工具列表

- [replaceText](./replaceText) 替换指定文件夹下指定格式的文件中的指定文本
- [pipenvInstaller](./pipenvInstaller) 指定一个pipenv项目中的的python文件，会自动安装项目所需的python环境，并为该文件创建快捷方式。
- [online-text-processor](./online-text-processor) 基于 Vue.js 的纯前端文本处理工具
- [ahk](./ahk) autohotkey脚本
- [copyMd](./copyMd) 复制markdown以及其链接的本地图片（使用go实现）
- [rmMd](./rmMd) 删除markdown文件以及其链接的图片
- [obsidian-calendar](./obsidian-calendar) obsidian日历插件，支持循环事件
- [flatFolder](./flatFolder) 递归地读取文件夹下的所有文件，将其转化为一个大文件，以便于与Claude2等LLM通话。
- [handright](./handright) 使用handright库，生成手写笔记
- [fullScreenCheck](./fullScreenCheck) 当你运行全屏应用，例如全屏播放视频时，每隔一分钟，输入`'shift'+'ctrl'+'alt'+'.'`，使得Stretchly不要误以为你没有使用电脑
- [mklinks](./mklinks) 如果需要频繁地将某些文件或文件夹创建符号链接到多个不同目录，那么这个工具可能会对你有所帮助。
- [autoWechat](./autoWechat) 微信自动发消息（已废弃）
- [handles](./handles) 持续监视一个进程占有的句柄
- [checkMDImage](./checkMDImage) 检测某个目录下的markdown文件中所对应的本地图片是否存在，并检测文件夹中的文件是否被markdown文件引用
- [localizeWebsite](./localizeWebsite) 将一个网站中所有的文件中的所有远程路径改为本地路径，方便复刻网站
- [dictionaryAttack](./dictionaryAttack) 使用字典攻击破解压缩包密码
- [fullcpu](./fullcpu) 一键使CPU满载
- [dockerClear](./dockerClear) 清理docker-desktop占用的内存
- [randomFile](./randomFile) 生成指定大小的内容完全随机的文件
- [localizeMD](./localizeMD) 将指定文件夹下的所有markdown文件中引用的图片下载到本地
- [pipenvRun](./pipenvRun) 在windows上一键使用pipenv运行python文件
- [headers2dict](./headers2dict) 将http消息头转化为python字典（json）
- [downloader](./downloader) 多线程下载器（未完成）
- [html2pdf](./html2pdf) 将网页批量转化为pdf文件，方便打印
- [copyHtml](./copyHtml) 复制网页上的文本，以及latex公式
- [clash_helper](./clash_helper) 使用clash的restful API，实现代理手动切换，以方便爬虫绕过IP限制
- [lunarDateCrawling](./lunarDateCrawling) 农历日期爬取
- [cnkiCrawler](./cnkiCrawler) 爬取知网摘要数据（已废弃）
- [auto-qq](./auto-qq) 使用pyautogui，打开qq并自动发送消息（已废弃）
- [colorBlind](./colorBlind) 将图片处理后色盲容易辨认的图片，但效果不好
- [pan-spider](./pan-spider) 通过bing搜索找到有效的网盘链接（已废弃）
- [questionnaire-spider](./questionnaire-spider) 自动填写“问卷星”（已废弃）
- [lockScreen](./lockScreen) 一键锁屏，如果因为某种原因不适合使用 `Win+L`
- [saladictHelper](./saladictHelper) 沙拉查词无法获得输入框中的单词的上下文，在这个网页粘贴句子，沙拉查词就可以获取上下文
- [liuji](./liuji) 爬取六级词汇表（已废弃）
- [img-spider](./img-spider) 批量从百度图片上下载图片（已废弃）

## hooks

你可以将 [.githooks](.githooks) 软链接到 `.git/hooks`，以实现 `pre-commit` 时自动更新README

## License

[MIT](./LICENSE)