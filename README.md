# UniXNU-r11 — OPPO R11 (CPH1707 / 16051, SDM660)

Device repository for the OPPO R11 running UniXNU. Everything board-specific is
here; the UEFI platform is the sibling [`uefi-r11`](../uefi-r11) tree.

| Item | Value |
| --- | --- |
| SoC | Qualcomm SDM660 + PM660 / PM660L (8 cores, 2 clusters, Adreno 512) |
| Model | CPH1707, firmware model id 16051 |
| Display | Samsung S6E3FA3 AMOLED, 1080x1920, command mode, single DSI |
| Touch | Synaptics S3508, I2C1 `0x0C175000`, address `0x20` |
| Storage | eMMC 5.1, 69 partitions, no A/B, `userdata` is a grow partition |
| UEFI FD | `0x9FC00000` + `0x300000` (the window the stock XBL reserves for `UEFI FD`) |
| OS profile | iOS 16.5 / 20F66, spoofed as iPhone10,3 |

## Where the numbers come from

Nothing in this repository is a guess about the hardware. `scripts/extract-inputs.py`
reads the device's own OFP package and writes `inputs/`:

| File | Content | Consumer |
| --- | --- | --- |
| `inputs/r11-stock.dtb` | the 16051 device tree appended to the stock `boot.img` | firmware DTB for `unixnu bootimg` |
| `inputs/r11-stock.dts` | readable dump of the same tree (peripheral addresses, panel node with 79 properties, reserved memory) | `dts/`, `uefi-r11` |
| `inputs/hw.json` | memory, CPUs, reserved memory, peripherals, I2C map, panel identity, boot image geometry | `board.toml`, `dts/` |
| `inputs/partitions.json` | GPT of both LUNs (`boot` 64 MiB, `userdata` grow) | `board.toml [userdata]` |

```sh
python3 scripts/extract-inputs.py --ofp ../ofp_extracted
```

Two values are not in the OFP and are marked as such in `board.toml`:

* **DRAM size.** The stock tree zeroes `/memory` because ABL patches it from
  SMEM. `0xFE4C0000` (3.98 GiB) is the measured 4 GiB layout; read the real
  value on the device and update `dts/r11.dts`, `[payload] dram_size` and
  `[payload.adt] owned_memory_size` together.
* **`userdata` end.** It is a grow partition, so its end depends on the eMMC
  capacity. The committed value is the 64 GiB mapping.

## Build

Prerequisites: Python 3.11+, Xcode command line tools, `dtc`, `mtools`,
`llvm` (`llvm-objcopy`, `llvm-nm`), and the UniXNU checkout with its submodules.

```sh
cd ../UniXNU
git submodule update --init --recursive          # components, kits, DarwinBoot

# 1. UEFI platform: Mu-Silicium checkout + r11Pkg + vendor DXE binaries
../uefi-r11/scripts/prepare-base.sh              # writes ../uefi-r11-base and ../Mu_Basecore

# 2. Configuration and sources
./unixnu defconfig r11_defconfig -D ../UniXNU-r11
./unixnu fetch -D ../UniXNU-r11

# 3. Firmware volume (must be exactly 0x300000 bytes)
./unixnu build firmware -D ../UniXNU-r11 --uefi ../uefi-r11-base --edk2 ../Mu_Basecore

# 4. Kernel, payload, boot image
./unixnu build kernel -D ../UniXNU-r11
./unixnu build payload -D ../UniXNU-r11 --unique-chip-id <hex> --trust-cache <bundle>
./unixnu bootimg -D ../UniXNU-r11 --uefi ../uefi-r11-base \
  --dtb ../uefi-r11-base/Platforms/OPPO/r11Pkg/DeviceTree/r11.dtb

# 5. Boot without touching flash (boot is only 64 MiB, the payload is 192 MiB)
fastboot boot out/r11/ios-16.5-20F66/r11/boot/boot.img
```

`../build-r11.sh` runs the same sequence: `inputs`, `base`, `config`, `kernel`,
`payload`, `firmware`, `bootimg`, or `all` for the host-runnable part.

