import json
import sys

sys.path.insert(0, '.')
from helper import make_post

P = []

P.append(make_post(21, 'journalctl 查服务日志的六个常用姿势', 'journalctl-logs', '系统运维', ['systemd', '日志'],
    '不只会 systemctl status，定位服务问题时真正好用的是 journalctl 的这几组参数。',
    [('一、先按时间倒序看最近', [
        '排查问题第一步永远是从最近的日志开始看，而不是从头翻。',
        '```', 'journalctl -u nginx -n 100 --no-pager', '```',
        '- `-u` 指定服务单元，`-n` 取最后 N 行，`--no-pager` 避免分页器吞掉输出',
        '- 想实时跟：`journalctl -u nginx -f`，等价于 tail -f',
    ]),
     ('二、按时间段切片', [
        '知道故障大概发生在几点，比盲翻几百行有效得多。',
        '```', 'journalctl -u myapp --since "2026-11-01 09:00" --until "2026-11-01 10:00"', '```',
        '也支持 `--since "1 hour ago"` 这种相对写法。',
    ]),
     ('三、只看错误级别', [
        '`-p err` 过滤出 error 及以上，日志量立刻降一个数量级。',
        '- `-p err` 只保留 err、crit、alert、emerg',
        '- `-p warning` 放宽一档',
        '- 配合 `-o short-precise` 能看清毫秒级的时间顺序',
    ]),
     ('四、格式化输出', [
        '`-o json-pretty` 适合看结构化字段，`-o cat` 只留消息正文、去掉时间戳和主机名前缀，复制日志给别人时更干净。',
    ]),
     ('五、注意持久化', [
        '默认日志可能只存在内存里，重启就没了。检查 `/etc/systemd/journald.conf` 里的 `Storage=`，改成 `persistent` 后会落到 `/var/log/journal`。',
        '另外 `SystemMaxUse=` 控制上限，别忘了设，不然磁盘会被日志吃掉。',
    ])],
    'post-11.svg', '2026-10-28T09:20:00'))

P.append(make_post(22, 'cron 还是 systemd timer：怎么选', 'cron-vs-timer', '系统运维', ['cron', 'systemd'],
    '两者都能定时跑任务，差别在日志、依赖和错过的补偿。',
    [('一、cron 的优势是简单', [
        '一行写完就能跑，不需要额外的单元文件。临时任务、几行脚本，用 cron 最快。',
        '```', '0 3 * * * /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1', '```',
        '注意 `%` 在 crontab 里有特殊含义，命令里出现要转义成 `\\%`。',
    ]),
     ('二、timer 的优势是可观测', [
        'systemd timer 的输出直接进 journal，`systemctl list-timers` 能看到上次和下次执行时间，排查「到底跑没跑」不用翻邮件。',
        '- 支持 `OnBootSec`、`OnUnitActiveSec` 这类相对时间',
        '- 可以设置 `Persistent=true`，关机期间错过的任务开机后补跑',
        '- 依赖管理：`After=`、`Requires=` 直接复用 systemd 的能力',
    ]),
     ('三、我的选择标准', [
        '- 一次性、临时、个人机器：cron',
        '- 生产服务、需要日志和对账：timer',
        '- 任务需要跑很久、要限制资源：timer + `CPUQuota=`',
    ]),
     ('四、踩过的坑', [
        'cron 的环境变量极简，PATH 只有 `/usr/bin:/bin`。很多「手动能跑、定时不行」都是因为脚本里调用了 `/usr/local/bin` 下的程序。解决办法是在脚本开头显式设置 PATH。',
    ])],
    'post-12.svg', '2026-10-27T21:05:00'))

