"""
清理 simpletheme-build 里的历史副本。

只会删除这三类目录，别的一概不动：
  _old_static_*   每次构建替换下来的旧成品
  _scratch_*      调试时复制出来的站点副本
  dist-*          历史构建输出（保留最新一个）

用法：双击上级目录的「清理旧构建.bat」，或 python clean_build.py
"""

import os
import re
import shutil

BUILD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'simpletheme-build')

PATTERNS = [
    (r'^_old_static_\d{8}-\d{6}$', 0),
    (r'^_scratch_', 0),
    (r'^dist-\d{8}-\d{6}$', 1),   # 保留最新 1 个
]


def human(n):
    for unit in ('B', 'KB', 'MB', 'GB'):
        if n < 1024:
            return '%.1f %s' % (n, unit)
        n /= 1024
    return '%.1f TB' % n


def dir_size(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def main():
    if not os.path.isdir(BUILD_DIR):
        print('找不到构建目录：%s' % BUILD_DIR)
        input('按回车退出…')
        return

    entries = [d for d in os.listdir(BUILD_DIR) if os.path.isdir(os.path.join(BUILD_DIR, d))]
    targets = []

    for pattern, keep in PATTERNS:
        matched = sorted([d for d in entries if re.match(pattern, d)])
        if keep:
            matched = matched[:-keep] if len(matched) > keep else []
        targets.extend(matched)

    if not targets:
        print('没有需要清理的目录，构建目录很干净。')
        input('按回车退出…')
        return

    freed = 0
    print('将删除以下目录：')
    for name in targets:
        path = os.path.join(BUILD_DIR, name)
        size = dir_size(path)
        freed += size
        print('  %-36s %8s' % (name, human(size)))

    print('\n合计释放约 %s' % human(freed))
    answer = input('确认删除？输入 y 回车：').strip().lower()
    if answer != 'y':
        print('已取消。')
        input('按回车退出…')
        return

    for name in targets:
        try:
            shutil.rmtree(os.path.join(BUILD_DIR, name))
            print('  已删除 %s' % name)
        except Exception as e:
            print('  删除失败 %s：%s' % (name, e))

    print('\n清理完成。')
    input('按回车退出…')


if __name__ == '__main__':
    main()
