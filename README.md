# my-blog

个人博客：Vue 3 + Vite 静态站点，内容用一个 JSON 管理，构建后部署到腾讯 EdgeOne Pages。

## 结构

```
admin/
  content.json        内容源（文章、论文、项目、奖项、分类、菜单、站点设置）
  build.py            构建脚本：JSON → mock-data.ts → vite build → 静态外壳
  admin.py            本地后台服务（可选，127.0.0.1:8910）
  ui/                 本地后台界面
simpletheme-build/
  src/                主题源码（Vue 3 + TS）
  public/             静态资源；write.html 是在线写作页
  bin/static-shell.mjs 生成 index.html 外壳（含 SPA 回退、CSS 收集）
.github/workflows/
  deploy.yml          推送后自动构建并发布到 EdgeOne
```

## 本地开发

```bash
cd simpletheme-build
npm install
npm run dev          # http://localhost:5173
```

完整构建（含内容注入与静态外壳）：

```bash
python admin/build.py --rebuild   # 产物在 simpletheme-static/
```

本地后台（可视化编辑内容）：

```bash
双击 启动后台.bat    # http://127.0.0.1:8910
```

## 部署

推到 `main` 分支后，GitHub Actions 会自动：

1. `npm ci` 安装依赖
2. `python admin/build.py --rebuild` 生成静态站点
3. `edgeone pages deploy` 发布到 EdgeOne

需要在仓库里配置：

| 类型 | 名称 | 值 |
| --- | --- | --- |
| Secret | `EDGEONE_TOKEN` | EdgeOne 控制台生成的 API Token |
| Variable | `EDGEONE_PROJECT` | EdgeOne 项目名称 |

没配这两项时，Action 只构建、不发布。

## 在线写作

访问站点上的 `/write.html`（首页右上角「写博客」）。

填写仓库 `2397275995/my-blog`、分支 `main`、content.json 路径 `admin/content.json`，
以及一个有 **Contents: Read and write** 权限的 GitHub Token，即可在线写文章、收录论文、管理分类。

Token 只保存在浏览器本地。

## 文档

- `SimpleTheme-说明.md`：结构与常见改动位置
- `在线写作后台-说明.md`：在线写作的完整配置与排错
- `发布到EdgeOne-说明.md`：三种发布方式对比
