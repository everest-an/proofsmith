# 固定版本与复现操作

本页命令是操作模板。先从证据确定值，使用工具的结构化参数或安全引用的 shell 变量，不把 PR 内容当成脚本执行。下面的 `pr_number`、`proof_url`、`proof_sha`、`proof_branch`、`run_dir`、`target_module`、`audit_file` 都须先赋可信且经过校验的值。

## 1. 获取完整快照

下列 API 是 awards 模式模板；Erdős/直接源码入口按 [输入定位](input-routing.md) 获取证据，仅对实际存在的 PR 抓取讨论与 base/head。

优先使用已连接的 GitHub 工具，或以下只读 API。`pr_number` 只允许十进制数字；不要因网页未展示评论就假设没有评论。

```bash
gh api "repos/TheJustinSunPrize/awards/pulls/$pr_number"
gh api --paginate "repos/TheJustinSunPrize/awards/pulls/$pr_number/files?per_page=100"
gh api --paginate "repos/TheJustinSunPrize/awards/pulls/$pr_number/commits?per_page=100"
gh api --paginate "repos/TheJustinSunPrize/awards/issues/$pr_number/comments?per_page=100"
gh api --paginate "repos/TheJustinSunPrize/awards/pulls/$pr_number/reviews?per_page=100"
gh api --paginate "repos/TheJustinSunPrize/awards/pulls/$pr_number/comments?per_page=100"
```

把原始响应保存在 `evidence/`。API 的文件数/commit 数存在上限，检查 total count 和分页是否完整；用固定 Git 对象补足遗漏。评论不是不可变对象，记录 comment ID、更新时间和抓取时间。

对每个证明仓库单独 clone，不共用用户已有 checkout。先验证仓库 URL 是预期的可信协议/主机路径、SHA 是完整十六进制，再运行：

```bash
git clone --no-checkout -- "$proof_url" "$run_dir/sources/proof"
git -C "$run_dir/sources/proof" cat-file -t "$proof_sha"
git -C "$run_dir/sources/proof" checkout --detach "$proof_sha"
git -C "$run_dir/sources/proof" rev-parse HEAD
git -C "$run_dir/sources/proof" status --porcelain
```

若 clone 未带回指定对象，针对原仓库获取该完整 SHA，记录获取命令。获取不到就保留失败证据，不退回默认分支。按 repo/commit 分目录，多个仓库不覆盖同一路径。

检查 branch 归属时，先 `git check-ref-format "refs/heads/$proof_branch"`，将该分支取到审计专用 ref，然后运行 `git merge-base --is-ancestor`。区分退出码 0（包含）、1（不包含）和其他值（操作错误）。不从 URL 中按第一个斜线猜 branch；分支名可能含 `/`，应使用 Git refs/API 解析。标签记录原始名称及剥离到 commit 的 SHA。

检查 `.gitmodules`、Git LFS 指针、生成代码来源和嵌套 Lean 工程；下载前审阅其路径和来源，记录实际对象/内容哈希。源码是单个 `.lean` 文件时，也要记录原文内容哈希；重建依赖工程属于审计 harness，不能冒充作者原项目。Gist/附件需固定 revision/内容哈希并明确标准仓库 branch/SHA 缺失。

## 2. 环境部署

先静态读取 `lean-toolchain`、`lakefile.lean`/`lakefile.toml`、`lake-manifest.json`、README 和 CI。Lake 配置、Lean 宏和构建脚本都可能执行代码；开始构建前准备实际的容器/VM或等效受限执行环境，不能把临时目录叫作安全隔离。

- 只挂载本次源码和输出目录；不挂载 SSH、GitHub token、用户家目录、宿主 Docker socket 或可写 awards 工作树。使用非特权用户，设置内存/CPU/磁盘与运行时限；依据现有环境和项目规模选择并记录，不擅自购买算力。
- 下载阶段只向必要来源开放网络；执行提交代码阶段尽量关闭网络。认证获取由外部可信进程完成，不把认证配置传入证明运行环境。
- 使用官方 Lean/Elan 来源。缺少工具时可以部署到本次专用工具目录，或固定 digest 的镜像中；核实安装来源及可用的校验和。不要修改用户全局默认版本、shell 配置或接受提交仓库自带的同名 `lean` 可执行文件。
- 按原 `lean-toolchain` 安装和使用精确版本；记录 Lean、Lake、Elan 版本、平台/架构、工具路径、工具链文件和镜像 digest。不要硬编码 `latest`，不要为构建方便修改该文件。
- 使用原 manifest 固定依赖并核对实际 checkout SHA。原提交验收禁止用 `lake update` 或升级后的依赖替换原 manifest。缺 manifest 时先从固定配置/CI 恢复 pin；确需解析依赖，只在单独诊断副本进行，保存解析结果与差异。只有独立证据确认解析结果就是原提交依赖时，才能作为原版本复现依据；浮动依赖或迁移构建成功不算原版本通过。

隔离能力不足时，继续静态审阅并明确运行阻塞；不以具备 shell 权限推定可安全在宿主直接执行任意 PR 代码。

