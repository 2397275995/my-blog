import json
import sys

sys.path.insert(0, '.')
from helper import make_post

P = []

P.append(make_post(61, 'Docker 镜像从 1.2G 瘦到 180M', 'docker-slim', '虚拟化', ['docker', '镜像'],
    '镜像大不只是传输慢，构建缓存和攻击面也跟着变大。',
    [('一、先看谁占的空间', [
        '```', 'docker history --no-trunc myimage:v1 | head -20', '```',
        '找到体积最大的那几层。通常是基础镜像、包管理器缓存、构建中间产物。',
    ]),
     ('二、三条最有效的办法', [
        '- 换更小的基础镜像：`node:20` → `node:20-alpine`，`ubuntu` → `debian-slim`',
        '- 多阶段构建：构建依赖留在 builder 阶段，最终镜像只拷贝产物',
        '- 合并且清理：`apt-get update && apt-get install -y ... && rm -rf /var/lib/apt/lists/*` 写在同一层',
    ]),
     ('三、多阶段构建示例', [
        '```', 'FROM node:20 AS build', 'WORKDIR /app', 'COPY package*.json ./', 'RUN npm ci', 'COPY . .', 'RUN npm run build', '', 'FROM nginx:alpine', 'COPY --from=build /app/dist /usr/share/nginx/html', '```',
        '最终镜像里没有 node_modules，也没有源码。',
    ]),
     ('四、注意', [
        'alpine 用的是 musl libc，个别二进制（老版本 glibc 依赖、某些 Python 包）会跑不起来。遇到诡异报错先换回 `-slim` 版本。',
    ])],
    'post-11.svg'))

P.append(make_post(62, 'Compose 编排：把一堆 docker run 收成一个文件', 'compose', '虚拟化', ['docker', '编排'],
    '参数记不住就写进 compose.yml，还能纳入版本管理。',
    [('一、最小可用示例', [
        '```', 'services:', '  app:', '    image: myapp:latest', '    ports: ["8080:8080"]', '    environment:', '      TZ: Asia/Shanghai', '    restart: unless-stopped', '    depends_on: [db]', '  db:', '    image: postgres:16-alpine', '    volumes: ["pgdata:/var/lib/postgresql/data"]', 'volumes:', '  pgdata:', '```',
    ]),
     ('二、几个容易踩的点', [
        '- `depends_on` 只保证启动顺序，不保证服务就绪。要等就写 healthcheck',
        '- 容器里的 `localhost` 指容器自己，连别的服务用服务名',
        '- 环境变量写在 `.env` 里，别直接提交密码',
    ]),
     ('三、健康检查', [
        '```', 'healthcheck:', '  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]', '  interval: 10s', '  retries: 3', '```',
    ]),
     ('四、日常命令', [
        '```', 'docker compose up -d', 'docker compose logs -f app', 'docker compose down          # 保留数据卷', 'docker compose down -v       # 连数据一起删，慎用', '```',
    ])],
    'post-12.svg'))

P.append(make_post(63, 'Docker 网络模式：bridge、host 与自定义网络', 'docker-network', '虚拟化', ['docker', '网络'],
    '容器连不上外网、或者容器之间无法解析名字，基本都是网络模式选错了。',
    [('一、三种常用模式', [
        '- `bridge`（默认）：容器有独立 IP，通过 NAT 出网，端口要映射',
        '- `host`：直接用宿主机网络栈，没有端口映射，性能最好但会抢占宿主端口',
        '- `none`：只有 loopback，用于完全隔离的场景',
    ]),
     ('二、容器之间怎么互相访问', [
        '同一个自定义网络里的容器可以用服务名互相解析：',
        '```', 'docker network create app-net', 'docker run -d --name db --network app-net postgres:16', 'docker run -d --name app --network app-net myapp', '```',
        '此时 app 里连 `db:5432` 就能通。用默认 bridge 网络则不支持名字解析，只能靠 IP，这是很多人「连不上」的根源。',
    ]),
     ('三、排查', [
        '```', 'docker network ls', 'docker inspect app --format "{{json .NetworkSettings.Networks}}"', '```',
        '先确认两个容器是不是在同一个网络里。',
    ]),
     ('四、host 模式的取舍', [
        '省掉一层 NAT，延迟低一点，适合高性能代理或监控 agent。代价是端口冲突和隔离性下降，日常业务还是用 bridge。',
    ])],
    'post-13.svg'))

