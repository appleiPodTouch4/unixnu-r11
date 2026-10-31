"""Minimal flattened-device-tree (DTB) reader and DTS dumper.

Only what the r11 input extractor needs: parse the structure block, walk nodes,
read typed properties and print a reference DTS. No writing, no dtc dependency
(the macOS host may not have dtc installed).
"""
import struct

FDT_MAGIC = 0xD00DFEED
BEGIN_NODE, END_NODE, PROP, NOP, END = 1, 2, 3, 4, 9


class Node:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.props = []          # [(name, bytes)]
        self.children = []

    def get(self, name, default=None):
        for key, value in self.props:
            if key == name:
                return value
        return default

    def child(self, path):
        node = self
        for part in [p for p in path.split('/') if p]:
            node = next((c for c in node.children if c.name == part or c.name.split('@')[0] == part), None)
            if node is None:
                return None
        return node

    def walk(self, prefix=''):
        yield prefix or '/', self
        for child in self.children:
            yield from child.walk(f'{prefix}/{child.name}')


def parse(blob):
    magic, total, off_struct, off_strings, _, version, _, _, size_strings, size_struct = \
        struct.unpack_from('>10I', blob, 0)
    if magic != FDT_MAGIC or total > len(blob):
        raise ValueError('not a flattened device tree')
    strings = blob[off_strings:off_strings + size_strings]
    pos, end = off_struct, off_struct + size_struct
    root, current = None, None
    while pos < end:
        tag, = struct.unpack_from('>I', blob, pos)
        pos += 4
        if tag == BEGIN_NODE:
            stop = blob.index(b'\0', pos)
            node = Node(blob[pos:stop].decode('latin-1'), current)
            if current is None:
                root = node
            else:
                current.children.append(node)
            current = node
            pos = (stop + 4) & ~3
        elif tag == END_NODE:
            current = current.parent
        elif tag == PROP:
            length, name_off = struct.unpack_from('>II', blob, pos)
            pos += 8
            stop = strings.index(b'\0', name_off)
            current.props.append((strings[name_off:stop].decode(), blob[pos:pos + length]))
            pos = (pos + length + 3) & ~3
        elif tag == NOP:
            continue
        elif tag == END:
            break
        else:
            raise ValueError(f'bad FDT tag {tag} at {pos - 4:#x}')
    if root is None:
        raise ValueError('empty device tree')
    return root, {'total': total, 'version': version, 'size_strings': size_strings, 'size_struct': size_struct}


def cells(value):
    return list(struct.unpack(f'>{len(value) // 4}I', value))


def text_of(value):
    return [part.decode('latin-1') for part in value.split(b'\0') if part]


def as_text(value):
    if not value or not value.endswith(b'\0'):
        return None
    parts = text_of(value)
    return parts if parts and all(all(0x20 <= ord(c) < 0x7F for c in part) for part in parts) else None


def fmt(value):
    """Readable form: string, list of strings, or 32-bit cells in hex."""
    if value is None or isinstance(value, (str, list)):
        return value
    strings = as_text(value)
    if strings:
        return strings[0] if len(strings) == 1 else strings
    if value and len(value) % 4 == 0:
        return [f'{cell:#x}' for cell in cells(value)]
    return value.hex()


def addr_size(value, address_cells=2, size_cells=2):
    """Decode a reg-style property into [(address, size)]."""
    words = cells(value)
    stride = address_cells + size_cells
    out = []
    for index in range(0, len(words) - stride + 1, stride):
        address = 0
        for word in words[index:index + address_cells]:
            address = (address << 32) | word
        size = 0
        for word in words[index + address_cells:index + stride]:
            size = (size << 32) | word
        out.append((address, size))
    return out


def split_multi_dtb(blob):
    """Split Qualcomm's concatenated (multi-DTB) blob into members."""
    members, pos = [], 0
    while pos + 8 <= len(blob):
        magic, total = struct.unpack_from('>II', blob, pos)
        if magic != FDT_MAGIC or total == 0 or pos + total > len(blob):
            break
        members.append(blob[pos:pos + total])
        pos += total
        while pos < len(blob) and blob[pos] == 0:
            pos += 1
    return members


def dts_value(value):
    strings = as_text(value)
    if strings:
        return ' , '.join(f'"{s}"' for s in strings) if len(strings) > 1 else f'"{strings[0]}"'
    if not value:
        return '<0>'
    if len(value) % 4 == 0:
        return '<' + ' '.join(f'{cell:#x}' for cell in cells(value)) + '>'
    return '[' + ' '.join(f'{byte:02x}' for byte in value) + ']'


def to_dts(root):
    lines = ['/dts-v1/;', '', f'// {fmt(root.get("model")) or "device tree"}',
             f'// compatible: {fmt(root.get("compatible"))}', '']

    def emit(node, depth, label):
        pad = '\t' * depth
        lines.append(f'{pad}{label} {{' if label else f'{pad}/ {{')
        for name, value in node.props:
            lines.append(f'{pad}\t{name} = {dts_value(value)};')
        for child in node.children:
            emit(child, depth + 1, child.name)
        lines.append(f'{pad}}};')

    emit(root, 0, '')
    return '\n'.join(lines) + '\n'
