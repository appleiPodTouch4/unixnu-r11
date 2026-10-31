# Firmware log capture on the OPPO R11

The R11 has no exposed UART, so anything the firmware or DarwinBoot prints is
invisible unless it is either drawn on the panel or kept in memory and read back
from a menu. Both are now wired up. This page records what was added, why the
addresses are what they are, and what is still missing.

## What the platform looked like before

`SiliciumPkg/SiliciumPkg.dsc.inc` maps `DebugLib` to `BaseDebugLibSerialPort` on
DEBUG and `SerialPortLib` to `FrameBufferSerialPortLib`, so `DEBUG()` output
already lands on the panel. That is why the boot is not silent. It scrolls away,
though, and the screen is the only copy.

## What was added

| Piece | Where | Why |
| --- | --- | --- |
| `DebugLib` → `BaseDebugLibAdvancedLogger` | `r11.dsc` `[LibraryClasses]` | every `DEBUG()` line also goes into the memory log |
| `AdvancedLoggerLib` per phase | `r11.dsc` `[LibraryClasses.common.SEC/DXE_CORE/DXE_DRIVER/DXE_RUNTIME_DRIVER]` | the buffer is formatted once in SEC, published as a HOB, then read through `gAdvancedLoggerProtocolGuid` |
| `AdvancedLoggerHdwPortLib` | `r11.dsc` | keeps the on-screen output: the hardware port writes to `SerialPortLib`, i.e. the framebuffer |
| `QrEncoderLib`, `AdvancedLoggerAccessLib` | `r11.dsc` | needed by the exporter |
| `UniXNUPkg/Driver/AdvancedLogDxe` | `r11.dsc` `[Components]`, `Include/DXE.inc` | registers **Tools → Advanced Logger**, which pages the log out as QR codes |
| `AdvLogger` memory region | `Library/MemoryMapLib/MemoryMapLib.c` | the buffer must be reserved and never allocated |
| `[payload] tools = true` | `board.toml` | puts the **Tools** entry in the generated boot menu |

The mapping is listed after `!include StarlordPkg/StarlordPkg.dsc.inc`, so it
wins over SiliciumPkg's `DebugLib`.

## Why 0x9D300000

The stock XBL declares `DXE Heap` as `0x94000000 + 0x09400000`, which runs to
`0x9D800000` — straight through the continuous-splash carve-out at `0x9D400000`.
The map is ours to correct, so the heap now ends at `0x9D300000` and the last
MiB of it is `AdvLogger`:

```c
{"DXE Heap",    0x94000000, 0x09300000, AddMem, SYS_MEM, SYS_MEM_CAP, Conv,   WRITE_BACK_XN},
{"AdvLogger",   0x9D300000, 0x00100000, AddMem, SYS_MEM, SYS_MEM_CAP, Reserv, WRITE_BACK_XN},
{"Display Reserved", 0x9D400000, 0x02400000, ...},
```

`r11.dsc` sets `PcdAdvancedLoggerBase` to the same address with
`PcdAdvancedLoggerPages = 0x100` (1 MiB). It is a reserved DRAM window, so SEC
can format the header before any allocator exists — SEC runs with DDR already up
because ABL loaded the payload there.

The `Log Buffer` entry at `0x9FFF7000` was deliberately not reused: those 32 KiB
belong to the vendor ABL logger and are in its own format.

## What is verified by the build

* `R11_UEFI.fd` is still exactly `3145728` bytes.
* `AdvancedLogDxe.efi` (35 KiB) is in `FVMAIN.Fv`: `FV/Guid.xref` lists
  `8D4E7F50-3A2C-4C9A-9E1B-50C4C8472D41 AdvancedLogDxe`, and `FVMAIN.inf` carries
  its FFS path.
* `SEC` links `AdvancedLoggerLib/PeilessArm`, `DxeMain` links
  `AdvancedLoggerLib/DxeCore`, DXE drivers link the `Dxe` instance.
* `boot.img` is `1343488` bytes: gzip payload `3145840` (= 112-byte BootShim +
  3145728-byte FD), appended DTB `330172` bytes, `tags` at `0x100`.

## What cannot be read yet

**The Tools menu comes from the payload's `unixnu.toml`, and the payload needs a
kernel.** `unixnu build payload` copies `payloads/kernel.macho` first, so until the
kernel links there is no payload, no boot menu, and no way to open the exporter.
The log is being recorded; nothing can read it back.

Once the kernel exists, the sequence on the device is:

1. `fastboot boot out/r11/ipados-17.7.11-21H461/r11/boot/boot.img`
2. pick the kernel entry; if the loader reports an error it returns to the menu
3. **Tools → Advanced Logger**, then scan the rotating QR frames with
   [OneSend](https://onesend.01mvp.com) on another device and save the `.log`

A panic that resets the phone before the menu comes back loses the in-memory log.
For that case the fallback is a reserved log region written by the kernel plus a
Linux or recovery reader; see `UniXNU/docs/zh/porting/log-capture.md`.

## Rollback

The previous image is kept next to the new one:

```
out/r11/ipados-17.7.11-21H461/r11/boot/boot.img.bak-pre-advlogger   1331200 bytes
```

Nothing is flashed — the port boots with `fastboot boot` — so booting the old
file restores the exact previous behaviour.