P.append(make_post(23, 'top 里到底该看哪几个数', 'top-metrics', '系统运维', ['性能', '监控'],
    'load average 高不高、内存还剩多少，这几个数字的真实含义常被误读。',
    [('一、load average 的三种解读', [
        '三个数字分别是 1 分钟、5 分钟、15 分钟的平均负载。',
        '- 4 核机器 load 4.0 表示刚好跑满，不是「4 倍过载」',
        '- 1 分钟高、15 分钟低：突发流量，通常不用管',
        '- 15 分钟持续高：真的扛不住了，要看是谁在占 CPU',
        '- load 高但 CPU 空闲，多半卡在 IO 或不可中断睡眠（D 状态）',
    ]),
     ('二、内存要看 available', [
        '别盯 free 那一列。Linux 会把空闲内存拿去做缓存，看起来「用完了」很正常。看 `available` 才是应用真正还能申请的量。',
        '```', 'free -h', "```",
        '如果 available 持续低于总量 10%，并且 swap 在频繁换入换出（`si`/`so` 非零），那就是真的不够了。',
    ]),
     ('三、按内存排序抓元凶', [
        '```', 'ps aux --sort=-%mem | head -10', '```',
        'CPU 同理换成 `--sort=-%cpu`。比在 top 里翻页快得多，也方便贴给别人看。',
    ])],
    'post-13.svg', '2026-10-27T10:40:00'))

P.append(make_post(24, 'swap 到底该不该开', 'swap-oom', '系统运维', ['内存', 'swap'],
    '关于 swap 的争论很多，实际决策要看你的应用类型和内核版本。',
    [('一、swap 的作用被误解了', [
        'swap 不是「内存不够时的备用内存」，它更大的价值是让内核能把长期不活跃的匿名页换出去，腾出物理内存做文件缓存。完全关掉 swap 有时反而让内存回收更激进。',
    ]),
     ('二、什么情况该开', [
        '- 有大量长生命周期但长期不活跃的进程（个人服务器、开发机）',
        '- 内存 2G 以下的小机器，留一点缓冲能避免瞬时峰值直接把服务打死',
        '- 数据库机器要谨慎：交换会带来不可预期的延迟抖动',
    ]),
     ('三、swappiness 怎么调', [
        '```', 'cat /proc/sys/vm/swappiness', 'sysctl -w vm.swappiness=10', '```',
        '默认 60 偏激进。服务器上常用 10，数据库机器可以设 1 甚至 0（0 表示尽量不用，但 8G 以上内存的新内核里 0 并不等于完全禁用）。',
    ]),
     ('四、OOM killer 不是敌人', [
        '真的内存耗尽时，内核会挑一个进程杀掉。避免全局崩溃的重点不是关 swap，而是给关键服务设 `OOMScoreAdjust=-500`，让它别被优先选中。',
        '```', 'systemctl show -p OOMScoreAdjust myapp', '```',
    ])],
    'post-14.svg', '2026-10-26T16:30:00'))

P.append(make_post(25, 'Too many open files 的定位与修复', 'ulimit-nofile', '系统运维', ['文件句柄', '排错'],
    '句柄打满不是简单调大限制就完事，先搞清楚是谁没释放。',
    [('一、先确认确实是句柄问题', [
        '```', 'ulimit -n', 'cat /proc/<pid>/limits | grep "open files"', 'ls /proc/<pid>/fd | wc -l', '```',
        '第二条看进程软限制，第三条看它当前真正占用了多少。数量逼近软限制就是它。',
    ]),
     ('二、临时调大', [
        '```', 'ulimit -n 65535', '```',
        '只对当前 shell 生效，子进程继承。想永久生效改 `/etc/security/limits.conf`，注意 systemd 服务不吃这个文件，要写 `LimitNOFILE=`。',
    ]),
     ('三、systemd 服务的正确写法', [
        '```', '[Service]', 'LimitNOFILE=65535', '```',
        '改完 `systemctl daemon-reload` 再 restart，光 restart 不生效。',
    ]),
     ('四、别忘了查泄露', [
        '如果句柄数持续上涨不回落，调大只是推迟爆炸时间。看句柄类型：',
        '```', 'ls -l /proc/<pid>/fd | awk "{print $11}" | sort | uniq -c | sort -rn | head', '```',
        '大量 `socket:` 指向连接没关，大量普通文件指向日志或临时文件没 close。',
    ])],
    'post-15.svg', '2026-10-26T09:15:00'))

