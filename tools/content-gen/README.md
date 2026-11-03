# 批量内容生成脚本

用来一次性往 `admin/content.json` 里灌入结构化短文（当前 100 篇的产出工具）。

## 用法

```bash
cd tools/content-gen
python batch1.py            # 产出 p1.json
...
python merge.py             # 合并 p*.json 到 admin/content.json（带 id/slug/分类校验）
```

## 约定

- `helper.py` 里的 `make_post()` 负责把「标题 + 小节」转成主题需要的 HTML 正文
- 小节内容支持三种行：普通段落、`- ` 列表项、``` 包裹的代码块
- 行内可用 `` `code` `` 和 `**粗体**`
- 不传 `date` 时按 id 自动排布日期（id 越大越新）

新增批次时照抄 `batch1.py` 的结构即可，注意每个 `make_post(...)` 调用结尾是 `))`。
