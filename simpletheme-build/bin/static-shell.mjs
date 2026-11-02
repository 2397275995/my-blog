/**
 * 生成纯静态部署所需的 HTML 外壳 + 托管配置。
 *
 * 背景：本主题对外的 HTML 外壳原本由 WordPress 的 index.php 渲染，
 * 构建产物 dist/ 里只有 JS/CSS。要做「无后端」的静态托管，需要按
 * <outDir>/.vite/manifest.json 生成一份等价外壳。
 *
 * 这个脚本不做任何视觉/逻辑改动，只负责：
 *   1. 读 manifest，把 frontend 入口的 JS/CSS 按真实文件名写进 index.html
 *   2. 写入 window.__ST_SITE_NAME__ 与最小 SimpleThemeConfig
 *   3. 生成 SPA 回退规则 _redirects
 *
 * 运行: node bin/static-shell.mjs
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, resolve } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')
const dist = join(root, process.argv[2] || 'dist')

const manifestPath = join(dist, '.vite', 'manifest.json')
if (!existsSync(manifestPath)) {
  console.error('找不到 <outDir>/.vite/manifest.json，请先执行 vite build')
  process.exit(1)
}

const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'))
const entry = manifest['src/main.ts']
if (!entry) {
  console.error('manifest 中缺少 src/main.ts 入口')
  process.exit(1)
}

// 站点信息：从 admin/content.json 读取，改后台就能同步到 <title> / og / __ST_SITE_NAME__
// （早先这里写死过 'iielxy'，导致后台改名后浏览器标题不跟着变）
function readSiteInfo() {
  const contentPath = join(root, '..', 'admin', 'content.json')
  const fallback = { name: 'iielxy', desc: '记录技术、实践与思考', url: '' }
  try {
    const content = JSON.parse(readFileSync(contentPath, 'utf8'))
    const site = content.siteInfo || {}
    return {
      name: site.name || fallback.name,
      desc: site.description || fallback.desc,
      url: site.url || fallback.url,
    }
  } catch (err) {
    console.warn('  ! 读不到 admin/content.json，使用默认站点名：' + err.message)
    return fallback
  }
}

const site = readSiteInfo()
const SITE_NAME = site.name
const SITE_DESC = site.desc
const SITE_URL = site.url

/** HTML 属性/文本转义，站点名里可能带引号或 & */
function escHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

/**
 * 递归收集入口及其静态 import 链上的全部 CSS。
 *
 * 关键：Vite 会把组件样式按 chunk 拆成多个 .css，只有把它们都写进 HTML，
 * 弹窗、插画等组件的样式才会生效。（主题原本由 PHP 的
 * simple_theme_collect_entry_css() 做这件事，静态构建必须自己补上）
 */
function collectCss(manifest, key, seen = new Set(), out = []) {
  const chunk = manifest[key]
  if (!chunk || seen.has(key)) return out
  seen.add(key)
  for (const file of chunk.css || []) {
    if (!out.includes(file)) out.push(file)
  }
  for (const dep of chunk.imports || []) {
    collectCss(manifest, dep, seen, out)
  }
  return out
}

const cssFiles = collectCss(manifest, 'src/main.ts')
const cssLinks = cssFiles
  .map((file) => `    <link rel="stylesheet" href="/${file}">`)
  .join('\n')
console.log('  CSS 共 ' + cssFiles.length + ' 个：' + cssFiles.map((f) => f.split('/').pop()).join(', '))

const html = `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${escHtml(SITE_NAME)}</title>
    <meta name="description" content="${escHtml(SITE_DESC)}">
    <meta property="og:type" content="website">
    <meta property="og:title" content="${escHtml(SITE_NAME)}">
    <meta property="og:description" content="${escHtml(SITE_DESC)}">
    ${SITE_URL ? `<meta property="og:url" content="${escHtml(SITE_URL)}">` : ''}
    <meta name="theme-color" content="#f5f6f7" media="(prefers-color-scheme: light)">
    <meta name="theme-color" content="#1a1a1a" media="(prefers-color-scheme: dark)">
    <link rel="icon" href="/favicon.ico">
    <link rel="manifest" href="/manifest.webmanifest">
    <script>
      window.__ST_SITE_NAME__ = ${JSON.stringify(SITE_NAME)};
      // 静态部署没有 WordPress：只覆盖插画目录，其余路径用主题自带的 origin 兜底
      // （siteUrl / homeUrl 必须是绝对地址，否则主题内部的 new URL() 会抛错）
      window.SimpleThemeConfig = {
        illustrationsUrl: window.location.origin + '/illustrations/',
      };
      (function () {
        var theme = localStorage.getItem('theme');
        if (theme !== 'light' && theme !== 'dark') {
          theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        document.documentElement.setAttribute('data-theme', theme);
        document.documentElement.style.colorScheme = theme;
      })();
    </script>
${cssLinks}
  </head>
  <body class="simple-theme-shell">
    <div id="app"></div>
    <script type="module" src="/${entry.file}"></script>
  </body>
</html>
`

writeFileSync(join(dist, 'index.html'), html)
console.log('  ✓ dist/index.html')

// SPA 回退：所有未命中静态文件的路径都交给前端路由
writeFileSync(join(dist, '_redirects'), '/*    /index.html   200\n')
console.log('  ✓ dist/_redirects')

// 静态资源长缓存，HTML 每次回源
writeFileSync(
  join(dist, '_headers'),
  [
    '/assets/*',
    '  Cache-Control: public, max-age=31536000, immutable',
    '',
    '/index.html',
    '  Cache-Control: public, max-age=0, must-revalidate',
    '',
    '/*',
    '  X-Content-Type-Options: nosniff',
    '  Referrer-Policy: strict-origin-when-cross-origin',
    '',
  ].join('\n'),
)
console.log('  ✓ dist/_headers')