### Host split: what this machine can and cannot build

| Step | Host requirement | macOS 12 / Xcode 14.2 |
| --- | --- | --- |
| `defconfig`, `fetch`, `tree` | Python 3.11+ | ok |
| `build firmware` | `lld-link` (llvm@15 here) | ok, FD is exactly `0x300000` |
| `bootimg` | `llvm-objcopy`, `llvm-nm` | ok |
| `build kernel` | Apple clang, plus `scripts/xnu-clang` | builds and prelinks: 15.5 MB `mach.development.bcm2837`, 53.8 MB `kernel.macho` |

`xnu-10063` expects Xcode 15's compiler, but the three arguments it chokes on
here are all rewritable. `scripts/xnu-clang` (and its `xnu-clang++` symlink) drop
`-mach_msg2` — which the host's `migcom` forwards to the compiler — and supply the
gate Xcode 14 needs for `-ftrivial-auto-var-init=zero`. Two board patches fix
compile-time assertions that only a newer clang folds. What is left is a version
mismatch between the host's `iig` and `iokit/DriverKit/IORPC.h`. See
`docs/host-toolchain.md` for the evidence and both ways out.

### Firmware log

The board has no exposed UART, so the firmware keeps a 1 MiB in-memory log at
`0x9D300000` and ships `AdvancedLogDxe`, which exports it as QR codes under
**Tools → Advanced Logger**. Recording works today; reading it back needs a
payload, and a payload needs the kernel. `docs/firmware-log.md` has the details
and the rollback image path.

### Building the kernel on a GitHub macOS runner

The project's `macOS build` workflow (`.github/workflows/macos.yml` in the
UniXNU checkout) runs the kernel step on `macos-26` with Xcode 26.6:

```sh
git remote add origin git@github.com:<owner>/UniXNU-r11.git
git push -u origin main
# then, in the UniXNU fork's Actions tab: "macOS build"
#   device_repository = <owner>/UniXNU-r11
#   device_ref        = main
#   defconfig         = r11_defconfig
#   steps             = kernel
```

Add the `UNIXNU_UNIQUE_CHIP_ID` secret before using `steps=kernel payload`: this
board sets `[payload.adt] unique_chip_id = "required"`.

## State

Board inputs, firmware integration and boot image assembly are in place. The
kernel-side storage, display, input and power drivers are not written; see
`porting.toml` for the per-area status, limits and next action.

| Stage | Status |
| --- | --- |
| Hardware inputs from the OFP package | done (`inputs/`) |
| Format 2 board configuration, DTS, defconfig | done; `defconfig` resolves all four layers |
| UEFI platform package, FD layout, BootShim | builds here; boots on hardware (`fastboot boot`) |
| Firmware log (`Advanced Logger` + QR exporter) | builds and ships in the FD; readable once a payload exists |
| Vendor SDM660 DXE set | reused from a sibling UEFI device, profiles not R11-specific |
| Display | simple framebuffer over the stock splash buffer; no MDSS/DSI driver |
| Storage / input / power | no XNU driver (UEFI side works through vendor drivers) |
| Kernel | builds and prelinks on this host; `build/xnu/.../mach.development.bcm2837` 15.5 MB, `kernel/kernel.macho` 53.8 MB |
| Payload / boot image | payload 192 MiB holding `kernel.macho` and its ADT; `boot.img` 202,670,080 bytes carries it as the ramdisk (`fastboot boot` only) |

## Related

* [`docs/emmc-test-log.md`](docs/emmc-test-log.md) — irq50–irq94 eMMC/USB bring-up test table.
* `porting.toml` — the porting record: inputs, findings, limits, next actions.
* [`../uefi-r11`](../uefi-r11) — the Mu-Silicium platform package for this board.
* `soc/` — the SDM660 layer vendored in this repository so a clone builds without siblings\n  (`../UniXNU-sdm660-common` is the same content, kept for a future published repository).
* UniXNU documentation: [porting](https://unixnu.com/porting/), [UEFI firmware](https://unixnu.com/porting/uefi-firmware), [device repository](https://unixnu.com/porting/device-repository).
