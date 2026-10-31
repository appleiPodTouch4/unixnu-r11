#!/usr/bin/env python3
"""Extract OPPO R11 (r11, CPH1707 / 16051) board inputs from a stock OFP package.

Reads the stock boot image's appended multi-DTB and the GPT images, then writes
the evidence the device repository and the UEFI platform build are derived from:

    inputs/r11-stock.dtb     device tree the stock ABL hands to the kernel,
                             and the firmware DTB for "unixnu bootimg --dtb"
    inputs/r11-stock.dts     readable dump of the same tree (reference only)
    inputs/hw.json           board values: memory, CPUs, reserved memory,
                             peripherals, panel, touch, boot image geometry
    inputs/partitions.json   GPT partitions of both LUNs

Usage:
    python3 scripts/extract-inputs.py --ofp ../ofp_extracted
    python3 scripts/extract-inputs.py --ofp ../ofp_extracted --board-id 0x3eb3
"""
import argparse
import json
import struct
import sys
import zlib
from pathlib import Path

import fdt

HERE = Path(__file__).resolve().parent
DEFAULT_BOARD_ID = 0x3EB3          # R11 / 16051: qcom,board-id = <0x8 0x0 0x3eb3>


def parse_boot_image(path):
    """Android boot image header version 0/1/2 -> fields plus the kernel payload."""
    data = Path(path).read_bytes()
    if data[:8] != b'ANDROID!':
        raise SystemExit(f'{path}: not an Android boot image')
    fields = struct.unpack_from('<10I', data, 8)
    (kernel_size, kernel_addr, ramdisk_size, ramdisk_addr, second_size,
     second_addr, tags_addr, page_size, header_version, os_version) = fields
    if header_version not in (0, 1, 2):
        raise SystemExit(f'{path}: unsupported boot image header version {header_version}')
    name = data[48:64].split(b'\0')[0].decode('latin-1')
    cmdline = data[64:64 + 512].split(b'\0')[0].decode('latin-1')
    return {
        'path': str(path), 'header_version': header_version, 'page_size': page_size,
        'kernel_size': kernel_size, 'kernel_addr': kernel_addr,
        'ramdisk_size': ramdisk_size, 'ramdisk_addr': ramdisk_addr,
        'second_size': second_size, 'second_addr': second_addr,
        'tags_addr': tags_addr, 'board_name': name, 'cmdline': cmdline,
        'image_bytes': len(data), 'kernel': data[page_size:page_size + kernel_size],
    }


def split_kernel(kernel):
    """gzip(Image) + multi-DTB blob -> (image bytes, [dtb members])."""
    stream = zlib.decompressobj(16 + zlib.MAX_WBITS)
    image = stream.decompress(kernel)
    trailer = stream.unused_data
    if not stream.eof:
        raise SystemExit('kernel field is not a complete gzip member; not an Image.gz+dtb image')
    members = fdt.split_multi_dtb(trailer) if trailer[:4] == b'\xd0\x0d\xfe\xed' else []
    return image, members


def identity(blob):
    root, info = fdt.parse(blob)
    board_id = fdt.cells(root.get('qcom,board-id') or b'')
    msm_id = fdt.cells(root.get('qcom,msm-id') or b'')
    return {'board_id': board_id, 'msm_id': msm_id, 'model': fdt.fmt(root.get('model')),
            'compatible': fdt.fmt(root.get('compatible')), 'bytes': len(blob)}, root, info


def cell_counts(node):
    """#address-cells / #size-cells of a node's parent (reg is encoded in those units)."""
    parent = node.parent or node
    address = parent.get('#address-cells')
    size = parent.get('#size-cells')
    return (fdt.cells(address)[0] if address else 2, fdt.cells(size)[0] if size else 2)


def regs_of(node):
    value = node.get('reg') if node is not None else None
    if not value:
        return []
    address_cells, size_cells = cell_counts(node)
    return [(f'{address:#x}', f'{size:#x}')
            for address, size in fdt.addr_size(value, address_cells, size_cells)]


