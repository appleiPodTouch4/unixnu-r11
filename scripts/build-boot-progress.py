# Build the r11 boot progress kit (kits/r11) against the actual source-kernel ABI.
#
# From UniXNU-fajita / UniXNU-sirius scripts/build-boot-progress.py (BSD-2-Clause-Patent),
# which is from UniXNU-sheng: replays the recorded compile command of startup.o (and
# kern_exec.o for the bsd-side objects) with the kit sources, then archives the objects
# into build/boot-progress/libBootProgress.a, which build-xnu-4k-baseline.sh force-loads
# into the kernel link when CONFIG_XNU_BOOT_PROGRESS=y.
#
# Board differences vs sirius: no UFS log writer (BootLog.c stays out), the USB/eMMC
# probe objects are absent and every missing board counter is covered by the generated
# BootProgressStubs.c weak data stubs.
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/boot-progress'
OUT.mkdir(parents=True, exist_ok=True)
KIT = ROOT / 'kits/r11'
startup_record = json.loads((ROOT / 'build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837/osfmk/DEVELOPMENT/startup.o.json').read_text().strip().rstrip(','))
kexec_record = json.loads((ROOT / 'build/xnu/ios-obj/DEVELOPMENT_ARM64_BCM2837/bsd/DEVELOPMENT/kern_exec.o.json').read_text().strip().rstrip(','))


def replay(record, source, obj, extra):
    """Replay a recorded compile command with a different source/object.

    Warning flags: keep the recorded -Wno-* suppressions (the kit must compile
    under the same quiet-down flags as the kernel itself; the Xcode 14 clang
    even errors on xnu's stddef.h without -Wno-null-pointer-subtraction) and
    strip the rest, then apply the kit's own -Wall -Wextra -Werror.
    """
    command = []
    args = record['arguments']
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == record['file']:
            command.append(str(source))
        elif arg in ('-o', '-MF', '-MT', '-MJ'):
            if arg == '-o':
                command += ['-o', str(obj)]
            i += 1
        elif arg == '-Xclang' and args[i + 1].startswith('-W'):
            if args[i + 1].startswith('-Wno'):
                command += [arg, args[i + 1]]
            i += 1
        elif arg.startswith('-Wno'):
            command.append(arg)
        elif arg.startswith('-W'):
            pass
        elif arg == '-D' and args[i + 1].startswith('XNU_BOOT_PROGRESS='):
            i += 1
        else:
            command.append(arg)
        i += 1
    command += extra
    subprocess.run(command, cwd=record['directory'], check=True, timeout=120)
    return command


# -Wno-error=null-pointer-subtraction: xnu's own EXTERNAL_HEADERS/stddef.h
# defines ptrdiff_t via ((int*)NULL - (int*)NULL), which only turns into an
# error once our -Werror is appended; the kernel build leaves it a warning.
BP_ARGS = ['-DXNU_BOOT_PROGRESS=1', '-mgeneral-regs-only', '-Wall', '-Wextra', '-Werror',
           '-Wno-error=null-pointer-subtraction',
           '-I', str(ROOT / '.cache/xnu-work/osfmk'), '-I', str(KIT)]

main_cmd = replay(startup_record, KIT / 'BootProgress.c', OUT / 'BootProgress.o', BP_ARGS)

# BootProgressStubs.c and BootReset.c reuse the same replayed command line.
replay(startup_record, KIT / 'BootProgressStubs.c', OUT / 'BootProgressStubs.o', BP_ARGS)
replay(startup_record, KIT / 'BootReset.c', OUT / 'BootReset.o', BP_ARGS)
# FaultProbe is osfmk-side (kdp/vm headers).
replay(startup_record, KIT / 'BootFaultProbe.c', OUT / 'BootFaultProbe.o', BP_ARGS)

# WatchdogPolicy and DiagExport are bsd-side: replay the kern_exec.o record instead.
def replay_bsd(record, source, obj):
    command = []
    args = record['arguments']
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == record['file']:
            command.append(str(source))
        elif arg in ('-o', '-MF', '-MT', '-MJ'):
            if arg == '-o':
                command += ['-o', str(obj)]
            i += 1
        elif arg == '-Xclang' and args[i + 1].startswith('-W'):
            i += 1
        elif not arg.startswith('-W'):
            command.append(arg)
        i += 1
    # Same -W handling as replay(): keep -Wno-*, strip the rest.
    j = 0
    filtered = []
    while j < len(command):
        arg = command[j]
        if arg == '-Xclang' and command[j + 1].startswith('-W'):
            if command[j + 1].startswith('-Wno'):
                filtered += [arg, command[j + 1]]
            j += 1
        elif arg.startswith('-Wno'):
            filtered.append(arg)
        elif arg.startswith('-W'):
            pass
        else:
            filtered.append(arg)
        j += 1
    filtered += ['-mgeneral-regs-only', '-Wall', '-Wextra', '-Werror',
                '-Wno-error=null-pointer-subtraction']
    subprocess.run(filtered, cwd=record['directory'], check=True, timeout=120)


replay_bsd(kexec_record, KIT / 'BootWatchdogPolicy.c', OUT / 'BootWatchdogPolicy.o')
replay_bsd(kexec_record, KIT / 'BootDiagExport.c', OUT / 'BootDiagExport.o')

archive = OUT / 'libBootProgress.a'
archive.unlink(missing_ok=True)
subprocess.run(['xcrun', 'ar', 'rcs', str(archive), str(OUT / 'BootProgress.o'),
                str(OUT / 'BootProgressStubs.o'), str(OUT / 'BootFaultProbe.o'),
                str(OUT / 'BootWatchdogPolicy.o'), str(OUT / 'BootDiagExport.o'),
                str(OUT / 'BootReset.o')], check=True, timeout=60)
(OUT / 'compile-command.json').write_text(json.dumps(main_cmd, indent=2) + '\n')
print('r11 boot progress kit built:', archive)
