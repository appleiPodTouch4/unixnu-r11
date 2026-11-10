# R11 eMMC 测试结果（irq50–irq99）

本表汇总 XNU `qcom_emmc` 在 OPPO R11（SDM660，eMMC 5.1）上的真机测试。
每次只改变一个变量，镜像通过 `fastboot boot` 加载，不写分区。

> irq99 镜像与 irq98-linux 字节相同；它不能算独立的 irq99 二进制结果。
> 当前结论：CMD13 能到 Transfer/READY_FOR_DATA，CMD17/CMD18 命令通道可完成，
> 但 LBA1 数据仍是第一个 word 重复（`4546492045464920`，即 `"EFI EFI "`），
> 没有读到 `EFI PART`。eMMC 数据阶段尚未打通。

## eMMC 数据阶段

| irq | 关键改动 | 结果 | 结论 |
|---|---|---|---|
| 50 | 4.2 MHz 读 LBA1 | `EFI EFI` 首字重复 | 采样/时钟问题 |
| 51 | PIO 逐字 gating（Buffer Read Enable） | 仍首字重复 | 单纯 gating 不够 |
| 52 | 启用 SDMA | 面板 row 4 被覆盖，结果不可见 | 面板布局问题 |
| 53 | 字段并到 row 2 | 可见但行过长 | 面板布局问题 |
| 54 | EMMC 字段独占 row 3 | 推荐布局 | 后续基准 |
| 55 | CMD6 强制 1-bit 后读 | LBA1 全 0/EIO，LBA0 超时；不黑 | 1-bit 切换假设否掉 |
| 56 | 400 kHz + SDMA + PIO 对照 | 黑屏 | normal SDMA 是黑屏原因之一 |
| 57 | 强制 SDHCI v4 布局 | v4 失败 | host 实际为 v3 |
| 58 | warm-inherit + CMD13/SDMA | 黑屏，无照片 | 从 HS400/8-bit 直接搬数据会挂总线 |
| 59 | 只读 boot 状态探针 | 读到状态，随后黑屏 | 仅观察可用，数据仍不可用 |
| 60 | 关闭 UEFI charger watchdog | 仍黑 | charger watchdog 排除 |
| 61 | warm ADMA2 读 LBA1 | row 3 被 REG 覆盖 | 面板冲突，warm 未成功 |
| 62 | REG 移到 row 28 | `w=1`，CMD13 失败，`st=0` | UEFI 交棒卡未选中 |
| 63 | CMD7 RCA1 → CMD13 | 构建顺序 bug，`w=1` 无效 | 不能判断 RCA1 |
| 64 | 修正 CMD7/CMD13 顺序 | `w=2`，CMD7 RCA1 失败 | 卡确实未被 UEFI 保留 selected |
| 65 | normal path 改 PIO-only | 不黑；`EFI EFI`，EXT_CSD 零 | 黑屏来自 SDMA；数据仍 stale |
| 66 | CMD6 HS_TIMING=0 → BUS_WIDTH=0 | stale，no capacity；不黑 | 顺序/宽度切换未解决数据 |
| 67 | CMD6 HS/BW 结果上屏 | `c6=00800900/00800900`，R1 接受但 busy 超时 | 命令通道可，busy 不释放 |
| 68 | CMD6 R1b busy 等 2 s | HS0 成功，BUS_WIDTH 卡死，init 60 | 等 2 s 仍不够 |
| 69 | 只做 HS_TIMING=0，保持 8-bit | 未单独上机，被 irq70 取代 | 只改一个变量的对照 |
| 70 | 1.8 V 写在 HS0 之后 | HS0 在 3.3 V 就 busy，1.8 V 未执行 | 1.8 V 方案未被真正测到 |
| 71 | 1.8 V 提前到 CMD7/HS0 前 | 未单独上机；irq82 同代码覆盖 | irq82 证明 HS0 仍 busy |
| 72 | init 错误后 30 s 自动重启 | 触发，但 IOPlatformExpert 超时 panic | 自动重启不可用，已删除 |
| 73 | 直接 PE 复位 | 未作为 eMMC 结果采用 | 自动重启路线取消 |
| 82 | 去掉 USB 串口，保留 1.8 V early + HS0 + 8-bit | `hs0 busy`，`d1=0` | HS0 切换仍是硬阻塞 |
| 83 | 跳过 HS0/BUS_WIDTH，1-bit default + 1.8 V + PIO | `d1=4546492045464920`，`s=0`，init 60 | 1-bit default 数据仍 stale |
| 84 | warm RCA 1..8 + PIO；失败回 normal | `warm no rca`，fallback `EFI EFI`，init 6 | **最后一次确认 `EFI EFI`** |
| 85 | 跳过 `SWRST_ALL` | 未单独拍照，随后并入 irq86 | 未确认 |
| 86 | GCC 400k + alt FIFO | 卡在 GCC，未到 `clk 400k id`/`v3`，`d1=0` | GCC 写本身是新阻塞 |
| 87 | 只清 alt FIFO | `CMD1 busy`，`d1=0` | 只清 FIFO 不够 |
| 88 | GCC safe + FIFO | `gcc up=1`、`v3 6440->6040`、`pwr no event`，`d1=0` | 时钟/FIFO 成功，电源/CMD1 失败 |
| 89 | 跳过 PMIC handshake | `CMD1 busy`，`d1=0` | 跳过电源不能救 CMD1 |
| 90 | GCC 后 SDHCI divider=0 | `CMD1 busy`，`d1=0` | divider 不是阻塞 |
| 91 | 恢复 PMIC handshake | `CMD1 busy`，`d1=0` | 电源握手仍无法让卡应答 |
| 92 | CMD0 `0xF0F0F0F0` 后加 10 ms | 仍 `EFI EFI`，`s=0`，`n=512` | HS400 复位等待不是根因 |
| 93 | CMD17 前 `SWRST_CMD/DAT` 0x06 | 仍 `EFI EFI`，`hc2=0000/0003` | FIFO/DMA 残留不是根因 |
| 94 | CMD18 多块读 2 blocks | 已上机；`EFI EFI`，`s=0`；CMD18 只传 1 块（`s=512`） | 多块/AUTO_CMD12 未解决 |
| 95 | CMD17，BUF_RDY → drain → TC | 仍 `EFI EFI`，`s=0`，`n=512` | TC/FIFO 顺序不是唯一根因 |
| 96 | CMD16 SET_BLOCKLEN=512 | 仍 `EFI EFI`；`rev 0`、`sec 0`、`no capacity`、`init failed 6` | 块大小不是根因 |
| 97 | 只更新 IRQ 标记 | 仍 `EFI EFI`，`w=0`，`init failed 6` | 无新变量 |
| 98 | Linux 风格：保留 HS400/8-bit/ADMA，不复位 | `warm no rca`、`linux no rca`、`init failed 6` | RCA/命令相位失败 |
| 99 | 写 `CORE_VENDOR_SPEC=0xa9c` | 镜像与 irq98-linux 相同；仍 `no rca` | 未体现新改动 |