P.append(make_post(26, '磁盘满了但 du 找不到大文件：inode 用光', 'inode-full', '系统运维', ['磁盘', '排错'],
    'df 显示 100%，du 加起来却只有一半——八成是 inode 或已删除但仍被占用的文件。',
    [('一、先分辨是空间还是 inode', [
        '```', 'df -h /', 'df -i /', '```',
        '`df -h` 显示满、`df -i` 显示 IUse% 100%，就是 inode 耗尽：文件数量太多，单个文件很小。',
    ]),
     ('二、inode 耗尽的常见来源', [
        '- session 文件（PHP 的 `/var/lib/php/sessions`）',
        '- 邮件队列 `/var/spool/postfix`',
        '- 日志轮转后留下的大量小文件',
        '- 定时任务生成的时间戳文件没有清理',
    ]),
     ('三、另一种情况：文件被删除但没释放', [
        '`du` 算不出来但空间没回来，说明有进程还开着已删除的句柄。',
        '```', 'lsof +L1 2>/dev/null | head', '```',
        '重启对应进程，或者 `> /proc/<pid>/fd/<n>` 清空即可回收。',
    ]),
     ('四、预防', [
        '给 `/var/log` 配好 logrotate 的 `maxage`，对小文件密集的目录单独挂一个分区，这样涨爆也只影响局部。',
    ])],
    'post-16.svg', '2026-10-25T20:10:00'))

P.append(make_post(27, '防火墙入门：firewalld 与 iptables 该用哪个', 'firewall-basics', '系统运维', ['防火墙', '网络'],
    '新系统默认是 firewalld，老脚本里全是 iptables 规则，两者关系先理清。',
    [('一、它们不是替代关系', [
        'firewalld 是 nftables/iptables 之上的管理层，规则最终还是会落到内核。用 firewalld 就别同时手写 iptables 规则，否则会互相覆盖。',
    ]),
     ('二、firewalld 常用操作', [
        '```', 'firewall-cmd --list-all', 'firewall-cmd --add-service=https --permanent', 'firewall-cmd --reload', '```',
        '`--permanent` 不加就只对当前运行时生效，重载即丢。这个坑几乎人人踩过一次。',
    ]),
     ('三、开放单个端口', [
        '```', 'firewall-cmd --add-port=8080/tcp --permanent', 'firewall-cmd --reload', '```',
    ]),
     ('四、只允许某网段访问', [
        '```', 'firewall-cmd --permanent --add-rich-rule="rule family=ipv4 source address=10.0.0.0/8 port port=3306 protocol=tcp accept"', '```',
        '这比直接开放 3306 安全得多，数据库端口不要对全网开。',
    ]),
     ('五、排查思路', [
        '连不上时按「服务有没有监听 → 本机防火墙 → 云安全组 → 中间网络设备」的顺序排，别一上来就关防火墙。',
        '```', 'ss -lntp | grep 8080', '```',
    ])],
    'post-17.svg', '2026-10-25T11:25:00'))

P.append(make_post(28, '端口被占用：ss 与 lsof 的用法差异', 'port-occupied', '系统运维', ['网络', '排错'],
    '启动服务报 address already in use，怎么最快找到是谁占着。',
    [('一、ss 更快', [
        '```', 'ss -lntp | grep :8080', '```',
        '`-l` 监听、`-n` 数字端口、`-t` TCP、`-p` 显示进程。需要 root 才能看到别人的进程名。',
    ]),
     ('二、lsof 更细', [
        '```', 'lsof -i :8080', '```',
        '能看到文件描述符、连接状态和对端地址，排查「谁在连我」时更方便。',
    ]),
     ('三、TIME_WAIT 不是占用', [
        '重启服务时看到大量 TIME_WAIT，这不是端口被占，是正常的连接关闭流程。真要缓解可以调 `net.ipv4.tcp_tw_reuse=1`。',
        '但如果报错是 `address already in use` 且 `ss` 里没有 LISTEN，那多半是残留进程还在。',
    ]),
     ('四、杀之前先想清楚', [
        '`kill -9` 会跳过清理逻辑，可能留下锁文件或半写的数据。优先 `systemctl stop`，再考虑 kill。',
    ])],
    'post-18.svg', '2026-10-24T15:50:00'))