P.append(make_post(64, '容器数据卷：备份与迁移', 'docker-volume', '虚拟化', ['docker', '备份'],
    '容器随时可以删，数据不能。',
    [('一、为什么用卷而不是绑定目录', [
        '绑定宿主目录（`-v /data:/app/data`）简单直观，但权限、SELinux、路径依赖都会带来问题。命名卷由 Docker 管理，跨平台一致。',
    ]),
     ('二、备份命名卷', [
        '起一个临时容器，把卷挂进去打包：',
        '```', 'docker run --rm -v pgdata:/data -v $(pwd):/backup alpine \\', '  tar -czf /backup/pgdata.tar.gz -C /data .', '```',
    ]),
     ('三、恢复', [
        '```', 'docker run --rm -v pgdata:/data -v $(pwd):/backup alpine \\', '  sh -c "rm -rf /data/* && tar -xzf /backup/pgdata.tar.gz -C /data"', '```',
        '顺序很关键：先清空再解压，否则会留下旧文件。',
    ]),
     ('四、数据库别用冷备', [
        '直接打包正在运行的数据库卷，可能拿到写入一半的文件。要么停服务再备份，要么用 `pg_dump` 这类逻辑备份。',
    ])],
    'post-14.svg'))

P.append(make_post(65, 'WSL2 日常使用：把它当一台 Linux 用', 'wsl2', '虚拟化', ['Windows', 'Linux'],
    '路径、网络、文件性能，三个地方想清楚就顺手了。',
    [('一、文件放哪', [
        '项目代码放 Linux 侧（`~/code`），不要放 `/mnt/c/...`。跨文件系统的 IO 慢十倍以上，`npm install` 的差距非常明显。',
        'Windows 侧要访问 Linux 文件，用 `\\\\wsl$\\` 路径。',
    ]),
     ('二、网络', [
        'WSL2 默认 NAT，Windows 访问 Linux 服务用 `localhost` 就行。反过来 Linux 访问 Windows 服务则要用宿主 IP。',
        '最近版本支持 `networkingMode=mirrored`，镜像宿主网络，端口互通更简单。',
    ]),
     ('三、systemd', [
        '较新版本在 `/etc/wsl.conf` 里加：',
        '```', '[boot]', 'systemd=true', '```',
        '然后 `wsl --shutdown` 重启。有了 systemd，装服务、用 `systemctl` 都跟真机一致。',
    ]),
     ('四、和 Docker 的关系', [
        'Docker Desktop 会在 WSL 里起一个发行版来跑引擎。如果只用命令行，直接装 Docker Engine 到 WSL 里更轻。',
    ])],
    'post-15.svg'))

P.append(make_post(66, 'KVM 快速上手：命令行起一台虚拟机', 'kvm', '虚拟化', ['KVM', 'Linux'],
    '不想装 VMware，Linux 主机上 KVM 是最原生的选择。',
    [('一、检查支持', [
        '```', 'egrep -c "(vmx|svm)" /proc/cpuinfo', 'lsmod | grep kvm', '```',
        '非 0 且有 kvm 模块，就能用。',
    ]),
     ('二、安装', [
        '```', 'sudo apt install -y qemu-kvm libvirt-daemon-system virtinst bridge-utils', 'sudo systemctl enable --now libvirtd', '```',
    ]),
     ('三、建一台', [
        '```', 'sudo virt-install --name test01 --ram 2048 --vcpus 2 \\', '  --disk path=/var/lib/libvirt/images/test01.qcow2,size=20 \\', '  --cdrom /data/ubuntu-26.04-live-server-amd64.iso \\', '  --network network=default --graphics none --console pty,target_type=serial', '```',
        '没有图形界面时用 `--graphics none` 配合串口控制台安装，全程在终端里完成。',
    ]),
     ('四、管理', [
        '```', 'virsh list --all', 'virsh console test01', 'virsh snapshot-create-as test01 clean', '```',
    ]),
     ('五、网络', [
        '默认网络是 NAT（virbr0）。要桥接就把物理网卡加入 br0，虚拟机直接拿局域网 IP，配置稍麻烦但更接近真机。',
    ])],
    'post-16.svg'))

