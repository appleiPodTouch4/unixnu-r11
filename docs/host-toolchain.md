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
| `iokit/DriverKit/Makefile` | in the `%.h : %.iig` rule, after `iig` runs, an `awk` step injects the prototype into the generated `.iig.cpp` |

The iig output already splits on the kernel: its header block is
`#if KERNEL / #include <libkern/c++/OSString.h> / #else / #include
<DriverKit/DriverKit.h> / #endif`. It just does not move the `_Dispatch()` call
into the same guard. Under `KERNEL` the `IORPC` types are all present — the
compiler complains only about the missing function — so one prototype is the
whole fix.

The injection anchors on iig's own `/* @iig end */` marker, which lands after
every `#include` in the file:

```make
	$(_v)awk '/^\/\* @iig end \*\/$$/ && !iorpc { print; print "extern \"C\" IORPCMessage *IORPCMessageFromMach(IORPCMessageMach *, bool);"; iorpc = 1; next } { print }' $(patsubst %.h,%.iig.cpp,$@) > $(patsubst %.h,%.iig.cpp,$@).iorpc && mv $(patsubst %.h,%.iig.cpp,$@).iorpc $(patsubst %.h,%.iig.cpp,$@)
```

Rewriting the generated file was chosen after two dead ends. Adding `-include`
through `OTHER_CXXFLAGS` and then through `CXXFLAGS` both looked right —
`make -p` in `iokit/DriverKit` shows the flag on both variables — yet two full
rebuilds compiled without it, so something between the Makefile and the compile
line drops it. Where exactly was not isolated and does not need to be: the
injection depends on no variable at all. It only runs when the `.iig.cpp` is
regenerated, so delete `build/xnu/ios-obj/*/iokit/DriverKit/*.iig.cpp` after
touching this part of the patch.

Verify without running a build — XNU's `_v` is empty, so neither the log nor
`make -n` prints the real command line:

```sh
W=<tree>/.cache/xnu-work; O=<tree>/build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837
cd "$O/iokit/DriverKit" && clang++ -fsyntax-only -std=gnu++2b -fapple-kext \
  -DKERNEL -DKERNEL_PRIVATE -DAPPLE -DPRIVATE \
  -I"$O/iokit" -I"$O" -I"$W/iokit" -I"$W/osfmk" -I"$W/bsd" -I"$W/libkern" -I"$O/bsd" \
  -I"$W/EXTERNAL_HEADERS" --target=arm64-apple-ios17.0 \
  -isysroot "$(xcrun --sdk iphoneos --show-sdk-path)" OSObject.iig.cpp
```

No output means it passes. `-I"$O/iokit" -I"$O"` are required because the
generated headers live in the object directory.

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
