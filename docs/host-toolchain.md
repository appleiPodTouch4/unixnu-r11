# Host toolchain for the r11 port

Everything except one XNU file builds on macOS 12 Monterey with the tools
`../scripts/install-tools.sh` installs. This page records what the host can do,
what had to be rewritten to get there, and the one remaining blocker.

## What works on this host

| Step | Host requirement | State |
| --- | --- | --- |
| `unixnu fetch`, `defconfig`, `status`, `tree` | Python 3.11+ | ok |
| `unixnu build firmware` | llvm@15 (`lld-link`), EDK II `mu_basecore` | ok, `R11_UEFI.fd` is exactly `0x300000` |
| `unixnu bootimg` | llvm-objcopy/llvm-nm | ok |
| `unixnu build kernel` | Apple clang 14.0.0 (Xcode 14.2) + `scripts/xnu-clang` | compiles the tree; `iokit/DriverKit/OSObject.iig.cpp` still fails |

## Three toolchain differences, all rewritten

`xnu-10063` is an iOS 17 kernel and expects Xcode 15's compiler. Apple clang 14
here rejects three things; none of them needs a newer machine.

| Argument | Why Xcode 14 rejects it | Fix |
| --- | --- | --- |
| `-mach_msg2` | passed to `migcom`, which does not know it and forwards it to the compiler running the generated stubs | `scripts/xnu-clang` drops it; mig then emits `mach_msg_trap` stubs, which the kernel trap table still carries |
| `-ftrivial-auto-var-init=zero` | implemented but gated | the shim appends `-enable-trivial-auto-var-init-zero-knowing-it-will-be-removed-from-clang` |
| C++ objects (`.cpo`) | the same zero-init flag arrives through `CXX`, not `CC` | `scripts/xnu-clang++` (a symlink to the same file) is passed as `CXX` |

`scripts/build-xnu-4k-baseline.sh` gained `XNU_CC` / `XNU_CXX` for this, and
`build-r11.sh kernel` sets both. That script belongs to the UniXNU checkout, so a
`git pull` there has to keep the two-line hook.

On top of the compiler, two sources make compile-time assertions that are not
integer constant expressions in C — Xcode 15's clang folds them, Xcode 14's does
not. Board patches `patches/xnu/zzzz-host-clang-*.patch` fix those two:

* `osfmk/ipc/mach_port.c` asserts on a `const` local;
* `libkern/os/log.c` asserts that two macro aliases have the same address.

## The fourth gap: host `iig` against restored headers

```
DriverKit/OSObject.iig.cpp:233: use of undeclared identifier 'IORPCMessageFromMach'
```

`OSObject.iig.cpp` is generated at build time by the host's `iig`, and the `iig`
that ships with Xcode 14 emits an unguarded call to `IORPCMessageFromMach()`
from the `_Dispatch()` method of every `*.iig.cpp`. In `xnu-10063` that function
is declared only inside `#ifndef KERNEL` in `iokit/{IOKit,DriverKit}/IORPC.h`,
and the kernel keeps only the reply variant, `static
IORPCMessageFromMachReply()` in `iokit/Kernel/IOUserServer.cpp`. Newer `iig`
wraps the call in `#if !KERNEL`, which is why the same source builds in CI.

The trap is the header. `iokit/DriverKit/*.h` are **not part of the tree**:
`scripts/prepare-xnu-source.py` restores them from Apple's
`xnu-10063.121.3` **after** the patch series runs, and `restore()` skips any
target that already exists. So a board patch cannot touch `IORPC.h` — in
`.cache/xnu-work` the file is untracked (`??`), and on a fresh clone it is not
there at all.

`patches/xnu/zzzz-host-iig-iorpc-export.patch` therefore splits the fix across
two files that *are* tracked:

| File | Change |
| --- | --- |
| `iokit/Kernel/IOUserServer.cpp` | the reply body becomes `extern "C" IORPCMessage *IORPCMessageFromMach(IORPCMessageMach *, bool reply)`; `IORPCMessageFromMachReply()` stays as a one-line `static` wrapper passing `true`, so every in-kernel caller is untouched |
| `iokit/Kernel/iorpc_kernel_export.h` | new file: the prototype, forward declaring both structs because it is processed before the translation unit's own includes |
| `iokit/Makefile` | `OTHER_CXXFLAGS += -include $(SRCROOT)/iokit/Kernel/iorpc_kernel_export.h`, appended **after** `include $(MakeInc_dir)` |

`OTHER_CXXFLAGS` is XNU's own extension point — `makedefs/MakeInc.def:594`
feeds it into `CXXFLAGS_GEN`, which is what `P_RULE_1A` compiles `.iig.cpp` with.

Two placement details are not optional:

* **It belongs in `iokit/Makefile`, not `iokit/DriverKit/Makefile`.** Every
  directory Makefile re-runs `include $(MakeInc_def)`, and that file *assigns*
  `OTHER_CXXFLAGS` with `=` rather than `+=`. The parent `iokit/Makefile` reads
  its siblings (`IOKit`, `DriverKit`, `Exclaves`) while expanding
  `EXPINC_SUBDIRS`, so an append made inside `iokit/DriverKit/Makefile` is wiped
  before the C++ rules ever run. Verify with
  `cd iokit && SRCROOT=… make -f Makefile -p -n | grep '^OTHER_CXXFLAGS'`:
  empty means the append was lost, non-empty means it survives.
* **It has to come after the last include.** Hence the end of the file.

The `reply` argument only selects which version constant the message id is
checked against, so splitting the function is behaviour-preserving: the kernel
now passes `true` where it always did, and the generated `_Dispatch()` code
passes `false`, exactly as Apple's non-kernel implementation expects.

The alternative needs no source change: run the kernel step in CI, where Xcode
26.6's `iig` matches the header. See `README.md`.

## What already passes here

* all 62 patches apply, including the board copy of `zzz-boot-progress.patch` and
  the two host-clang workarounds (see `patches/xnu/series`);
* every XNU translation unit except the DriverKit one above compiles;
* the firmware volume builds with the Advanced Logger and `AdvancedLogDxe`
  (`docs/firmware-log.md`);
* the archive builders (corecrypto 14, libpthread, mockfs fixture, libdispatch
  firehose) run, but they need `build/xnu/ios-obj/.../link.filelist`, which only a
  completed bootstrap pass writes — so they cannot finish until the kernel links.

## How to build the kernel until that file is ported

Use the project's `macOS build` workflow (`.github/workflows/macos.yml`):

| Input | Value |
| --- | --- |
| `device_repository` | `<owner>/UniXNU-r11` |
| `device_ref` | the branch you pushed |
| `defconfig` | `r11_defconfig` |
| `steps` | `kernel` (add `payload` once the platform seed is a secret) |

Set the `UNIXNU_UNIQUE_CHIP_ID` secret when the payload step runs; the r11
board requires the seed because `[payload.adt] unique_chip_id = "required"`.
