# SimpleTheme 静态版 · 构建与部署说明

> 上游仓库：[worable233/SimpleTheme](https://github.com/worable233/SimpleTheme) v2.1.3（MIT）
> 做法：**直接用上游代码构建**，只替换内容层。没有自己另写一套页面。

> [!IMPORTANT]
> **日常改内容不要动代码**：双击 `启动后台.bat`，在浏览器里增删改文章，再点「构建发布」。
> 内容主库是 `admin/content.json`，`src/lib/mock-data.ts` 已经由它自动生成，手改会被覆盖（见第八节）。

---

## 一、目录分别是干什么的

| 目录 | 作用 | 要不要留 |
| --- | --- | --- |
| `admin/` | **后台管理界面**：`content.json` 内容主库 + 管理服务 + 构建脚本 | 保留 |
| `simpletheme/` | 上游源码克隆（内容文件由 `admin/build.py` 生成） | 保留 |
| `simpletheme-build/` | 构建工作区（含 node_modules，约 1GB）。跑构建用 | 保留，或下次重建时再装 |
| `simpletheme-static/` | **可以直接部署的成品**，2.2 MB，就是它上传到 Cloudflare Pages | 保留 |
| `启动后台.bat` / `启动预览.bat` | 双击启动后台 / 本地预览站点 | 保留 |
| `预览截图/` | 成品各页面截图，方便对照 | 可删 |

---

## 二、我到底改了哪些地方（全部清单）

你要求"只更改用户说明部分"。下面是逐条改动，一共 **5 处**，其中 3 处是内容，2 处是让静态托管能跑起来的必要配置。**组件、样式、布局、路由、交互逻辑一行没动。**

| # | 文件 | 改动 | 性质 |
| --- | --- | --- | --- |
| 1 | `src/lib/mock-data.ts` | 全部内容替换成你的：站点名 `iielxy`、描述、Hero 文案、统计数据、菜单、文章《记录思想与观察的空间》、4 个分类 | 内容 |
| 2 | `src/views/AboutView.vue` | "关于"页在没有 WordPress 时的兜底文案（原本是"这是一个基于 WordPress 构建的博客网站…"那四句）换成你的介绍 | 内容 |
| 3 | `.env`（新增文件） | `VITE_USE_MOCK=true` —— 打开主题内置的数据层，不连 WordPress | 配置 |
| 4 | `vite.config.ts` | 生产环境 `base` 由 `'./'` 改为 `'/'`。原因：主题用 History 路由，文章地址形如 `/ji-lu-.../`，相对路径在深层路由下会 404 | 配置 |
| 5 | `bin/static-shell.mjs`（新增脚本） | 按 `manifest.json` 生成 `index.html` / `_redirects` / `_headers`。原因：原主题的 HTML 外壳是 `index.php` 渲染的，静态托管没有 PHP，需要一份等价外壳 | 构建胶水 |

### 内容层里两处刻意的调整

- **菜单从 4 项减到 3 项**（首页 / 归档 / 关于），去掉了"友情链接"——你没有友链数据，点进去是一整屏空状态插图，很难看。
- **文章 `comment_status` 改为 `closed`**。静态站没有评论后端，开放评论等于让人填完表单提交失败。页面会显示"评论未开启"。

### 数据源说明

`src/lib/mock-data.ts` 现在就是你的**内容数据库**。加一篇新文章 = 在这个文件的 `mockPosts` 数组里加一个对象，然后重新构建。字段照抄现有那条改就行。

---

## 三、重新构建（改完内容后）

```bash
cd simpletheme-build

# 首次需要装依赖（约 6 分钟）
npm ci

# 1. 同步插画与表情资源
node bin/copy-illustrations.mjs
node bin/copy-emojis.mjs

# 2. 构建（每次换一个全新的 outDir，避免旧文件干扰）
npx vite build --outDir dist-final

# 3. 生成静态外壳 + 托管配置
node bin/static-shell.mjs dist-final

# 4. 代码高亮资源（这个脚本固定写 dist/，手动搬到产物里）
node bin/copy-prism.mjs
cp -r dist/prism dist-final/prism
```

然后把 `dist-final` 的内容覆盖到 `simpletheme-static/` 即可。

> 本机在装依赖时被文件系统保护拦过几次（npm 解包触发了批量删除保护），如果你在自己电脑上重跑通常不会遇到；真遇到就把 `node_modules` 删掉重新 `npm ci`。

---

## 四、部署到 Cloudflare Pages

1. 登录 https://dash.cloudflare.com → **Workers 和 Pages** → **创建** → **Pages** → **上传资源**
2. 项目名填 `iielxy`（决定域名 `iielxy.pages.dev`，要别的名字就填别的）
3. 把 **`simpletheme-static` 文件夹里的内容**整个拖进去（不是拖文件夹本身）
4. 部署

产物里已经带了两个关键文件，别漏掉：

- **`_redirects`** —— `/* /index.html 200`，让 `/about`、`/ji-lu-.../` 这些前端路由刷新时不会 404。**没有它，除了首页其他页面一刷新就挂。**
- **`_headers`** —— 静态资源长缓存 + 基础安全头。

想接 Git 自动发布：仓库根目录放这些内容，构建命令留空，输出目录填 `/`。

---

## 五、必须知道的三个限制

**1. 没有服务端直出，SEO 弱于 WordPress 版。**
原主题是 PHP 把首屏 HTML 直出再交给 Vue 接管，爬虫能看到完整正文。静态模式改成了纯客户端渲染——打开页面时先白一下，再把内容画出来；搜索引擎（尤其百度）抓取能力明显变差。

如果你的主要目的是"文章被人搜到"，这条路不如原来的 WordPress；如果只是"自己写、发给朋友看、留个作品集"，完全够用。

**2. 评论、说说、友链都是空壳。**
评论已关闭；`/shuoshuo`、`/links` 页面存在但内容为空，已从菜单摘掉。以后有数据了在 `mock-data.ts` 里补上、加回菜单即可。

**3. "一言"会请求第三方接口。**
侧栏的 Hitokoto 走 `https://v1.hitokoto.cn`。不想有外部请求，就在 `mock-data.ts` 的 `sidebar` 数组里删掉那一项。

---

## 六、以后有了服务器怎么办

不用改代码。两个方向：

**A. 想要完整主题（评论、搜索、后台管理都活）**
把 `.env` 里的 `VITE_USE_MOCK=true` 去掉，`VITE_WP_SITE_URL` 指向你的 WordPress 地址，重新构建，然后把 `dist/` 当静态前端用、WordPress 当后端。这时才是这个主题设计时的完整形态。

**B. 就想接着用纯静态**
继续改 `mock-data.ts` 重新构建，托管在任何静态服务上（Nginx / 宝塔 / Vercel / 对象存储都行）。
Nginx 记得配 SPA 回退：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}
```

---

## 七、上游版权

主题 MIT 协议，保留原仓库署名即可。页脚已经自带 `Theme SimpleTheme` 链接，不用动。

---

## 八、后台管理界面

### 打开

双击根目录的 **`启动后台.bat`**，或命令行：

```bash
cd admin
python admin.py
```

浏览器会自动打开 http://127.0.0.1:8910/

**注意：后台只监听本机（127.0.0.1），别人访问不到，也不会暴露到公网。** 它没有登录密码——因为只有本机能开，不要把它改成 `0.0.0.0`。

### 能干什么

| 页面 | 功能 |
| --- | --- |
| **文章** | 列表、搜索、新建、编辑、删除；草稿状态（存着但不上线） |
| **分类** | 增删分类；分类下还有文章时会拦住不让删 |
| **站点设置** | 站点名、副标题、首页大标题与介绍、关于页正文、备案号 |
| **构建发布** | 一键重新构建，实时看日志 |

### 写作时的两个约定

- **链接别名**（slug）只能用英文小写、数字和短横线，它决定文章网址 `/slug/`。中文标题请自己起个拼音别名。
- **正文格式**有两种，编辑器里可以切换：
  - `Markdown`（新建文章默认）—— 支持 `##` 标题、`-` 列表、`>` 引用、三反引号代码块、`**加粗**`、`` `行内代码` ``、`[文字](链接)`
  - `HTML` —— 直接写标签，已存在的两篇文章是这种格式

