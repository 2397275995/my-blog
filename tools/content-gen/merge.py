"""把 p*.json 合并进 admin/content.json，带校验。"""
import collections
import glob
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
CONTENT = os.path.join(ROOT, 'admin', 'content.json')

c = json.load(open(CONTENT, encoding='utf-8'))
have_ids = {p['id'] for p in c['posts']}
have_slugs = {p['slug'] for p in c['posts']}
cats = {x['name'] for x in c['categories']}

new = []
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), 'p*.json'))):
    new += json.load(open(f, encoding='utf-8'))

dup_id = [p['id'] for p in new if p['id'] in have_ids]
counts = collections.Counter([p['slug'] for p in new] + list(have_slugs))
dup_slug = [s for s, n in counts.items() if n > 1]
bad_cat = sorted({p['category'] for p in new if p['category'] not in cats})

print('待合并 %d 篇 | 重复 id %s | 重复 slug %s | 未知分类 %s' % (len(new), dup_id, dup_slug, bad_cat))
if dup_id or dup_slug or bad_cat:
    raise SystemExit('校验未通过，未写入')

c['posts'].extend(new)
c['posts'].sort(key=lambda p: p['id'])
json.dump(c, open(CONTENT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('合并完成，总数 %d' % len(c['posts']))