def collect(root, boot):
    def prop(path, *names):
        node = root.child(path)
        return {name: fdt.fmt(node.get(name)) for name in names} if node is not None else None

    memory = root.child('memory')
    banks = regs_of(memory)
    cpus = root.child('cpus') or root.child('cpus/cpu-map')
    cpu_list = []
    usage = root.child('cpus')
    if usage is not None:
        for child in usage.children:
            if child.name.startswith('cpu@'):
                cpu_list.append({'node': child.name, 'reg': fdt.fmt(child.get('reg')),
                                 'compatible': fdt.fmt(child.get('compatible'))})

    reserved = []
    region = root.child('reserved-memory')
    if region is not None:
        for child in region.children:
            entries = regs_of(child)
            reserved.append({'node': child.name, 'reg': entries,
                             'no_map': child.get('no-map') is not None})

    peripherals = {}
    soc = root.child('soc')
    if soc is not None:
        for child in soc.children:
            key = child.name.split('@')[0]
            if key in ('sdhci', 'uart', 'i2c', 'clock-controller', 'pinctrl', 'spmi', 'qcom,mdss_mdp',
                       'interrupt-controller', 'timer', 'qcom,kgsl-3d0', 'arm,smmu-mmss', 'qcom,smem',
                       'qcom,icnss', 'qcom,msm-imem'):
                peripherals.setdefault(key, []).append({
                    'node': child.name, 'compatible': fdt.fmt(child.get('compatible')),
                    'reg': regs_of(child), 'status': fdt.fmt(child.get('status'))})

    buses = {}
    if soc is not None:
        for child in soc.children:
            if child.name.startswith('i2c@'):
                devices = []
                for device in child.children:
                    devices.append({'node': device.name, 'compatible': fdt.fmt(device.get('compatible'))})
                buses[child.name] = {'reg': regs_of(child), 'devices': devices}

    panel = None
    mdp = root.child('soc/qcom,mdss_mdp@c900000')
    if mdp is not None:
        chosen = [c for c in mdp.children if 'oppo16051' in c.name] or \
                 [c for c in mdp.children if 's6e3fa3' in c.name]
        if chosen:
            node = chosen[0]
            panel = {'node': node.name,
                     'name': fdt.fmt(node.get('qcom,mdss-dsi-panel-name')),
                     'width': fdt.fmt(node.get('qcom,mdss-dsi-panel-width')),
                     'height': fdt.fmt(node.get('qcom,mdss-dsi-panel-height')),
                     'lanes': fdt.fmt(node.get('qcom,mdss-dsi-lane-0-state')),
                     'fps': fdt.fmt(node.get('qcom,mdss-dsi-panel-framerate')),
                     'panel_type': fdt.fmt(node.get('qcom,mdss-dsi-panel-type')),
                     'properties': len(node.props)}

    return {
        'model': fdt.fmt(root.get('model')),
        'compatible': fdt.fmt(root.get('compatible')),
        'memory': {'banks': banks,
                   'dram_base': banks[0][0] if banks else None,
                   'dram_size_total': sum(int(size, 16) for _, size in banks)},
        'cpus': cpu_list,
        'timebase_frequency': fdt.fmt(root.child('timer') .get('clock-frequency')) if root.child('timer') else None,
        'reserved_memory': reserved,
        'peripherals': peripherals,
        'i2c': buses,
        'panel': panel,
        'chosen_bootargs': fdt.fmt(root.child('chosen').get('bootargs')) if root.child('chosen') else None,
        'boot_image': {key: (f'{value:#x}' if isinstance(value, int) else value)
                       for key, value in boot.items() if key != 'kernel'},
    }


def parse_gpt(path):
    data = Path(path).read_bytes()
    header = None
    for offset in (512, 4096, 0):
        if data[offset:offset + 8] == b'EFI PART':
            header = offset
            break
    if header is None:
        return None
    (_, _, header_size, _, _, _, _, _, _, _, entry_lba, entry_count,
     entry_size, _) = struct.unpack_from('<8sIIIIQQQQ16sQIII', data, header)
    base = entry_lba * 512 if entry_lba * 512 + entry_count * entry_size <= len(data) else header + header_size
    partitions = []
    for index in range(entry_count):
        entry = data[base + index * entry_size:base + (index + 1) * entry_size]
        if len(entry) < 128 or entry[:16] == b'\0' * 16:
            continue
        first_lba, last_lba, attributes = struct.unpack_from('<QQQ', entry, 32)
        name = entry[56:128].decode('utf-16-le').split('\0')[0]
        # A grow partition (userdata, last_grow) is encoded with last_lba < first_lba,
        # i.e. zero sectors: the size is only known once the eMMC size is known.
        sectors = last_lba - first_lba + 1 if last_lba >= first_lba else 0
        partitions.append({'index': index + 1, 'name': name, 'first_lba': first_lba,
                           'last_lba': last_lba if sectors else None, 'grow': sectors == 0,
                           'sectors': sectors, 'bytes': sectors * 512,
                           'attributes': f'{attributes:#x}'})
    return {'path': str(path), 'entry_count': entry_count, 'partitions': partitions}