## irq95–irq99 镜像

| irq | 大小 | sha256 |
|---|---|---|
| 95 | 8,638,464 | `87b55c2598dff44f15fad2e18f7336f482856a6913af19a5c82d4091d62384cd` |
| 96 | 8,638,464 | `0feee44fba8f5f489e4af79c35de61d8cbdff6a0fb9d5f3fe1310eb59f1c4114` |
| 97 | 8,646,656 | `cd39ab00fa64e25671467666bbede0b427640c63956a7a7ce895c1bebb016ef9` |
| 98 | 8,642,560 | `8a487cf3ad0a423473e21734966a31c1ba4609a3e5f56fbfb3b85d0a2f33123b` |
| 98-linux | 8,638,464 | `b21a92ddc03fbdf61b624cf24f44285b7e9143b4a691859ce17b8d56982bd0d2` |
| 99 | 8,638,464 | `b21a92ddc03fbdf61b624cf24f44285b7e9143b4a691859ce17b8d56982bd0d2`（与 98-linux 相同） |

## USB CDC 串口（irq74–irq81，已放弃）

| irq | 改动 | 结果 |
|---|---|---|
| 74 | DWC3 基础 CDC ACM | 不枚举 |
| 75 | QUSB2 PHY + QSCRATCH | `u=5` |
| 76 | bus reset 重 arm EP0 + ACM protocol 0 | `u=5` |
| 77 | no-data control 补 status | `u=5` |
| 78 | SET_ADDRESS 延后 + 诊断行 | `u=5` |
| 79 | last SETUP/status 计数 | `su=0005003a`，`d=0/0` |
| 80 | 未发布（错误 TRB data type） | — |
| 81 | status IN 走 EP1 | 仍 `u=5`；串口已 parked |

## 当前基线

- 精确 irq84：`boot-irq84.img`（8,691,712 字节，`72fae77f…`）
- 源码 irq84 可启动重建版（UEFI 已移除 SdccDxe）：`boot-irq84-rebuild-nosdcc.img`（8,642,560 字节，`a17189cc…`）
- UEFI 实验驱动在 `boot-control/wip-clockdxe/`，不再参与构建
