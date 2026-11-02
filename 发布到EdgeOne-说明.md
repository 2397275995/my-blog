# 更新后怎么发到 EdgeOne（三种方式）

改完内容，永远是这个流程：**本地构建 → 推送到 EdgeOne**。
构建必须在本地做（内容在 `admin/content.json`，后台是本地 Python 服务，EdgeOne 那边跑不了）。

推送有三种方式，按省事程度排序。

---

## 方案 A：一键脚本（日常推荐）

双击根目录的 **`发布到EdgeOne.bat`**。

它会依次做这几件事：

1. 检查 `simpletheme-static/index.html` 在不在
2. 问你「先重新构建站点吗？」—— 改了内容就输 `y`，约 3 分钟
3. 第一次运行会让你填一次 **EdgeOne 项目名称**，之后记在 `edgeone-project.txt` 里
4. 检查登录状态，没登录会弹浏览器登录一次（凭据保存到本地，以后不用再登）
5. 执行 `edgeone pages deploy simpletheme-static -n 项目名 -e production`

**第一次运行会比较慢**：npm 要下载 EdgeOne CLI（几十 MB），之后走缓存就快了。

底层命令是官方的：

```bash
npx -y edgeone pages deploy simpletheme-static -n 你的项目名 -e production
```

> 如果不想用脚本，也可以自己在命令行里敲这行。首次要先 `npx -y edgeone login`。

### 需要提前知道的两点

- 项目名称是**控制台里的项目名**（英文/数字那个），不是显示标题
- 如果项目当初是通过 Git 创建的，CLI 部署要求项目是「直接上传」类型，可能需要在控制台确认

---

## 方案 B：Git 自动部署（改得勤的话最省心）

在 EdgeOne 控制台把项目改成 Git 关联（GitHub / GitLab / Gitee），配置：

- **构建命令**：`echo skip`（产物已经提交进仓库，不需要再构建）
- **输出目录**：`simpletheme-static`

之后每次本地构建完，只要 `git add . && git commit -m "update" && git push`，
EdgeOne 自动拉取并发布。

好处：

- Git 只传差异，比每次传 2.4MB 整个目录快
- 有版本历史，出问题能回滚
- 手机上也能改（改 JSON 直接 push）

代价：要建一次仓库、配一次关联。配置完就一劳永逸。

---

## 方案 C：手动上传（原来的做法）

控制台「直接上传」，选 `simpletheme-static` 文件夹。
2.4MB 不算大，偶尔发一次完全够用，改得勤就会烦。

---

## 怎么选

| 情况 | 建议 |
| --- | --- |
| 一周改几次 | 方案 A，双击解决 |
| 每天都改，或者多台电脑改 | 方案 B，push 即发布 |
| 只是偶尔发一次 | 方案 C 也无所谓 |

---

## 三种方式都一样的部分

- 只上传 `simpletheme-static`，**不要**传 `simpletheme-build`（源码 + node_modules，近 1GB）
- 产物根目录必须有 `edgeone.json`（SPA 回退），没有的话刷新文章页会 404
- 上传后第一次看建议 `Ctrl+Shift+R` 强刷，Service Worker 会缓存旧版本

## 排错

| 现象 | 原因 |
| --- | --- |
| 部署成功但页面没变 | Service Worker 缓存，强刷；或浏览器缓存 |
| 刷新文章页 404 | `edgeone.json` 没上传或不在根目录 |
| 样式全丢 | `assets/` 没传全，重新完整上传 |
| 头像没变 | `img/` 没传上去；或忘了先构建 |