P.append(make_post(29, 'logrotate 配置：别让日志吃掉磁盘', 'logrotate', '系统运维', ['日志', '自动化'],
    '默认配置只覆盖了系统日志，自己部署的服务往往没人管。',
    [('一、最小可用配置', [
        '在 `/etc/logrotate.d/` 下建一个文件，比如 `myapp`：',
        '```', '/var/log/myapp/*.log {', '    daily', '    rotate 14', '    compress', '    delaycompress', '    missingok', '    notifempty', '    copytruncate', '}', '```',
    ]),
     ('二、copytruncate 还是 reopen', [
        '写日志的程序如果不支持重开文件句柄，用 `copytruncate`：复制后截断原文件，进程无感知但有极小的丢日志窗口。',
        '支持信号的程序（比如 nginx）用 `postrotate` 发 `USR1` 更干净，会真正重开文件。',
    ]),
     ('三、先测试再上线', [
        '```', 'logrotate -d /etc/logrotate.d/myapp', '```',
        '`-d` 是 dry-run，只打印将要做什么，不实际动文件。`-f` 强制立即轮转，用来验证配置。',
    ]),
     ('四、监控轮转是否真的在跑', [
        '配置写错不会报错，只会静默不生效。挂一个「单个日志文件超过 1G 就告警」的检查，比事后救火强。',
    ])],
    'post-19.svg', '2026-10-24T10:05:00'))

P.append(make_post(30, 'sudo 权限精细化：别动不动给 ALL', 'sudo-rule', '系统运维', ['权限', '安全'],
    '让运维同学只能重启指定服务，而不是拥有全部权限。',
    [('一、默认配置的问题', [
        '`user ALL=(ALL) ALL` 意味着这个账号等同于 root，一旦泄露就是全盘失守。',
    ]),
     ('二、按命令授权', [
        '```', 'deploy ALL=(root) NOPASSWD: /bin/systemctl restart myapp', 'deploy ALL=(root) NOPASSWD: /bin/systemctl status myapp', '```',
        '注意 sudo 是按「命令行前缀」匹配的，允许 `systemctl` 就几乎等于允许所有 systemctl 操作。',
    ]),
     ('三、用别名管理', [
        '```', 'Cmnd_Alias APP_CTL = /bin/systemctl restart myapp, /bin/systemctl stop myapp', 'deploy ALL=(root) NOPASSWD: APP_CTL', '```',
        '命令多了必须用别名，否则规则很快就没法维护。',
    ]),
     ('四、验证与审计', [
        '```', 'sudo -l -U deploy', '```',
        '定期跑一遍，确认没有意外的 ALL。sudo 的每次调用都会记进 auth 日志（`/var/log/auth.log` 或 journal），出问题能追溯。',
    ])],
    'post-20.svg', '2026-10-23T19:30:00'))

P.append(make_post(31, '软链接与硬链接：什么时候用哪个', 'symlink-hardlink', '系统运维', ['文件系统', '基础'],
    'ln 和 ln -s 差一个字母，行为差别很大，用错会踩坑。',
    [('一、本质区别', [
        '- 硬链接：同一份 inode 的另一个名字，删掉任何一个名字文件都还在，直到链接数为 0',
        '- 软链接：一个存着目标路径的小文件，目标删了它就悬空',
        '- 硬链接不能跨文件系统，不能指向目录；软链接两者都可以',
    ]),
     ('二、典型用法', [
        '版本切换用软链接：',
        '```', 'ln -s /opt/app-1.4.2 /opt/app-current', '```',
        '升级时只需要改 `app-current` 指向，回滚就是把链接指回去，比改配置快得多。',
    ]),
     ('三、备份时的差别', [
        '`tar` 默认不跟随软链接（存的是链接本身），`-h` 才会解引用。想完整备份应用目录，通常要保留链接结构，不要加 `-h`。',
    ]),
     ('四、怎么看', [
        '```', 'ls -li', '```',
        '第一列是 inode，两个文件 inode 相同就是硬链接；`l` 开头的是软链接，后面跟着 `->` 目标。',
    ])],
    'post-2.svg', '2026-10-23T09:40:00'))

