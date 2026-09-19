# 目标清单与自动检查

自动化补充证据，不作最终数学判断。`scripts/audit.py` 使用 Python 3.9+ 标准库；无需安装第三方 Python 包。当前脚本支持 Git+Lake 工程、官方 release/rc 工具链 pin、普通点分 Lean 标识符及已验证的 `#print axioms` 输出格式。版本不兼容、转义标识符或其他工程结构应走人工等价检查并保留缺口，不能把工具限制判成数学错误。

## 1. 建立 targets.json

从 `assets/targets.example.json` 复制到本次审计目录，替换示例值，不执行未填完的模板。一个清单只对应一个工程与 commit；跨仓库、不同版本分别建清单。

| 字段 | 含义 |
| --- | --- |
| `schema_version` | 当前为 1 |
| `project.root` | 已隔离 checkout 的绝对路径；可为仓库中的 Lake 子工程 |
| `project.repository/commit/toolchain` | 来源、完整小写 40 位 SHA、`lean-toolchain` 的精确内容；临时快照性质另在报告说明 |
| `problems[].id/source` | 独立题号/名称标识和原题来源 |
| `requirements[].id/description` | 从原题独立提取的每项要求，ID 在本题内唯一 |
| `requirements[].targets` | 关联目标 ID；没有可检查证明时用空列表并标记 `uncovered` |
| `requirements[].coverage` | `pending/full/partial/uncovered`；这是人工语义判断，脚本不会验证其真伪 |
| `requirements[].evidence` | 非 pending 状态必填：对应覆盖矩阵、原题段落、语义审阅和日志位置 |
| `targets[].id/problem/role` | 唯一目标 ID、所属问题、`theorem` 或 `bridge` |
| `targets[].module/source/declaration` | 模块名、相对工程根的 `.lean` 文件路径、完全限定声明名 |

清单必须列全所有主定理及桥梁，每个目标都连接到至少一条要求。保留没有目标的原题要求；一个问题完全没有源码时无须强造目标以运行脚本，直接报告材料缺口。机器只能检查清单内部关联，不能证明它包含原题的全部义务。

独立桥梁使用命名 theorem，以便公理检查。将可信审计者创建的桥梁模块置于隔离副本中可导入的路径，作为未跟踪 harness 文件记录；不修改原目标源码或 Lake 配置，另列 harness 与原提交的差异。无法无侵入导入时用独立工程清单/人工检查，不偷偷修改提交。审核 `module` 与 `source` 对应关系，防止导入同名但来源不同的模块。

## 2. 预检与生成

从 skill 目录执行，命令中的路径用实际值替换：

```bash
python3 scripts/audit.py preflight /audit/targets.json --out /audit/preflight-01
python3 scripts/audit.py prepare /audit/targets.json --out /audit/prepared-01
```

输出目录必须不存在且与工程分离，防止旧结果混入新检查。预检只读配置文件及 Git 状态，不运行 Lake/Lean 或安装依赖。它记录 HEAD、工具链文件、锁文件、目标文件哈希和缺口，并要求 `role=theorem` 的文件确实存在于指定 commit 且与其 blob 一致；`prepare` 额外生成每个目标的审计 `.lean` 文件。

`ready_for_target_checks` 仅表示静态前置条件齐全。人工补齐预检中的 `manual_preconditions`：真实隔离、资源限额、工具来源/实际版本、依赖 checkout SHA、可信缓存、源码干净重建、未跟踪文件、模块映射。checker 是否支持该版本另行验证；预检不会自动下载或测试它。

缺少锁文件/历史版本等原项目问题可按复现参考人工处理，记录保证范围。不要为让预检变绿而创建伪 manifest、改 pin、删除未覆盖要求或清理作者的未提交修改。

## 3. 执行目标检查

**先完成并记录原样干净构建，再在已隔离环境内调用 run。脚本本身不创建隔离环境。** 指定受信的工具链内 Lake 绝对路径，不使用提交者自带二进制；清除的环境变量仅用于避免搜索路径误用，不构成安全沙箱。

```bash
python3 scripts/audit.py run /audit/targets.json \
  --out /audit/check-01 \
  --lake /trusted/lean-toolchain/bin/lake \
  --timeout 300
```

先记录 Lake 与项目内 Lean 的实际版本，并核对 Lean release/rc 版本与 pin；nightly、自建工具链或无法识别的版本输出转人工验证。对每个目标依次运行：显式 `lake build +Module`、`lake env lean` 检查目标源文件、生成文件内的 `#check @name` / `#print name` / `#print axioms name`。目标构建失败仍继续检查其他目标。保留参数数组、cwd、退出码、耗时、完整合并日志、日志哈希、脚本与清单哈希，并比较执行前后目标/配置文件及 HEAD。

每条命令独立超时；隔离环境还需限制总运行时间、磁盘、内存及 CPU。输入不稳定时整体为 `incomplete`，即使某条日志观察到 `sorryAx` 也不能直接归因原 commit。结果文件不能替代对完整依赖和整个源码树的前后状态核查。脚本不会替你获取依赖、自动 clean、运行 kernel replay 或 comparator。

| 结果 | 退出码 | 解释 |
| --- | --- | --- |
| `standard_axioms_only` | 0 | 清单全部目标的检查成功，观察到的传递公理至多为标准三项；语义结论始终为 `not_determined` |
| `proof_gap` | 1 | 输入稳定时至少一个已检查目标依赖 `sorryAx`；其他目标的阻塞仍需报告 |
| `trust_review_required` | 2 | 观察到其他公理，需核查来源；可能是占位公理，也可能是本机计算等扩展信任，不自动断言无效 |
| `incomplete` 或预检/输入错误 | 2 | 命令失败、超时、缺失/重复/无法解析的输出、版本不符或输入变化；按日志区分证明检查失败与环境阻塞 |

不提供自定义公理“一键白名单”。任何额外信任都由报告逐项说明，适用验收标准明确接受后才可判断有条件通过。人工填写的 coverage 不能让脚本跳过目标，也不能直接改变机械结果。

审计以目标依赖为范围：无关文件含 `sorry` 不直接否定目标；`P → P` 可以机械通过，仍须语义审阅判定额外/循环假设。`#print` 输出可能被不受信环境影响；这些日志不是防伪证书，也不是独立内核检查。保留主 skill 的挑战文件与外部复核要求。

## 4. 回归验证

```bash
python3 -m unittest discover -s tests -v
```

默认测试检查清单、失败处理和输出解析；模拟输出测试不称为实际 Lean 检查。真实回归需指定一个已经安装的受信 Lake（测试不会下载安装工具链）：

```bash
LEAN_AUDIT_TEST_LAKE=/trusted/lean-toolchain/bin/lake \
  python3 -m unittest discover -s tests -v
```

真实样例仅使用 Lean 标准库，在临时工程创建并固定 fixture commit。覆盖正常证明、间接 `sorry`、无关占位、额外公理、循环假设、缺失声明和未纳入默认构建的模块。循环假设样例应得到机械成功但语义未确定，这正是防止过度自动判定的检查。

当前真实 Lean 回归使用 Lean 4.32.0；其他版本仍需检查语法与输出兼容性。完整公理声明保留详细打印，公理列表单独关闭 universe 展示，避免把 `sorryAx.{u}` 错认成未知公理。