编辑器里可以点「预览」左右对照，字数会实时统计。

### 保存 ≠ 上线

保存只写进 `admin/content.json`。要让线上站点变化，必须去**「构建发布」点一次「重新构建站点」**（约 1～3 分钟）。

构建做的事情就是第四节那套命令，只是自动化了：生成内容文件 → `vite build` → 生成静态外壳 → 替换 `simpletheme-static`。旧版本会移到 `simpletheme-build/_old_static_<时间戳>`，想清理手动删掉即可。

### 数据与备份

- 内容主库：`admin/content.json`（可以直接用文本编辑器改，改完在后台点构建即可）
- 每次保存前会自动备份上一版到 `admin/content.json.bak`
- `src/lib/mock-data.ts` 是**生成产物**，别手改——下次构建会被 `content.json` 覆盖

### 命令行等价操作

```bash
cd admin
python build.py            # 只生成 mock-data.ts，不构建
python build.py --rebuild  # 生成 + 完整重建站点
```

适合改完 JSON 又不想开浏览器的时候。

---

## 九、三个收集模块（论文 / 项目 / 奖项）

除博客文章外，站点还有三类个人存档，左侧图标栏里各占一个入口。

| 页面 | 路由 | 内容 |
| --- | --- | --- |
| 论文 | `/papers` | 读过的论文：标题、作者、会议、年份、**一句话结论**、标签、阅读日期 |
| 项目 | `/projects` | 做过的项目：名称、角色、周期、状态、技术栈、做了什么 |
| 奖项 | `/awards` | 获奖记录：奖项名、颁发单位、级别、时间、说明、证书图片 |

