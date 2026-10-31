# Host toolchain for the r11 port

The firmware, payload and boot image steps run on macOS 12 Monterey with the
tools `../scripts/install-tools.sh` installs. The kernel step does not.

## What works on this host

| Step | Host requirement | State |
| --- | --- | --- |
| `unixnu fetch`, `defconfig`, `status`, `tree` | Python 3.11+ | ok |
| `unixnu build firmware` | llvm@15 (`lld-link`), EDK II `mu_basecore` | ok, `R11_UEFI.fd` is exactly `0x300000` |
| `unixnu bootimg` | llvm-objcopy/llvm-nm | ok |
| `unixnu build kernel` | Apple clang with `-mach_msg2` (Xcode 15+) | **blocked** |

## Why the kernel step is blocked

`xnu-10063` runs `mig` over its definitions, and the generated server files are
compiled with `-mach_msg2`. Both compilers available here reject that flag:

```
/usr/bin/clang -mach_msg2 ...            -> error: unknown argument: '-mach_msg2'   (Apple clang 14.0.0, Xcode 14.2)
~/.local/opt/llvm/bin/clang -mach_msg2   -> error: unknown argument: '-mach_msg2'   (LLVM 15.0.7)
```

LLVM 15 additionally gates `-ftrivial-auto-var-init=zero` behind
`-enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang`, and
`scripts/unixnu/kernel.py` puts Homebrew LLVM first on `PATH` for the archive
builders, so it wins over the Command Line Tools compiler.

macOS 12 caps Xcode at 14.3, so a newer Xcode cannot be installed here. The
project's own CI runs the same step on `macos-26` with Xcode 26.6.

## What already passes here

The work before the compile is complete and reproducible on this host:

* all 60 arch/SoC patches apply, including the board copy of
  `zzz-boot-progress.patch` (see `patches/xnu/series`);
* the archive builders (corecrypto 14, libpthread, mockfs fixture, libdispatch
  firehose) build and install into the fakeroot;
* the bootstrap script accepts the board configuration
  (`CONFIG_XNU_BOOT_PROGRESS=n`, owner mount chain off).

## How to build the kernel until a newer host exists

Use the project's `macOS build` workflow (`.github/workflows/macos.yml`):

| Input | Value |
| --- | --- |
| `device_repository` | `<owner>/UniXNU-r11` |
| `device_ref` | the branch you pushed |
| `defconfig` | `r11_defconfig` |
| `steps` | `kernel` (add `payload` once the platform seed is a secret) |

Set the `UNIXNU_UNIQUE_CHIP_ID` secret when the payload step runs; the r11
board requires the seed because `[payload.adt] unique_chip_id = "required"`.