P.append(make_post(32, 'tar 打包：排除、增量与解压到指定目录', 'tar-usage', '系统运维', ['命令行', '备份'],
    'tar 参数多，但日常真正用得上的就那几个组合。',
    [('一、带排除打包', [
        '```', 'tar -czf app.tar.gz --exclude="*.log" --exclude="node_modules" ./app', '```',
        '排除模式要写在源目录前面，写后面不生效。',
    ]),
     ('二、看包内容再解压', [
        '```', 'tar -tzf app.tar.gz | head', '```',
        '先列一遍能避免「解压炸出一堆文件」的意外。',
    ]),
     ('三、解压到指定目录', [
        '```', 'mkdir -p /data/app && tar -xzf app.tar.gz -C /data/app', '```',
        '`-C` 必须在最后，且目标目录要已存在。',
    ]),
     ('四、增量备份', [
        '`--listed-incremental` 能做增量，但它依赖一个快照文件，且对文件移动很敏感。真要做可靠备份，我更推荐 rsync 加硬链接快照的方案。',
    ]),
     ('五、大数据量时的建议', [
        '压缩会吃满一个核。几 T 的数据打包时 `-I pigz` 用多核，速度差好几倍。',
    ])],
    'post-3.svg', '2026-10-22T20:15:00'))

P.append(make_post(33, 'find 的六个高频组合', 'find-usage', '系统运维', ['命令行'],
    '按时间、大小、权限找文件，配合 -exec 直接处理。',
    [('一、按时间清理', [
        '```', 'find /var/log -name "*.log" -mtime +30 -delete', '```',
        '`-mtime +30` 是修改时间超过 30 天。先用 `-print` 看清单，确认无误再换 `-delete`。',
    ]),
     ('二、按大小找占空间的文件', [
        '```', 'find / -xdev -type f -size +500M -exec ls -lh {} \\; | head', '```',
        '`-xdev` 不跨分区，避免扫到挂载的网络盘或容器层。',
    ]),
     ('三、按权限找危险文件', [
        '```', 'find /var/www -perm -o+w -type f', '```',
        '任何用户可写的站点文件都是潜在入口，定期扫一遍。',
    ]),
     ('四、批量执行的安全写法', [
        '`-exec cmd {} \\;` 每个文件起一次进程，慢；`-exec cmd {} +` 批量传参，快很多。文件名含空格时用 `-print0 | xargs -0`。',
    ]),
     ('五、排除目录', [
        '```', 'find . -path ./node_modules -prune -o -name "*.ts" -print', '```',
        '`-prune` 是 find 里少数需要固定搭配的写法，记下来就行。',
    ])],
    'post-4.svg', '2026-10-22T11:00:00'))

P.append(make_post(34, 'sed 常用改写十条', 'sed-usage', '系统运维', ['命令行', '文本处理'],
    '改配置、批量替换、取指定行，sed 比想象中好用。',
    [('一、原地替换', [
        '```', "sed -i 's/old/new/g' config.conf", '```',
        '`-i` 直接改文件。macOS 上要写 `-i ""`，这个差异坑过很多人。',
    ]),
     ('二、只替换第 N 次出现', [
        '```', "sed -i 's/foo/bar/2' file", '```',
    ]),
     ('三、按行范围替换', [
        '```', "sed -i '10,20s/http/https/g' file", '```',
        '范围可以是行号，也可以是 `/开始/,/结束/` 这种模式匹配。',
    ]),
     ('四、删除空行与注释', [
        '```', "sed -i '/^$/d; /^#/d' file", '```',
    ]),
     ('五、注意特殊字符', [
        '替换内容里有 `/` 时，换个分隔符更省事：`sed -i "s|/old/path|/new/path|g"`。',
        '变量展开要用双引号，否则 `$` 会被 sed 当特殊符号。',
    ])],
    'post-5.svg', '2026-10-21T16:45:00'))