P.append(make_post(67, '快照不是备份：什么时候该克隆', 'snapshot-strategy', '虚拟化', ['虚拟化', '备份'],
    '快照存在同一块磁盘上，磁盘坏了快照一起没。',
    [('一、快照的本质', [
        '快照记录的是「某个时间点的磁盘状态差异」。它依赖原始磁盘，不能脱离原盘独立存在。',
        '所以：快照适合「改之前留个后悔药」，不适合「防硬件故障」。',
    ]),
     ('二、什么时候拍快照', [
        '- 升级系统、改内核参数前',
        '- 装不熟悉的软件前',
        '- 做实验、练习编译前',
        '一个建议：装完系统配好网络和 SSH，先拍一个叫「干净系统」的快照，之后所有实验都从它分叉。',
    ]),
     ('三、快照链别太长', [
        '快照越多，写放大越严重，性能越差。做完实验记得合并（`virsh snapshot-delete --children` 或 VMware 的「整合」）。',
    ]),
     ('四、克隆补上备份缺口', [
        '完整克隆是独立副本，可以放到另一块盘甚至另一台机器，这才算备份。链接克隆省空间但依赖父盘，父盘没了它也废了。',
        '克隆后记得改 machine-id 和主机名，否则多台机器的 IP、日志标识会打架。',
    ])],
    'post-17.svg'))

P.append(make_post(68, '虚拟机磁盘扩容：从宿主机到文件系统', 'disk-expand', '虚拟化', ['虚拟化', '磁盘'],
    '三步走：扩虚拟盘、扩分区、扩文件系统。少一步都白做。',
    [('一、先扩虚拟磁盘', [
        '关机或确认支持在线扩容后，在虚拟化平台里把磁盘容量调大。这一步只改了「虚拟盘的上限」，系统里还看不到。',
        '```', 'qemu-img resize test01.qcow2 +20G', '```',
    ]),
     ('二、扩分区', [
        '```', 'lsblk', 'growpart /dev/sda 3', '```',
        '`growpart` 能在线扩分区，不需要重启。分区号要对着 `lsblk` 的输出填。',
    ]),
     ('三、扩逻辑卷（用了 LVM 的话）', [
        '```', 'pvresize /dev/sda3', 'lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv', 'resize2fs /dev/ubuntu-vg/ubuntu-lv', '```',
        '最后一步按文件系统类型换：xfs 用 `xfs_growfs`。',
    ]),
     ('四、顺序不能乱', [
        '跳过 LVM 直接 `resize2fs` 会报「nothing to do」。文件系统只能在自己的逻辑卷范围内扩展，上一步没做完它就没空间可长。',
    ])],
    'post-18.svg'))

P.append(make_post(69, 'NAT、桥接、仅主机：三种网络模式怎么选', 'vm-network', '虚拟化', ['虚拟化', '网络'],
    '装虚拟机第一步就选网络，选错了后面 SSH 怎么都连不上。',
    [('一、三种模式的实际效果', [
        '- NAT：虚拟机借宿主机上网，外网连不进来，宿主机能主动连。最省事',
        '- 桥接：虚拟机像局域网里一台独立机器，路由器给它单独分 IP，别的设备能访问',
        '- 仅主机：只能和宿主机通信，完全隔离',
    ]),
     ('二、怎么选', [
        '- 学 Linux、跑一般服务 → NAT',
        '- 需要手机或其他电脑访问（做网站预览、搭测试服务）→ 桥接',
        '- 做安全实验、跑可疑程序 → 仅主机',
    ]),
     ('三、NAT 下宿主机怎么找到虚拟机 IP', [
        '在虚拟机里 `ip -br a` 看地址，通常是 `192.168.x.128` 起。想固定就改 netplan 配置，别依赖 DHCP。',
    ]),
     ('四、桥接连不上的排查', [
        '- 确认物理网卡支持桥接（无线网卡经常不行）',
        '- 检查宿主机防火墙是否放行',
        '- 公司网络可能有端口安全或 MAC 限制，桥接会被直接丢弃',
    ])],
    'post-19.svg'))

