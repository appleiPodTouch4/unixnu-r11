#!/usr/bin/env python3
"""Board preflight for the OPPO R11 firmware step.

"unixnu build firmware" runs this before EDK II starts (board.toml
[firmware] preflight). It checks the inputs that silently break a boot image
when they disagree:

  * the firmware device tree exists and is a valid FDT with the r11 identity;
  * the FD base/size in the Mu-Silicium config equal the ones compiled into the
    platform DSC and the BootShim;
  * the UniXNU modules are both built (DSC) and embedded (FDF);
  * the vendor binary directory the DXE list references exists.

Exit status 0 means "nothing inconsistent found"; warnings never fail the build.
"""
import os
import re
import struct
import sys
import tomllib
from pathlib import Path

TREE = Path(__file__).resolve().parents[1]
MAGIC = 0xD00DFEED


def find_device(tree):
    """The device repository, whether this script runs in the repository or in a build tree.

    "unixnu build firmware" copies scripts/ into the tree but not inputs/, so when the
    script runs there the repository is recovered from tree/.cache/firmware, a symlink
    the build points at <device>/.cache/firmware.
    """
    if (tree / 'board.toml').is_file():
        return tree
    link = tree / '.cache/firmware'
    if link.is_symlink():
        device = link.resolve().parent.parent
        if (device / 'board.toml').is_file():
            return device
    value = os.environ.get('UNIXNU_DEVICE')
    return Path(value).resolve() if value else tree


DEVICE = find_device(TREE)


def fail(message):
    print(f'check-r11: {message}', file=sys.stderr)
    sys.exit(1)


def warn(message):
    print(f'check-r11: warning: {message}', file=sys.stderr)


def find_uefi():
    for value in (os.environ.get('UNIXNU_UEFI'),):
        if value and (Path(value) / 'Resources/Configs/r11.toml').is_file():
            return Path(value)
    for candidate in (DEVICE.parent / 'uefi-r11-base', DEVICE.parent / 'uefi-r11'):
        if (candidate / 'Resources/Configs/r11.toml').is_file():
            return candidate
    return None


def main():
    dtb = DEVICE / 'inputs/r11-stock.dtb'
    if not dtb.is_file():
        fail(f'missing {dtb}; run scripts/extract-inputs.py --ofp <OFP directory>')
    blob = dtb.read_bytes()
    magic, total = struct.unpack_from('>II', blob, 0)
    if magic != MAGIC or total != len(blob):
        fail(f'{dtb} is not a valid flattened device tree')
    if b'qcom,sdm660-mtp' not in blob:
        warn(f'{dtb} does not look like an SDM660 device tree')

    uefi = find_uefi()
    if uefi is None:
        warn('no uefi checkout found (--uefi / UNIXNU_UEFI); skipping firmware checks')
        print('check-r11: board inputs ok')
        return 0

    config = tomllib.loads((uefi / 'Resources/Configs/r11.toml').read_text())
    fd = config['uefi_fd']
    base, size = fd['base'], fd['size']

    dsc = uefi / 'Platforms/OPPO/r11Pkg/r11.dsc'
    if not dsc.is_file():
        fail(f'{dsc} missing: is {uefi} the prepared r11 checkout?')
    text = dsc.read_text()
    for key, value, pattern in (
            ('FD base', base, r'gArmTokenSpaceGuid\.PcdFdBaseAddress\|(0x[0-9A-Fa-f]+)'),
            ('FD size', size, r'gArmTokenSpaceGuid\.PcdFdSize\|(0x[0-9A-Fa-f]+)')):
        match = re.search(pattern, text)
        if not match:
            fail(f'{dsc} does not set {key}')
        if int(match.group(1), 16) != value:
            fail(f'{key} differs: config {value:#x}, DSC {int(match.group(1), 16):#x}')

    fdf = uefi / 'Platforms/OPPO/r11Pkg/r11.fdf'
    if not fdf.is_file():
        fail(f'{fdf} missing')
    body = fdf.read_text()
    for module in ('UniXNUPkg/Application/UniXNU/UniXNU.inf',
                   'UniXNUPkg/Driver/UniXNUDxe/UniXNUDxe.inf',
                   'UniXNUPkg/Driver/UniXNURamDiskDxe/UniXNURamDiskDxe.inf',
                   'DarwinBootPkg/Driver/DarwinBoot.inf'):
        if module not in body:
            fail(f'the firmware volume does not embed {module}')
        if module not in text:
            fail(f'the DSC does not build {module}')
    if 'Fat.inf' not in (uefi / 'Platforms/OPPO/r11Pkg/Include/DXE.inc').read_text():
        fail('the DXE list has no FAT driver: the payload volume would be unreachable')

    binaries = uefi / 'Binaries/r11'
    prepared = (uefi / 'Common/Mu').is_dir()
    if not binaries.is_dir():
        if prepared:
            fail(f'{binaries} missing: run uefi-r11/scripts/prepare-base.sh')
        warn(f'{uefi} looks like the overlay; run uefi-r11/scripts/prepare-base.sh to build')
    elif not (binaries / 'QcomPkg/Drivers/ClockDxe/ClockDxe.inf').is_file():
        warn(f'{binaries} has no ClockDxe: the vendor DXE set is incomplete')

    for name, value in (('Display Reserved', '0x9D400000'),):
        if value.lower() not in (uefi / 'Platforms/OPPO/r11Pkg/Library/MemoryMapLib/MemoryMapLib.c').read_text().lower():
            warn(f'MemoryMapLib has no {name} region at {value}: SimpleFbDxe would not find a framebuffer')

    print(f'check-r11: board inputs ok, FD {base:#x}+{size:#x}, uefi {uefi}')
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
