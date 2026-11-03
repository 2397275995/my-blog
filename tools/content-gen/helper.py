"""把「标题 + 小节」结构转成主题需要的 HTML 正文。

约定（每篇正文用同一套语法，避免 100 篇手写 HTML 出错）：
  ("小节标题", ["段落", "- 列表项", "```命令", "代码", "```"])
- 以 "- " 开头的行合并成无序列表
- ``` 成对包住的行转成 <pre><code>
- 其余非空行各自成段
"""


def _inline(text):
    """把 `code` 和 **粗体** 转成 HTML 标签"""
    import re
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text


def _slug_id(text, index):
    """给 h2 生成一个稳定 id（纯 ASCII，避免中文锚点）"""
    return 'sec-%d' % index


def render(sections):
    out = []
    for i, (heading, lines) in enumerate(sections, start=1):
        if heading:
            out.append('<h2 id="%s">%s</h2>' % (_slug_id(heading, i), heading))

        buf = []          # 待合并的段落
        items = []        # 待合并的列表项
        code = []         # 代码块缓冲
        in_code = False

        def flush():
            nonlocal buf, items
            for p in buf:
                out.append('<p>%s</p>' % _inline(p))
            if items:
                out.append('<ul>' + ''.join('<li>%s</li>' % _inline(x) for x in items) + '</ul>')
            buf, items = [], []

        for raw in lines:
            line = raw.rstrip()

            if line.strip() == '```':
                if in_code:
                    out.append('<pre><code>%s</code></pre>' % '\n'.join(code))
                    code, in_code = [], False
                else:
                    flush()
                    in_code = True
                continue

            if in_code:
                code.append(line)
                continue

            if not line.strip():
                flush()
                continue

            if line.startswith('- '):
                buf and flush()
                items.append(line[2:].strip())
            else:
                if items:
                    flush()
                buf.append(line.strip())

        flush()
        if in_code and code:
            out.append('<pre><code>%s</code></pre>' % '\n'.join(code))

    return '\n'.join(out)


def make_post(pid, title, slug, category, tags, excerpt, sections, cover, date=None):
    if date is None:
        from datetime import datetime, timedelta
        base = datetime(2026, 10, 17, 9, 0)
        date = (base - timedelta(days=pid - 21)).strftime('%Y-%m-%dT%H:%M:00')

    return {
        'id': pid,
        'slug': slug,
        'title': title,
        'date': date,
        'modified': date,
        'category': category,
        'tags': tags,
        'excerpt': excerpt,
        'format': 'html',
        'body': '\n<p>%s</p>\n' % _inline(excerpt) + render(sections) + '\n',
        'published': True,
        'cover': '/covers/%s' % cover,
    }