P.append(make_post(70, 'LXC 与 Docker：都叫容器，定位不同', 'lxc-vs-docker', '虚拟化', ['容器', 'Linux'],
    '想要一个「轻量虚拟机」还是「跑一个应用」，答案不同。',
    [('一、本质区别', [
        '- LXC/LXD 偏向「系统容器」：里面有完整的 init、systemd、多个服务，像一台轻量虚拟机',
        '- Docker 偏向「应用容器」：一个容器跑一个进程，生命周期跟着应用走',
    ]),
     ('二、启动方式差异', [
        'LXC 里你会 `systemctl start nginx`；Docker 里你不会在容器里跑 systemd，而是直接把 nginx 作为主进程。',
        '这也是为什么 Docker 容器通常不应该装一堆服务——它不擅长模拟完整系统。',
    ]),
     ('三、什么时候选 LXC', [
        '- 需要一台「隔离但轻量」的机器跑老旧应用',
        '- 想要接近虚拟机的使用体验但省内存',
        '- 做多用户隔离环境（每人数一个容器）',
    ]),
     ('四、什么时候选 Docker', [
        '- 应用交付、CI 构建、微服务',
        '- 需要镜像分发和版本管理',
        '- 需要和编排系统（compose、k8s）配合',
    ])],
    'post-20.svg'))

P.append(make_post(71, 'Vagrant：一条命令拉起可复现的实验环境', 'vagrant', '虚拟化', ['虚拟化', '自动化'],
    '折腾环境最怕「我这能跑」，Vagrant 用配置文件把环境写死。',
    [('一、Vagrantfile 示例', [
        '```', 'Vagrant.configure("2") do |config|', '  config.vm.box = "ubuntu/jammy64"', '  config.vm.network "private_network", ip: "192.168.56.10"', '  config.vm.provider "virtualbox" do |vb|', '    vb.memory = 2048', '    vb.cpus = 2', '  end', '  config.vm.provision "shell", inline: <<-SHELL', '    apt-get update && apt-get install -y nginx', '  SHELL', 'end', '```',
    ]),
     ('二、常用命令', [
        '```', 'vagrant up', 'vagrant ssh', 'vagrant halt', 'vagrant destroy -f', '```',
        '`destroy` 之后 `up` 还能得到一模一样的环境，全靠那个配置文件和 box。',
    ]),
     ('三、适合的场景', [
        '- 教别人搭环境，直接给仓库，不用写文档',
        '- 一次性的实验（学 K8s、练 Ansible）',
        '- 多人协作时保证基础环境一致',
    ]),
     ('四、成本', [
        '每个项目一个虚拟机，内存开销大。本地机器 16G 以下建议一次只开一个。',
    ])],
    'post-1.svg'))

P.append(make_post(72, '云服务器选型：先看瓶颈在哪', 'cloud-vm-sizing', '虚拟化', ['云服务器', '选型'],
    'CPU 核数不是唯一指标，很多业务瓶颈根本不在 CPU。',
    [('一、按业务类型挑', [
        '- 静态站点、小 API：1 核 2G 足够，重点看带宽',
        '- 数据库：内存优先，IO 次之，CPU 反而次要',
        '- 编译、转码：CPU 核数和大内存，注意突发型实例有积分限制',
        '- 长连接网关：看网络带宽和连接数上限，不是核数',
    ]),
     ('二、突发性能实例要小心', [
        '便宜机型常是「积分制」：平时低负载攒积分，跑满后会被限速到很低。适合养站，不适合跑批处理。',
        '看监控里的 CPU 积分余额，别等业务高峰期才发现被限。',
    ]),
     ('三、带宽怎么估', [
        '1 Mbps 约等于 128 KB/s。一个 2MB 的页面，1 Mbps 带宽下一个用户要 16 秒。图片多的站点，带宽是第一个瓶颈。',
        '静态资源上 CDN，比升带宽便宜得多。',
    ]),
     ('四、先小后大', [
        '云主机可以随时升配。按最小可用规格起步，用监控数据说话，比一次性买大更划算。',
    ])],
    'post-2.svg'))

P.append(make_post(73, '容器资源限制：别让一个容器拖垮整台机器', 'container-limits', '虚拟化', ['docker', '资源'],
    '不设限制的容器会吃掉宿主机所有内存，然后被 OOM 一起带走。',
    [('一、限制 CPU 与内存', [
        '```', 'docker run -d --cpus="1.5" --memory="1g" --memory-swap="1g" myapp', '```',
        '`--memory-swap` 等于 `--memory` 表示禁用 swap，容器超限直接被 kill，行为可预测。',
    ]),
     ('二、compose 里写', [
        '```', 'deploy:', '  resources:', '    limits:', '      cpus: "1.5"', '      memory: 1g', '```',
        '注意 `deploy` 段在 `docker compose up` 下也生效（早期版本只认 swarm，现在没问题）。',
    ]),
     ('三、查看实际用量', [
        '```', 'docker stats --no-stream', '```',
        '持续观察一段时间，看峰值而不是瞬时值来定限制。',
    ]),
     ('四、日志也会撑爆磁盘', [
        '```', 'logging:', '  driver: json-file', '  options:', '    max-size: "10m"', '    max-file: "3"', '```',
        '默认不限，一个死循环打日志的容器几小时就能写满磁盘。',
    ])],
    'post-3.svg'))