P.append(make_post(35, 'awk 按列统计：日志分析的入门利器', 'awk-usage', '系统运维', ['命令行', '日志'],
    '不用写脚本，一行 awk 就能算出访问量 Top 10。',
    [('一、统计 IP 访问次数', [
        '```', "awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -10", '```',
        '`$1` 是第一列。配合管道就是完整的统计流水线。',
    ]),
     ('二、按状态码统计', [
        '```', 'awk \'{print $9}\' access.log | sort | uniq -c | sort -rn', '```',
        'nginx 默认格式里第 9 列是状态码，一眼看出 5xx 占比。',
    ]),
     ('三、条件过滤', [
        '```', "awk '$9 >= 500 {print $1, $7}' access.log | head", '```',
    ]),
     ('四、求和与平均', [
        '```', "awk '{sum += $10; n++} END {printf \"总流量 %.1f MB\\n\", sum/1024/1024}' access.log", '```',
        '`END` 块在全部行处理完后执行，适合做汇总。',
    ]),
     ('五、按小时聚合', [
        '```', 'awk \'{print substr($4, 2, 14)}\' access.log | uniq -c', '```',
        '日志按时间有序时，`uniq -c` 直接就能出每小时的量。',
    ])],
    'post-6.svg', '2026-10-21T09:30:00'))

P.append(make_post(36, 'grep 与 ripgrep：搜索代码该用哪个', 'grep-rg', '系统运维', ['命令行', '搜索'],
    '项目里搜代码，rg 比 grep 快一个数量级，但有几点要注意。',
    [('一、默认行为差异', [
        'rg 默认递归、遵守 `.gitignore`、跳过二进制文件，还会按行号着色。这些默认值恰好符合「在项目里搜代码」的场景。',
        'grep 想达到同样效果要写一长串参数，还不一定记得全。',
    ]),
     ('二、常用组合', [
        '```', 'rg -n "TODO" src/', 'rg -l "oldFunction" ', 'rg -i -t py "import requests"', '```',
        '`-n` 行号、`-l` 只列文件、`-t` 按文件类型。',
    ]),
     ('三、什么时候还是用 grep', [
        '- 搜索 `/proc`、`/sys` 这种非普通文件',
        '- 需要搜被 gitignore 的构建产物：`rg -uu`',
        '- 目标机器上没装 rg，别为了搜索去装东西',
    ]),
     ('四、性能差在哪', [
        'rg 默认多线程，并且先用正则引擎的字面量前缀做预筛。全仓库搜索时差距非常明显。',
    ])],
    'post-7.svg', '2026-10-20T21:10:00'))

P.append(make_post(37, 'tmux 保持会话：断线不丢任务', 'tmux', '系统运维', ['命令行', '效率'],
    '跑长任务时 SSH 断了怎么办？tmux 是最低成本的保险。',
    [('一、会话操作', [
        '```', 'tmux new -s work', 'tmux ls', 'tmux attach -t work', '```',
        '`Ctrl+b d` 脱离，进程继续跑。',
    ]),
     ('二、分屏', [
        '`Ctrl+b %` 竖分，`Ctrl+b "` 横分，`Ctrl+b 方向键` 切换。看日志同时改配置时特别顺手。',
    ]),
     ('三、复制模式', [
        '`Ctrl+b [` 进入，用方向键或 vi 键位移动，`空格` 开始选择，`回车` 复制。要跟系统剪贴板打通需要在配置里开启。',
    ]),
     ('四、最低配置建议', [
        '```', 'set -g mouse on', 'set -g history-limit 10000', '```',
        '开鼠标能直接滚屏和选窗格，history-limit 默认只有 2000 行，日志很容易被冲掉。',
    ])],
    'post-8.svg', '2026-10-20T10:20:00'))