### 数据在哪

都在 `admin/content.json` 里，分别是 `papers` / `projects` / `awards` 三个数组。
构建时由 `admin/build.py` 编译成 `mockPapers` / `mockProjects` / `mockAwards`。

### 怎么改

**推荐用后台**：双击 `启动后台.bat` → 左侧「论文 / 项目 / 奖项」→ 列表右上角「＋ 新增」，或点任意一行的「编辑」。

表单字段：

- 论文：标题\*、作者、期刊/会议、年份、分类、原文链接、标签、阅读日期、一句话结论
- 项目：项目名称\*、我的角色、周期、状态、链接、技术栈、做了什么
- 奖项：奖项名称\*、颁发单位、级别、获奖时间、证书图片地址、说明

带 `*` 的是必填。标签和技术栈用逗号分隔（中英文逗号都行），会自动拆成一个个小 chip。

改完必须去「构建发布」点一次「重新构建站点」，线上才会变。**保存 ≠ 上线。**

### 页面行为

- **论文**：按「分类」字段自动汇总筛选标签（全部 / 自然语言处理 / 知识图谱…），新增分类不用改代码。分类和标签重复时只显示一次。
- **项目**：双列卡片，按周期倒序；状态自动分色（含「运行/进行」绿色，「交付/上线/完成」蓝色）。
- **奖项**：单列卡片，左侧金色奖杯徽章，级别做成徽章展示。
- 三个页面移动端都做了适配（卡片铺满、标签换行）。

### 证书图片

奖项的「证书图片地址」填站内相对路径即可，例如把扫描件放到 `simpletheme-build/public/awards/guojiang.png`，
字段填 `/awards/guojiang.png`。填了才会在页面上出现「查看证书」入口。

> 注意：`public/` 下的文件在构建时会被整目录复制到产物根目录，所以路径是 `/awards/...` 而不是 `/public/awards/...`。

---

## 十、部署到腾讯 EdgeOne Pages

### 上传哪个目录

**只传 `simpletheme-static/`**——这是构建产物，2.4MB，里面 `index.html` 在根。

- 控制台「直接上传」时选 `simpletheme-static` 这个文件夹，它里面的内容会成为站点根目录
- **不要传 `simpletheme-build/`**，那是源码 + node_modules，近 1GB，传上去也没用

### 必须存在的 edgeone.json

EdgeOne Pages **不识别 Cloudflare 的 `_redirects`**，SPA 回退要用它自己的 `edgeone.json`。
产物根目录已经有这个文件（由 `public/edgeone.json` 在构建时复制进去）：

```json
{
  "rewrites": [{ "source": "/*", "destination": "/index.html" }],
  "headers": [
    { "source": "/assets/*", "headers": [{ "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }] }
  ]
}
```

`/* → /index.html` 这条会被识别为 SPA fallback：先匹配静态资源和函数，都没命中才回 index.html。
**没有它，`/papers`、`/archives`、每篇文章的地址一刷新就是 404。**

### 三个平台的文件对照

| 平台 | 回退配置 | 缓存/响应头 |
| --- | --- | --- |
| Cloudflare Pages | `_redirects` | `_headers` |
| EdgeOne Pages | `edgeone.json` → `rewrites` | `edgeone.json` → `headers` |
| Nginx | `try_files $uri $uri/ /index.html` | 自行配置 |

产物里同时放了 `_redirects`、`_headers` 和 `edgeone.json`，三套并存互不干扰，换平台不用改。

### 上传后检查这几项

1. 首页能打开，样式正常（说明 `assets/` 传全了）
2. 点进任意一篇文章，**刷新页面**，还是文章页而不是 404（说明 SPA 回退生效）
3. 打开 `/papers`、`/archives` 直接刷新同样正常
4. 头像是你上传的那张（说明 `img/` 传上去了）