P.append(make_post(74, '用三台虚拟机搭一套集群实验环境', 'lab-multi-vm', '虚拟化', ['虚拟化', '集群'],
    '学 K8s、练 Ansible、试负载均衡，一台机器不够用。',
    [('一、资源规划', [
        '- 宿主机 16G：三台各 2C/2G，留 4G 给宿主',
        '- 磁盘：每台 20G，用精简置备（用多少长多少）',
        '- 网络：NAT 模式 + 固定 IP，避免每次开机地址都变',
    ]),
     ('二、先配好一台再克隆', [
        '装完一台、配好 SSH 免密和 hosts 后关机，再克隆两台。比装三次省一多半时间。',
        '克隆后必须改：`machine-id`、主机名、IP。',
        '```', 'sudo rm /etc/machine-id && sudo systemd-machine-id-setup', 'sudo hostnamectl set-hostname node2', '```',
    ]),
     ('三、hosts 统一', [
        '在三台机器的 `/etc/hosts` 里写死名字解析，后面写 Ansible 清单、K8s 配置都直接用人名，不用记 IP。',
    ]),
     ('四、用完就关', [
        '三台一起开着跑一天，笔记本风扇会一直响。实验完 `vagrant halt` 或关机，需要时再开。',
    ])],
    'post-4.svg'))

P.append(make_post(75, '虚拟化性能调优：几个真正见效的设置', 'virt-perf', '虚拟化', ['虚拟化', '性能'],
    '先确认瓶颈，再改设置。盲目开「性能优化」往往更慢。',
    [('一、先量再调', [
        '在虚拟机里跑基准（`fio` 测磁盘、`iperf3` 测网络、`sysbench` 测 CPU），和宿主机对比。差距在哪就调哪里。',
    ]),
     ('二、磁盘', [
        '- 用 virtio 而不是 IDE/SATA',
        '- 缓存模式：`none`（直通）适合数据库，`writeback` 适合一般场景',
        '- 预分配磁盘（`--prealloc-metadata`）能减少碎片',
    ]),
     ('三、CPU', [
        '- 开 `host-passthrough` 让虚拟机看到真实 CPU 特性，避免某些指令集缺失导致的性能断崖',
        '- vCPU 别超过物理核数，超了会互相抢',
    ]),
     ('四、网络', [
        'virtio-net + 多队列能明显提升吞吐。桥接比 NAT 少一层转发，延迟更低。',
    ]),
     ('五、别做的优化', [
        '关掉 KSM、关掉 balloon、给虚拟机绑死核心——这些在个人环境里收益很小，反而让内存更紧张。',
    ])],
    'post-5.svg'))

P.append(make_post(76, '技术笔记到底该记什么', 'what-to-note', '随笔', ['笔记', '方法'],
    '把文档抄一遍是最常见的无效努力。',
    [('一、不该记的', [
        '- 官方文档里能直接查到的命令参数',
        '- 一次性问题的临时解法（除非会复发）',
        '- 「今天学了 XX」这种没有结论的流水账',
    ]),
     ('二、该记的三类', [
        '- **踩坑记录**：现象、原因、解法。下次遇到同类问题能秒定位',
        '- **决策依据**：为什么选 A 不选 B，当时权衡了什么。半年后你会感谢自己',
        '- **可复用的做法**：一段能直接粘贴的配置、一个检查清单',
    ]),
     ('三、判据', [
        '写完问自己：三个月后我会翻它吗？如果答案是「不会」，那就别写。',
        '笔记的价值不在数量，在于下一次能省多少时间。',
    ]),
     ('四、格式建议', [
        '标题用结论，正文先写「现象/问题」，再写「原因」，最后「怎么做」。这个顺序对未来的你最有帮助——因为搜索的时候你只记得现象。',
    ])],
    'post-6.svg'))