def choose(members, wanted):
    identities = []
    for blob in members:
        info, root, _ = identity(blob)
        info['blob'] = blob
        identities.append(info)
    for item in identities:
        if item['board_id'] and item['board_id'][-1] == wanted:
            return item, identities
    return identities[0], identities


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--ofp', required=True, help='extracted OFP directory')
    parser.add_argument('--boot', default='boot.img', help='stock boot image inside --ofp')
    parser.add_argument('--board-id', type=lambda text: int(text, 0), default=DEFAULT_BOARD_ID,
                        help='qcom,board-id subtype to select (default 0x3eb3, R11/16051)')
    parser.add_argument('--out', default=str(HERE.parent / 'inputs'), help='output directory')
    args = parser.parse_args()

    ofp = Path(args.ofp)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    boot = parse_boot_image(ofp / args.boot)
    image, members = split_kernel(boot.pop('kernel'))
    if not members:
        raise SystemExit('no appended device tree in the boot image')
    chosen, identities = choose(members, args.board_id)
    print(f'kernel: {len(image)} bytes uncompressed, {len(members)} appended DTBs')
    for item in identities:
        mark = '*' if item is chosen else ' '
        print(f' {mark} board-id {[hex(v) for v in item["board_id"]]} '
              f'msm-id {[hex(v) for v in item["msm_id"]]} {item["bytes"]} bytes'
              f'  {item["model"]}')

    (out / 'r11-stock.dtb').write_bytes(chosen['blob'])
    root, info = fdt.parse(chosen['blob'])
    (out / 'r11-stock.dts').write_text(fdt.to_dts(root))

    hardware = collect(root, boot)
    if hardware['memory']['dram_size_total'] == 0:
        hardware['memory']['note'] = ('the stock tree zeroes /memory reg; ABL patches it from SMEM at boot. '
                                      'dram_size_total is taken from the measured 4 GiB unit (0xFE4C0000).')
        hardware['memory']['dram_base'] = '0x80000000'
        hardware['memory']['dram_size_total'] = 0xFE4C0000
        hardware['memory']['banks'] = [['0x80000000', '0x80000000'], ['0x100000000', '0x7E4C0000']]
    hardware['device_tree'] = {'board_id': chosen['board_id'], 'msm_id': chosen['msm_id'],
                               'members': len(members), 'bytes': chosen['bytes'],
                               'version': info['version']}
    hardware['gpt'] = {}
    for name in ('gpt_main0.bin', 'gpt_main2.bin'):
        if (ofp / name).is_file():
            table = parse_gpt(ofp / name)
            if table:
                hardware['gpt'][name] = table
    (out / 'hw.json').write_text(json.dumps(hardware, indent=2) + '\n')

    partitions = {name: table for name, table in hardware['gpt'].items()}
    if partitions:
        (out / 'partitions.json').write_text(json.dumps(partitions, indent=2) + '\n')

    print('\nmemory:', hardware['memory']['dram_base'], hardware['memory']['dram_size_total'])
    print('cpus:', len(hardware['cpus']), [c['reg'] for c in hardware['cpus']])
    print('panel:', hardware['panel']['name'] if hardware['panel'] else 'not found')
    i2c = hardware['i2c']
    touch = next((d for bus in i2c.values() for d in bus['devices'] if 'synaptics' in (d['node'] or '')), None)
    print('touch:', touch['node'] if touch else 'not found')
    for name, table in partitions.items():
        names = {p['name']: p for p in table['partitions']}
        boot_part = names.get('boot')
        user = names.get('userdata')
        print(f'{name}: {len(names)} partitions', end='')
        if boot_part:
            print(f", boot {boot_part['bytes'] / 2**20:.0f} MiB", end='')
        if user:
            span = (f"{user['first_lba']}-grow (end depends on the eMMC size)"
                    if user.get('grow') else
                    f"{user['first_lba']}-{user['last_lba']} ({user['bytes'] / 2**30:.1f} GiB)")
            print(f", userdata {span}", end='')
        print()
    print(f'\nwrote {out}/r11-stock.dtb, r11-stock.dts, hw.json and partitions.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