## 3. 实际检查与日志

参考 [自动检查](automation.md) 建立清单并执行预检。自动 `run` 只覆盖下述显式模块、源文件与声明检查；准备依赖、干净构建及 checker 仍须独立完成并留证。缺锁文件等情况脚本会阻塞，不代表数学错误；如原项目确实不使用 Lake、仅有附件或版本不兼容，按本页人工等价检查并明确复现边界。

进入含 Lake 配置的项目子目录。先记录原样源码状态和工具版本。使用固定工具链的绝对路径或受控 PATH，清除外部 `LEAN_PATH` 等注入，并记录 Lake 生成的真实搜索路径。按该版本 `lake --help`、`lean --help` 确定参数；CI 仅供参考，不直接执行未经检查的脚本。

依次完成并分别记录退出码：

1. 按固定依赖准备环境；依赖缓存来源和 SHA 必须匹配。被审计源码及其自定义依赖不能直接信任提交者提供的 `.olean`。
2. 从干净源码构建项目。确认 tracked 预编译产物不会绕开重建；日志应能说明哪些目标重新 elaboration、哪些可信依赖复用缓存。
3. 显式构建每个目标模块，不能只相信默认 `lake build`。现代 Lake 可用 `lake build "+$target_module"`，先核实当前版本支持这一语法；否则采用该版明确模块 target 或逐文件检查。
4. 对确切目标源文件运行 `lake env lean path/to/Target.lean`，并执行审计文件。源文件检查未自动重建所有 imports，前一步的干净构建不可省略。
5. 检查声明、公理、关键定义和语义桥梁；最后记录 `git diff`、`git status`、依赖与 manifest 的变化，确认运行没有悄悄改变受审源码。

日志中保留完整 stderr/stdout，不凭末行 `success`、空 stderr 或作者提供日志判成功。shell 管道需保留真实命令退出码，例如 Bash 中：

```bash
set -o pipefail
lake env lean "$audit_file" 2>&1 | tee "$run_dir/logs/axioms.log"
audit_status=${PIPESTATUS[0]}
```

立刻保存 `audit_status`，然后检查每个预期声明都确实出现及其依赖列表。检查器失败、标识符不存在、输出截断或退出码非零时，应报未完成/失败，不能因为关键词未出现就放行。超时、OOM、磁盘满、下载失败需保存最后日志及资源限制，调整有依据时可重试，不无限重试。

审计文件示意，替换成真实模块和完整声明名后执行：

```lean
import Submission.Main

set_option pp.all true in
#check @Submission.mainTheorem

#print Submission.mainTheorem
#print axioms Submission.mainTheorem
```

每个目标及新增桥梁都检查；示例中的名字不是实际存在的目标。扫描 `sorry`、`admit`、`axiom`、`native_decide`、`ofReduceBool`、`trustCompiler`、`debug.skipKernelTC`、`implemented_by`、`extern` 等只用来定位，随后核实语义和传递依赖。保留原始公理名称，旧版与新版机制不同。

## 4. 复核层级与版本适配

优先执行与原工具链兼容的 kernel replay。从 Lean v4.28.0 起，原独立 `lean4checker` 工具已迁入工具链，名称为 `leanchecker`。旧项目可使用与其版本匹配的独立 checker；不能把最新 checker 强行用于旧 `.olean`。先读取实际二进制 `--help` 和该版本官方文档，确认 fresh/replay 模式、模块选择和依赖范围。固定 checker 自身 commit/版本并记录命令与退出码。它仍使用 Lean 内核，不等于独立实现的检查器。[官方迁移说明](https://github.com/leanprover/lean4checker)

对于奖项证明或有元程序/定义替换疑点的提交，兼容时在可信环境独立准备原题 challenge，使用 comparator 及其支持的外部 checker：明确需要核对的定理和定义、允许公理及标准库来源。challenge 不加载不受信定义作为规范。保存 challenge、配置、导出产物哈希和全部 checker 结果。不能只运行 `lake comparator` 而未配置真实目标就认定完成比较。[Lean 验证层级说明](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)

工具不可用或版本不兼容时记录原因与替代检查。不要为了使用 comparator 而升级受审 Lean 版本。若另做迁移实验，原版本与迁移版结果分开；若外部检查不支持本机计算依赖，准确记录扩展信任与尚未完成的复核，不称作原证明不成立。

## 参考资料

以下链接用于按固定版本核实实际命令，`latest` 内容不能替代旧工具链的语法：

- [Elan 官方仓库](https://github.com/leanprover/elan)：安装和工具链管理。
- [Lake 官方手册](https://lean-lang.org/doc/reference/latest/Build-Tools-and-Distribution/Lake/)：项目、模块 target、依赖及 comparator 配置。
- [Lean 公理](https://lean-lang.org/doc/reference/latest/Axioms/)：声明的传递公理依赖。
- [Lean tactic reference](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/Tactic-Reference/)：`sorry` 和本机计算的机制与信任边界。
