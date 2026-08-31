# 端点发现模式矩阵

> 以下行为实测于 2026-08（Chrome 151，macOS）。Chrome 每 4 周一个大版本，
> 使用前如遇异常请先对照本节，而不是怀疑代码。

## 两种启动模式

| 模式 | `DevToolsActivePort` 文件 | HTTP `/json/version` | 实际连接走 |
| --- | --- | --- | --- |
| 传统模式（`--remote-debugging-port` + 专用 `--user-data-dir`） | **不写**（Chrome 151 实测） | 200 | HTTP 探测 |
| auto-connect（`chrome://inspect` 里的 “Allow remote debugging for this browser instance”，Chrome ≥ 144） | 写（端口 + `/devtools/browser/<UUID>`） | **404** | 文件里的 WS 路径 |

两条发现路径**互不替代**，本 skill 的 `find_endpoint()` 两条都试。

## 关键坑（全部实测踩过）

1. **Chrome 136+ 默认目录禁调**：对默认用户数据目录传
   `--remote-debugging-port` 会被**静默忽略**，端口不开、也不报错。
   必须配合专用 `--user-data-dir`（本 skill 的 `--setup` 自动处理）。

2. **auto-connect 每次连接都要人工点“允许”**：授权不跨连接复用，
   不点则连接挂起（实测 60s/90s）。这就是“无感”目标必须用专用 profile 的原因。

3. **端口冲突不报错**：9222 已被占用时，第二个实例静默退到 IPv6 `[::1]:9222`，
   此时 HTTP 打到 127.0.0.1 可能命中**前一个实例**（返回 404）。
   所以默认端口避开 9222，用 9333。

4. **同一 `--user-data-dir` 同时只能有一个浏览器进程**：目录被占用时再带参数
   启动只会给旧进程开新窗口，**新参数全部被忽略**。排查“参数没生效”先查这条。

5. **文件里的 WS 路径属于写文件的那个实例**：显式端口与文件端口不一致时，
   以显式端口为准、丢弃文件里的路径（否则必然连不上）。

## 本 skill 的发现顺序

```
find_endpoint():
  1. 显式 --port          → HTTP /json/version
  2. 专用目录文件         → WS 探活成功则直连文件路径
  3. 专用目录 HTTP(9333)  → 传统模式（文件不写，只能 HTTP）
  4. 真实目录文件/HTTP    → 兼容用户手动开的 auto-connect
```

## 版本演进提醒

- Chrome 127：Windows App-Bound Encryption（影响磁盘方案，不影响 CDP）；
- Chrome 136：默认目录禁开调试端口；
- Chrome 144+：`chrome://inspect` auto-connect 开关（每次连接需人工确认）；
- Chrome 151（实测基准）：传统模式不再写 `DevToolsActivePort`。

遇到“端口通但握手挂起”时，先判断是否处于 auto-connect 模式：看
`DevToolsActivePort` 是否存在、`/json/version` 是否 404。
