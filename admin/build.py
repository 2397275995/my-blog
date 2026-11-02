"""
把 admin/content.json 编译成主题需要的内容文件，并重建静态站。

内容主库是 content.json，别直接改 mock-data.ts —— 每次构建都会覆盖它。

命令行用法：
    python build.py            只生成 mock-data.ts
    python build.py --rebuild  生成 + 完整重建站点
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
import time

ADMIN_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ADMIN_DIR)
CONTENT_FILE = os.path.join(ADMIN_DIR, 'content.json')

BUILD_DIR = os.path.join(ROOT, 'simpletheme-build')
SRC_DIR = os.path.join(ROOT, 'simpletheme')
SITE_DIR = os.path.join(ROOT, 'simpletheme-static')

MOCK_TARGETS = [
    os.path.join(BUILD_DIR, 'src', 'lib', 'mock-data.ts'),
    os.path.join(SRC_DIR, 'src', 'lib', 'mock-data.ts'),
]

# 主题的设计令牌，保持上游默认值，不参与内容编辑
THEME_TS = """  theme: {
    primaryColor: '#333333',
    bodyFont: '"MiSans VF", "OPPO Sans", "SF Pro SC", HarmonyOS_Regular, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "PingFang SC", "Segoe UI", "Noto Sans", "Microsoft Yahei", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji"',
    codeFont: '"Fira Code", "Cascadia Code", "JetBrains Mono", "SF Mono", ui-monospace, "Menlo", "Monaco", "Consolas", "Liberation Mono", "Courier New", monospace',
    radius: 'medium' as const,
    shadow: 'small' as const,
    backgroundLight: '#f5f6f7',
    backgroundDark: '#1a1a1a',
    cardLight: '#ffffff',
    cardDark: '#222222',
    foregroundLight: '#333333',
    foregroundDark: '#e0e0e0',
    accentLight: '#f5f5f5',
    accentDark: '#2a2a2a',
    borderLight: '#e2e2e2',
    borderDark: '#333333',
    containerMaxWidth: 1500,
    articleMaxWidth: 900,
    cardMeta: {
      showCategory: true,
      showPublishDate: true,
      showModifiedDate: false,
      showCommentCount: false,
      showViewCount: false,
      showReadingTime: true,
      showWordCount: false,
      showAuthor: true,
    },
  },"""


# ---------------------------------------------------------------- 内容读写

def load_content():
    with open(CONTENT_FILE, encoding='utf-8') as f:
        return json.load(f)


def save_content(data):
    tmp = CONTENT_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CONTENT_FILE)


def count_words(text):
    """中文按字、英文按词，粗略统计字数。"""
    text = re.sub(r'<[^>]+>', '', text or '')
    cjk = len(re.findall(r'[\u4e00-\u9fff]', text))
    latin = len(re.findall(r'[A-Za-z0-9_]+', text))
    return cjk + latin


def html_to_text(html):
    return re.sub(r'<[^>]+>', '', html or '').strip()


# ---------------------------------------------------------------- Markdown

def _inline(text):
    """行内语法：行内代码、加粗、斜体、链接。先转义再替换。"""
    s = (text.replace('&', '&amp;').replace('<', '&lt;')
             .replace('>', '&gt;').replace('"', '&quot;'))
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(^|[^*])\*([^*]+)\*', r'\1<em>\2</em>', s)
    s = re.sub(r'\[([^\]]+)\]\((https?:[^)\s]+)\)', r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md):
    """Markdown 子集 → HTML，规则与后台编辑器里的实现保持一致。"""
    lines = (md or '').replace('\r\n', '\n').split('\n')
    out, buf, i = [], [], 0

    def flush():
        if buf:
            out.append('<p>%s</p>' % _inline(' '.join(buf)))
            buf.clear()

    while i < len(lines):
        line = lines[i]

        if re.match(r'^```\s*[A-Za-z0-9+#_-]*\s*$', line):
            flush()
            code = []
            i += 1
            while i < len(lines) and not re.match(r'^```\s*$', lines[i]):
                code.append(lines[i])
                i += 1
            i += 1
            esc = '\n'.join(code).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            out.append('<pre><code>%s</code></pre>' % esc)
            continue

        m = re.match(r'^(#{2,4})\s+(.*)$', line)
        if m:
            flush()
            lv = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (lv, _inline(m.group(2)), lv))
            i += 1
            continue

        m = re.match(r'^#\s+(.*)$', line)
        if m:
            flush()
            out.append('<h2>%s</h2>' % _inline(m.group(1)))
            i += 1
            continue

        if re.match(r'^>\s?', line):
            flush()
            q = []
            while i < len(lines) and re.match(r'^>\s?', lines[i]):
                q.append(re.sub(r'^>\s?', '', lines[i]))
                i += 1
            out.append('<blockquote><p>%s</p></blockquote>' % _inline(' '.join(q)))
            continue

        if re.match(r'^\s*[-*+]\s+', line):
            flush()
            items = []
            while i < len(lines) and re.match(r'^\s*[-*+]\s+', lines[i]):
                items.append('<li>%s</li>' % _inline(re.sub(r'^\s*[-*+]\s+', '', lines[i])))
                i += 1
            out.append('<ul>%s</ul>' % ''.join(items))
            continue

        if re.match(r'^\s*\d+\.\s+', line):
            flush()
            items = []
            while i < len(lines) and re.match(r'^\s*\d+\.\s+', lines[i]):
                items.append('<li>%s</li>' % _inline(re.sub(r'^\s*\d+\.\s+', '', lines[i])))
                i += 1
            out.append('<ol>%s</ol>' % ''.join(items))
            continue

        if re.match(r'^\s*(-{3,}|\*{3,})\s*$', line):
            flush()
            out.append('<hr>')
            i += 1
            continue

        if not line.strip():
            flush()
            i += 1
            continue

        buf.append(line.strip())
        i += 1

    flush()
    return '\n'.join(out)


def post_html(post):
    """取文章正文的 HTML：优先用已渲染结果，Markdown 则现渲染。"""
    rendered = post.get('rendered') or ''
    if rendered:
        return rendered
    body = post.get('body') or ''
    return md_to_html(body) if post.get('format') == 'md' else body


def compute_stats(content):
    posts = [p for p in content['posts'] if p.get('published', True)]
    words = sum(count_words(post_html(p)) for p in posts)
    tags = set()
    for p in posts:
        for t in p.get('tags') or []:
            tags.add(t)
    dates = sorted(p['date'] for p in posts) if posts else ['2026-01-01T00:00:00']
    return {
        'postCount': len(posts),
        'categoryCount': len(content.get('categories') or []),
        'tagCount': len(tags),
        'shuoshuoCount': len(content.get('shuoshuo') or []),
        'totalWordCount': words,
        'commentCount': 0,
        'registeredDate': dates[0],
        'lastActivityDate': dates[-1],
    }


# ---------------------------------------------------------------- 生成 TS

def write_text(path, text):
    """写文本。

    Windows 上目标文件常被杀毒/索引服务短暂占用，直接 open(w) 会 PermissionError。
    改为先写同目录临时文件，再 os.replace 原子替换——替换只需目录项操作，
    即使原文件正被读也不会失败；失败则退避重试。
    """
    last = None
    for attempt in range(8):
        tmp = '%s.tmp%d' % (path, attempt)
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write(text)
            os.replace(tmp, path)
            return
        except (PermissionError, OSError) as e:
            last = e
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            time.sleep(0.3 * (attempt + 1))
    raise last


def js(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if value is None:
        return "''"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def build_mock_data(content):
    site = content['siteInfo']
    hero = site.get('hero') or {}
    stats = compute_stats(content)

    out = []
    out.append('// 此文件由 admin/build.py 从 admin/content.json 自动生成，请勿手工编辑。\n')

    # ---- siteInfo
    out.append('export const mockSiteInfo = {')
    out.append('  name: %s,' % js(site.get('name', '')))
    out.append('  description: %s,' % js(site.get('description', '')))
    out.append('  url: %s,' % js(site.get('url', '')))
    out.append('  introTitle: %s,' % js(site.get('introTitle', '')))
    out.append('  introSubtitle: %s,' % js(site.get('introSubtitle', '')))
    out.append('  hero: {')
    out.append('    enabled: %s,' % js(bool(hero.get('enabled', True))))
    out.append("    displayMode: 'inset' as const,")
    out.append('    useImage: %s,' % js(bool(hero.get('useImage'))))
    out.append('    image: %s,' % js(hero.get('image', '')))
    out.append('    showAvatar: %s,' % js(bool(hero.get('showAvatar'))))
    out.append('    avatar: %s,' % js(hero.get('avatar', '')))
    out.append('    title: %s,' % js(hero.get('title', '')))
    out.append('    subtitle: %s,' % js(hero.get('subtitle', '')))
    out.append('    typewriterEnabled: false,')
    out.append('    typewriterInterval: 110,')
    out.append("    typewriterTexts: '',")
    out.append('  },')
    out.append(THEME_TS)
    out.append('  stats: {')
    out.append('    postCount: %d,' % stats['postCount'])
    out.append('    categoryCount: %d,' % stats['categoryCount'])
    out.append('    tagCount: %d,' % stats['tagCount'])
    out.append('    shuoshuoCount: %d,' % stats['shuoshuoCount'])
    out.append('    totalWordCount: %d,' % stats['totalWordCount'])
    out.append('    commentCount: %d,' % stats['commentCount'])
    out.append('    registeredDate: %s,' % js(stats['registeredDate']))
    out.append('    lastActivityDate: %s,' % js(stats['lastActivityDate']))
    out.append('  },')

    links = site.get('socialLinks') or []
    if links:
        out.append('  socialLinks: [')
        for s in links:
            out.append('    { label: %s, url: %s, icon: %s },'
                       % (js(s.get('label')), js(s.get('url')), js(s.get('icon', 'link'))))
        out.append('  ],')
    else:
        out.append('  socialLinks: [],')

    out.append('  comments: {')
    out.append('    requireNameEmail: true,')
    out.append('    registrationOnly: false,')
    out.append('    showEmailField: true,')
    out.append('    showUrlField: true,')
    out.append('    showCookiesOptIn: true,')
    out.append('  },')
    out.append('  collections: {')
    out.append('    homePostCount: 15,  // 首页每页 15 篇，配合 HomeView 的翻页')
    out.append('    shuoshuoPageSize: 12,')
    out.append('  },')
    out.append('  icp: %s,' % js(site.get('icp', '')))
    out.append('  icpGov: %s,' % js(site.get('icpGov', '')))

    sidebar = site.get('sidebar') or []
    out.append('  sidebar: [')
    for item in sidebar:
        t = item.get('type')
        st = item.get('settings') or {}
        if t == 'profile':
            out.append("    { type: 'profile' as const, settings: { showStats: %s, showHeatmap: %s, showSocial: %s } },"
                       % (js(bool(st.get('showStats', True))), js(bool(st.get('showHeatmap', True))),
                          js(bool(st.get('showSocial', True)))))
        elif t == 'hitokoto':
            out.append("    { type: 'hitokoto' as const, settings: { api: %s } },"
                       % js(st.get('api', 'https://v1.hitokoto.cn')))
        elif t == 'html':
            out.append("    { type: 'html' as const, html: %s },"
                       % js(item.get('html', '')))
        else:
            out.append("    { type: 'techInfo' as const },")
    if not sidebar:
        out.append("    { type: 'profile' as const, settings: { showStats: true, showHeatmap: true, showSocial: true } },")
        out.append("    { type: 'techInfo' as const },")
    out.append('  ],')
    out.append('}\n')

    # ---- 菜单
    out.append('export const mockMenuItems = [')
    for i, m in enumerate(content.get('menus') or [], start=1):
        url = m.get('url', '/')
        out.append('  {')
        out.append('    id: %d,' % (m.get('id') or i))
        out.append('    title: %s,' % js(m.get('title', '')))
        out.append('    url: %s,' % js(url))
        out.append('    path: %s,' % js(url))
        out.append('    target: %s,' % js(m.get('target', '')))
        out.append("    description: '',")
        out.append('    current: %s,' % js(url == '/'))
        out.append('    icon: %s,' % js(m.get('icon', 'link')))
        out.append('    children: [],')
        out.append('  },')
    out.append(']\n')

    # ---- 文章（只输出已发布的）
    posts = [p for p in content['posts'] if p.get('published', True)]
    posts.sort(key=lambda p: p['date'], reverse=True)
    out.append('export const mockPosts = [')
    for p in posts:
        rendered = post_html(p)
        body_words = count_words(rendered)
        reading = max(1, round(body_words / 300))
        excerpt_html = p.get('excerptHtml') or ('<p>%s</p>' % (p.get('excerpt') or ''))
        cats = [p['category']] if p.get('category') else []
        out.append('  {')
        out.append('    id: %d,' % int(p.get('id') or 1))
        out.append('    date: %s,' % js(p['date']))
        out.append('    modified: %s,' % js(p.get('modified') or p['date']))
        out.append('    link: %s,' % js('/%s/' % p['slug']))
        out.append('    slug: %s,' % js(p['slug']))
        out.append("    type: 'post',")
        out.append("    comment_status: 'closed' as const,")
        out.append('    title: { rendered: %s },' % js(p.get('title', '')))
        out.append('    excerpt: { rendered: %s },' % js(excerpt_html))
        out.append('    content: { rendered: %s },' % js(rendered))
        out.append('    categories: [%s],' % ', '.join(js(c) for c in cats))
        out.append('    tags: [%s],' % ', '.join(js(t) for t in (p.get('tags') or [])))
        out.append('    featuredImage: %s,' % js(p.get('cover', '')))
        out.append('    commentCount: 0,')
        out.append('    viewCount: 0,')
        out.append('    wordCount: %d,' % body_words)
        out.append('    readingTime: %d,' % reading)
        out.append('  },')
    out.append(']\n')

    # ---- 说说
    out.append('export const mockShuoshuo = [')
    for s in content.get('shuoshuo') or []:
        out.append('  {')
        out.append('    id: %d,' % int(s.get('id') or 1))
        out.append('    date: %s,' % js(s['date']))
        out.append('    modified: %s,' % js(s.get('modified') or s['date']))
        out.append('    link: %s,' % js('/shuoshuo/%s/' % s['slug']))
        out.append('    slug: %s,' % js(s['slug']))
        out.append("    type: 'shuoshuo',")
        out.append("    comment_status: 'closed' as const,")
        out.append('    title: { rendered: %s },' % js(s.get('title') or '说说'))
        out.append('    excerpt: { rendered: %s },' % js('<p>%s</p>' % (s.get('body') or '')))
        out.append('    content: { rendered: %s },' % js('<p>%s</p>' % (s.get('body') or '')))
        out.append('    categories: [],')
        out.append('    tags: [],')
        out.append("    featuredImage: '',")
        out.append('    commentCount: 0,')
        out.append('    viewCount: 0,')
        out.append('    wordCount: %d,' % count_words(s.get('body') or ''))
        out.append('    readingTime: 1,')
        out.append('  },')
    out.append(']\n')

    # ---- 分类
    out.append('export const mockCategories: Array<{ id: number; name: string; slug: string }> = [')
    for i, c in enumerate(content.get('categories') or [], start=1):
        out.append('  { id: %d, name: %s, slug: %s },'
                   % (int(c.get('id') or i), js(c['name']), js(c.get('slug') or 'c%d' % i)))
    out.append(']\n')

    # ---- 友链
    out.append('export const mockLinkCategories = [')
    for lc in content.get('links') or []:
        out.append('  {')
        out.append('    id: %d,' % int(lc.get('id') or 1))
        out.append('    name: %s,' % js(lc.get('name', '')))
        out.append('    slug: %s,' % js(lc.get('slug', 'links')))
        out.append('    description: %s,' % js(lc.get('description', '')))
        out.append('    links: [')
        for i, l in enumerate(lc.get('links') or [], start=1):
            out.append(
                "      { id: %d, name: %s, url: %s, description: %s, image: '', target: '_blank', rating: %d, notes: '' },"
                % (i, js(l.get('name')), js(l.get('url')), js(l.get('description', '')), int(l.get('rating') or 5)))
        out.append('    ],')
        out.append('  },')
    out.append(']')

    # ---- 论文收集
    out.append('\nexport const mockPapers = [')
    for p in content.get('papers') or []:
        out.append('  {')
        out.append('    id: %d,' % int(p.get('id') or 1))
        out.append('    title: %s,' % js(p.get('title', '')))
        out.append('    authors: %s,' % js(p.get('authors', '')))
        out.append('    venue: %s,' % js(p.get('venue', '')))
        out.append('    year: %s,' % js(str(p.get('year', ''))))
        out.append('    category: %s,' % js(p.get('category', '')))
        out.append('    summary: %s,' % js(p.get('summary', '')))
        out.append('    url: %s,' % js(p.get('url', '')))
        out.append('    tags: [%s],' % ', '.join(js(t) for t in (p.get('tags') or [])))
        out.append('    readDate: %s,' % js(p.get('readDate', '')))
        out.append('  },')
    out.append(']\n')

    # ---- 项目收集
    out.append('export const mockProjects = [')
    for p in content.get('projects') or []:
        out.append('  {')
        out.append('    id: %d,' % int(p.get('id') or 1))
        out.append('    name: %s,' % js(p.get('name', '')))
        out.append('    role: %s,' % js(p.get('role', '')))
        out.append('    period: %s,' % js(p.get('period', '')))
        out.append('    status: %s,' % js(p.get('status', '')))
        out.append('    summary: %s,' % js(p.get('summary', '')))
        out.append('    stack: [%s],' % ', '.join(js(t) for t in (p.get('stack') or [])))
        out.append('    url: %s,' % js(p.get('url', '')))
        out.append('  },')
    out.append(']\n')

    # ---- 奖项收集
    out.append('export const mockAwards = [')
    for a in content.get('awards') or []:
        out.append('  {')
        out.append('    id: %d,' % int(a.get('id') or 1))
        out.append('    name: %s,' % js(a.get('name', '')))
        out.append('    issuer: %s,' % js(a.get('issuer', '')))
        out.append('    level: %s,' % js(a.get('level', '')))
        out.append('    date: %s,' % js(a.get('date', '')))
        out.append('    summary: %s,' % js(a.get('summary', '')))
        out.append('    certificate: %s,' % js(a.get('certificate', '')))
        out.append('  },')
    out.append(']')

    return '\n'.join(out) + '\n'


def write_mock_data(content):
    text = build_mock_data(content)
    written = []
    for path in MOCK_TARGETS:
        if os.path.isdir(os.path.dirname(path)):
            write_text(path, text)
            written.append(path)
    return written


ABOUT_TARGETS = [
    os.path.join(BUILD_DIR, 'src', 'views', 'AboutView.vue'),
    os.path.join(SRC_DIR, 'src', 'views', 'AboutView.vue'),
]


def render_about_html(text):
    """把纯文本（每行一段，## 开头为小标题）转成 about 页的段落。"""
    out = []
    for line in (text or '').splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith('## '):
            out.append('            <h3>%s</h3>' % s[3:].strip())
        else:
            out.append('            <p>%s</p>' % s)
    return '\n'.join(out)


