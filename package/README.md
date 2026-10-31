# Board package (kit `r11`)

The build assembles this directory into the tree as `kits/r11` and links it from
`kits/r11`. Kernel archive scripts and board services live here once they exist.

## What belongs here

| Content | Purpose |
| --- | --- |
| `build-r11-*.py` | archive recipes referenced by `board.toml [kernel] archives` |
| `R11Display*`, `R11Touch*`, `R11Sdhci*` | board drivers linked into the kernel |
| `r11-platform-power.py` | PM660 regulator and clock configuration for the kernel |
| `make-r11-adt.py` | only for format 1; format 2 uses the shared ADT generator |

## What is deliberately absent

The first bring-up has no board drivers: `board.toml [kernel] archives` lists the
arch-profile scripts only, and `configs/r11_defconfig` keeps
`CONFIG_XNU_NATIVE_UFS`, `CONFIG_XNU_NATIVE_RAM_BLOCK` and the display switches
off, so the kernel runs against a mockfs root. Adding a driver means adding its
recipe here **and** its archive line to `board.toml`, then updating the matching
`porting.toml` area.

## Priority order

1. eMMC (`SDHCI v5`): unblocks a real root and the Data volume.
2. DSI panel (`S6E3FA3`, command mode): the menu already works on the stock
   framebuffer, the kernel console does not.
3. Touch (`S3508` over RMI4).
4. Power (`PM660` / `PM660L`, OPPO charger MCU).