P.append(make_post(38, '环境变量到底从哪加载的', 'env-profile', '系统运维', ['shell', '基础'],
    '「明明加了 PATH 却不生效」几乎都和加载顺序有关。',
    [('一、加载顺序', [
        '- 登录 shell：`/etc/profile` → `/etc/profile.d/*.sh` → `~/.bash_profile` → `~/.bashrc`',
        '- 交互式非登录 shell（新开终端）：只读 `~/.bashrc`',
        '- 非交互式（脚本、ssh 远程执行命令）：只读 `BASH_ENV`，通常什么都不读',
    ]),
     ('二、最常见的坑', [
        '把 PATH 追加写在 `~/.bashrc` 里，然后 `ssh host "command"` 找不到命令——因为非交互式不读 bashrc。',
        '解决办法：把环境变量放到 `/etc/profile.d/` 下，或者用 systemd 的 `Environment=`。',
    ]),
     ('三、PATH 追加的正确姿势', [
        '```', 'export PATH="$PATH:/opt/bin"', '```',
        '别写成 `PATH=/opt/bin`，那会覆盖掉系统路径，很多命令就找不到了。',
    ]),
     ('四、诊断', [
        '```', 'echo $PATH', 'bash -lc "echo $PATH"', '```',
        '对比登录式和非登录式的结果，能立刻定位到底哪一层没生效。',
    ])],
    'post-9.svg', '2026-10-19T18:00:00'))

P.append(make_post(39, '时区设错导致的时间错乱', 'timezone-ntp', '系统运维', ['时间', '排错'],
    '日志时间差 8 小时，或者证书莫名过期，先看时区。',
    [('一、检查三处', [
        '```', 'timedatectl', 'date', 'date -u', '```',
        '`timedatectl` 会同时显示本地时间、UTC 时间、时区设置和 NTP 同步状态。',
    ]),
     ('二、设置北京时间', [
        '```', 'sudo timedatectl set-timezone Asia/Shanghai', '```',
        '容器里没 systemd 时，直接设 `TZ=Asia/Shanghai` 环境变量，或者挂载 `/etc/localtime`。',
    ]),
     ('三、NTP 没同步的表现', [
        '`System clock synchronized: no` 说明没对上。虚拟机挂起恢复后时间漂移很常见，装 `chrony` 或 `systemd-timesyncd` 并确认服务在跑。',
        '```', 'chronyc sources -v', '```',
    ]),
     ('四、为什么这事要紧', [
        '- 日志跨机器对比会完全错位',
        '- TLS 证书校验依赖时间，差得多了直接握手失败',
        '- 分布式任务调度会出现重复执行或漏执行',
    ])],
    'post-10.svg', '2026-10-19T09:15:00'))

P.append(make_post(40, '新服务器上线前的安全检查清单', 'security-baseline', '系统运维', ['安全', '清单'],
    '机器开出来到对外服务之间，这十项建议逐条过一遍。',
    [('一、账号与登录', [
        '- 禁用 root 直接登录：`PermitRootLogin no`',
        '- 改 SSH 端口意义有限，但能减少日志噪音',
        '- 用密钥登录，关掉 `PasswordAuthentication`',
        '- 建个人账号 + sudo 规则，别所有人共用 root',
    ]),
     ('二、网络暴露面', [
        '```', 'ss -lntp', '```',
        '把监听端口挨个确认一遍，不认识的要么关掉要么查清楚。数据库、Redis 这类默认只监听 127.0.0.1。',
        '云上还要看安全组，别出现 `0.0.0.0/0` 全放通。',
    ]),
     ('三、更新与补丁', [
        '```', 'apt list --upgradable', '```',
        '至少把安全更新装上。生产机器建议开 `unattended-upgrades` 只自动装安全补丁。',
    ]),
     ('四、审计与备份', [
        '- 确认日志在写、能轮转、有人看',
        '- 备份任务真的跑成功过（不是配了就算）',
        '- 记录这台机器是干什么的、谁负责',
    ])],
    'post-1.svg', '2026-10-18T20:40:00'))

json.dump(P, open('p1.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('生成', len(P), '篇')