def write_about(content):
    """把关于页正文写进 AboutView.vue 的兜底块（模板结构不变，只换文字）。"""
    text = (content.get('siteInfo') or {}).get('about') or ''
    if not text.strip():
        return []
    block = render_about_html(text)
    patched = []
    pattern = re.compile(
        r'(<div class="about-page__fallback">\s*\n\s*<h2>.*?</h2>\n)(.*?)(\s*</div>)', re.S)
    for path in ABOUT_TARGETS:
        if not os.path.isfile(path):
            continue
        with open(path, encoding='utf-8') as f:
            src = f.read()
        new_src, n = pattern.subn(lambda m: m.group(1) + block + '\n' + m.group(3), src)
        if n:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_src)
            patched.append(path)
    return patched


# ---------------------------------------------------------------- 重建站点

def _node_env():
    env = os.environ.copy()
    managed = r'C:\Users\23972\.workbuddy\binaries\node\versions\22.22.2'
    if os.name == 'nt' and os.path.isdir(managed):
        env['PATH'] = managed + os.pathsep + env.get('PATH', '')
    return env


def rebuild():
    """生成内容 → 构建 → 生成外壳 → 替换成品。逐步 yield 日志。"""
    content = load_content()
    stamp = time.strftime('%Y%m%d-%H%M%S')

    yield '① 生成内容文件 mock-data.ts'
    for p in write_mock_data(content):
        yield '   → %s' % os.path.relpath(p, ROOT)
    if write_about(content):
        yield '   → 更新关于页正文'

    out_dir = 'dist-%s' % stamp
    yield '② 构建前端（约 30 秒）'
    # 用字符串而不是列表：shell=True 时 POSIX 只把列表第一项当命令，
    # 在 GitHub Actions 的 Linux 上会退化成裸跑 npx。
    proc = subprocess.run(
        'npx vite build --outDir %s' % out_dir,
        cwd=BUILD_DIR, env=_node_env(),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        shell=True,
    )
    tail = [l for l in (proc.stdout or '').splitlines() if l.strip()][-6:]
    for l in tail:
        yield '   ' + l[:160]
    if proc.returncode != 0:
        yield '✗ 构建失败，站点未更新'
        return

    yield '③ 生成静态外壳'
    proc = subprocess.run(
        'node bin/static-shell.mjs %s' % out_dir,
        cwd=BUILD_DIR, env=_node_env(),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True,
    )
    for l in (proc.stdout or '').splitlines():
        yield '   ' + l

    dist = os.path.join(BUILD_DIR, out_dir)

    # prism 代码高亮资源由 node_modules 生成到 dist/prism。
    # 本地可能早就有了，但 GitHub Actions 是干净环境，必须先生成再复制。
    prism_src = os.path.join(BUILD_DIR, 'dist', 'prism')
    if not os.path.isdir(prism_src):
        subprocess.run(
            'node bin/copy-prism.mjs',
            cwd=BUILD_DIR, env=_node_env(), shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )

    if os.path.isdir(prism_src) and not os.path.isdir(os.path.join(dist, 'prism')):
        shutil.copytree(prism_src, os.path.join(dist, 'prism'))
        yield '   → 复制 prism 代码高亮资源'
    elif not os.path.isdir(prism_src):
        yield '   ! 没找到 prism 资源，代码高亮可能失效'

    yield '④ 替换线上成品'
    moved = False
    if os.path.isdir(SITE_DIR):
        old = os.path.join(BUILD_DIR, '_old_static_%s' % stamp)
        try:
            shutil.move(SITE_DIR, old)
            moved = True
            yield '   → 旧版本移到 simpletheme-build/%s' % os.path.basename(old)
        except OSError as e:
            # 常见原因：有程序开着这个目录（预览服务、资源管理器）。
            # 移不走就原地覆盖，不至于让整次构建白跑。
            yield '   ! 旧版本移不走（目录可能被占用），改为覆盖写入'
            yield '     %s' % e

    if moved or not os.path.isdir(SITE_DIR):
        shutil.copytree(dist, SITE_DIR)
    else:
        shutil.copytree(dist, SITE_DIR, dirs_exist_ok=True)
    yield '✓ 完成，刷新站点即可看到新内容'


def main():
    args = sys.argv[1:]
    content = load_content()
    if '--rebuild' in args:
        for line in rebuild():
            print(line, flush=True)
    else:
        for p in write_mock_data(content):
            print('已生成', os.path.relpath(p, ROOT))
        if write_about(content):
            print('已更新关于页正文')


if __name__ == '__main__':
    main()