P.append(make_post(77, '故障复盘怎么写才有用', 'postmortem', '随笔', ['复盘', '方法'],
    '复盘的目的不是追责，是让同样的事不再发生。',
    [('一、结构', [
        '- 时间线：几点几分发生了什么，谁做了什么',
        '- 影响面：谁受影响、多久、损失多少',
        '- 根因：技术上的直接原因，以及为什么没被发现',
        '- 改进项：每条都要有负责人和截止时间',
    ]),
     ('二、别停在「人为失误」', [
        '「某某配置写错了」不是根因。真正要问的是：为什么这个配置能直接生效？为什么没有校验？为什么测试环境没暴露？',
        '把责任归到个人，下次只会换个人再犯。',
    ]),
     ('三、改进项要可验证', [
        '「加强培训」不可验证。「给配置加上 schema 校验，非法值直接拒绝加载」可验证。',
    ]),
     ('四、小故障也值得记', [
        '没造成用户影响的险情（near miss）往往暴露同样的系统缺陷，而且没有情绪包袱，更适合拿来改进。',
    ])],
    'post-7.svg'))

P.append(make_post(78, '怎么读官方文档：先看例子再看参数', 'read-docs', '随笔', ['学习', '方法'],
    '几百页的文档不用通读，会查比读完更有用。',
    [('一、顺序', [
        '- 先看「快速开始」，跑通最小例子',
        '- 再看「配置/参数」里你实际用到的部分',
        '- 遇到不懂再翻「概念」章节',
        '倒过来读是最累的方式。',
    ]),
     ('二、善用结构', [
        '好的文档有搜索、有目录、有版本切换。查之前先确认版本——很多坑源于照着新版文档配旧版软件。',
    ]),
     ('三、看不懂时', [
        '- 找该项目的 issue / discussions，别人的困惑往往就是你的困惑',
        '- 看示例仓库比读文字快',
        '- 实在没有再问 AI，但要把版本和环境说清楚',
    ]),
     ('四、记下来的不是文档，是路径', [
        '与其抄一遍参数表，不如记一句「这个参数在某某章节，用来解决某某问题」。下次直接跳过去。',
    ])],
    'post-8.svg'))

P.append(make_post(79, '搜索技巧：用对关键词比换搜索引擎有用', 'search-skills', '随笔', ['搜索', '方法'],
    '搜不到东西，多数时候是问题描述得不对。',
    [('一、把问题变成关键词', [
        '「电脑很卡怎么办」搜不出有用结果。换成具体的报错原文、软件名、版本号，命中率立刻不同。',
        '- 优先搜**完整报错信息**，去掉路径和变量',
        '- 加版本号缩小范围：`vue 3.5 suspense bug`',
        '- 英文搜一遍，很多问题的答案只在英文社区',
    ]),
     ('二、几个实用语法', [
        '- `site:github.com 关键词` 只在某站搜',
        '- `"完整句子"` 精确匹配',
        '- `filetype:pdf` 找文档',
    ]),
     ('三、AI 搜索的用法', [
        '适合「我该怎么做」这类开放问题；不适合查具体参数——它会编。参数类问题一定要回到官方文档确认。',
    ]),
     ('四、别搜显而易见的', [
        '「如何打开终端」这种直接试一下比搜快。判断标准：搜的时间超过自己试的时间，就别搜了。',
    ])],
    'post-9.svg'))

P.append(make_post(80, '信息源要少而准', 'information-diet', '随笔', ['信息', '习惯'],
    '每天读一百条资讯的收益，远低于读三篇能落地的文章。',
    [('一、砍掉噪音', [
        '- 新闻推送、热搜榜：信息密度极低，且容易上瘾',
        '- 收藏夹里存了半年没看的文章：直接删',
        '- 十几个技术群：留两三个真正活跃且聊技术的',
    ]),
     ('二、留下什么', [
        '- 两三个高质量周报/月刊（系统性，不是碎片）',
        '- 官方 changelog（知道你用的东西变了什么）',
        '- 少量真正在做事的人的博客',
    ]),
     ('三、摄入要有出口', [
        '读到的内容如果没有任何输出（笔记、实践、跟人讲），基本等于没读。每周挑一条真正用起来。',
    ]),
     ('四、允许自己不知道', [
        '技术圈每天都有新东西，不追不会死。等你需要用到时再学，效率反而更高。',
    ])],
    'post-10.svg'))

json.dump(P, open('p3.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('生成', len(P), '篇')
