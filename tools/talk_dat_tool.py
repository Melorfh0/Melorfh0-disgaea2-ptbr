"""Extract and patch UTF-8 text candidates framed by 0x01 and 0x00.

The extractor preserves U+3000 and U+00A0 spaces. The default patcher accepts
same-byte-length replacements; --allow-resize is experimental, shifts following
bytes, and updates detected absolute 24-bit text references plus segment-30
16-bit offsets. It does not update unproven external metadata and is not yet a
complete record or archive repacker.
"""
from pathlib import Path
import argparse, json, re

FRAME=re.compile(b'(?=(\x01([^\x00]+)\x00))')

def extract(source: Path, destination: Path):
    data=source.read_bytes(); rows=[]
    for m in FRAME.finditer(data):
        payload=m.group(2)
        try: text=payload.decode('utf-8')
        except UnicodeDecodeError: continue
        if len(text)<4 or not all(c.isprintable() or c in '\r\n\t\u3000\u00a0' for c in text): continue
        offset=m.start()+1; end=offset+len(payload)
        rows.append({'index':len(rows),'record_offset':m.start(),'offset':offset,
                     'end_offset':end,'byte_length':len(payload),'text':text})
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    return rows

def rebuild(source: Path, replacements: Path, destination: Path, allow_resize=False):
    original=source.read_bytes(); patches=[]
    for line in replacements.read_text(encoding='utf-8').splitlines():
        if not line.strip(): continue
        row=json.loads(line)
        new_text=row.get('translation') or row.get('text')
        if not new_text or new_text==row.get('original',row.get('text')): continue
        start=int(row.get('offset',row.get('payload_offset'))); end=int(row['end_offset'])
        if start<1 or end>=len(original) or original[start-1:start]!=b'\x01' or original[end:end+1]!=b'\x00':
            raise ValueError(f"0x{start:x}: expected 01/text/00 framing")
        expected=row.get('original',row.get('text'))
        if expected is not None and original[start:end].decode('utf-8')!=expected:
            raise ValueError(f"0x{start:x}: source text does not match the inventory")
        encoded=str(new_text).encode('utf-8')
        if not allow_resize and len(encoded)!=end-start:
            raise ValueError(f"0x{start:x}: replacement must be exactly {end-start} bytes (or pass --allow-resize)")
        patches.append((start,end,encoded))
    patches.sort()
    for left,right in zip(patches,patches[1:]):
        if left[1]>right[0]: raise ValueError('Overlapping replacements')
    adjusted_pointers=0
    if allow_resize:
        # Rebuild from left to right so every source offset remains anchored to
        # the original input, while following data shifts by the cumulative delta.
        chunks=[]; cursor=0
        for start,end,encoded in patches:
            chunks.extend((original[cursor:start],encoded)); cursor=end
        chunks.append(original[cursor:])
        result=bytearray(b''.join(chunks))

        # These DATs use packed little-endian 24-bit absolute references to
        # framed text boundaries. Find references to candidate record starts,
        # payload starts, and terminators, then shift both targets and pointer
        # locations by the edits. Keep pointer detection conservative: only
        # values that exactly match a boundary in this source file are touched.
        boundaries=set(); spans=[]
        for m in FRAME.finditer(original):
            payload=m.group(2)
            try: text=payload.decode('utf-8')
            except UnicodeDecodeError: continue
            if len(text)<4 or not all(c.isprintable() or c in '\r\n\t\u3000\u00a0' for c in text): continue
            record=m.start(); start=m.start()+1; end=start+len(payload)
            boundaries.update((record,start,end)); spans.append((record,end+1))

        protected=bytearray(len(original))
        for a,b in spans: protected[a:b]=b'\x01'*(b-a)
        sites=[]
        for pos in range(len(original)-2):
            if protected[pos]: continue
            value=original[pos] | (original[pos+1]<<8) | (original[pos+2]<<16)
            if value in boundaries: sites.append((pos,value))
        sites.sort()
        for (left,_),(right,_) in zip(sites,sites[1:]):
            if right<left+3: raise ValueError(f'Overlapping 24-bit pointer candidates at 0x{left:x} and 0x{right:x}')

        def shifted(value):
            delta=0
            for start,end,encoded in patches:
                if value < start: break
                if value < end: # Only the span start is unambiguous within edited text.
                    if value==start: return value+delta
                    raise ValueError(f'Pointer targets inside edited text at 0x{value:x}; cannot remap safely')
                delta += len(encoded)-(end-start)
            return value+delta

        for pos,value in sites:
            new_pos=shifted(pos)
            new_value=shifted(value)
            if new_value >= 1<<24: raise ValueError(f'24-bit pointer overflow at 0x{value:x}')
            result[new_pos:new_pos+3]=new_value.to_bytes(3,'little')
            if new_value!=value: adjusted_pointers+=1

        # The 32-byte row table also contains segmented 16:16 addresses at
        # +24: low word is a file offset and high word is the segment id.
        # In these talk files, segment 30 points into the DAT body. Shift only
        # offsets after resized spans; other segment values are not understood.
        if len(original)>=16:
            row_count=int.from_bytes(original[:4],'little')
            table_end=16+row_count*32
            if table_end<=len(original):
                for row in range(row_count):
                    pos=16+row*32+24
                    target=int.from_bytes(original[pos:pos+2],'little')
                    segment=int.from_bytes(original[pos+2:pos+4],'little')
                    if segment!=30: continue
                    new_target=shifted(target)
                    if new_target>=1<<16: raise ValueError(f'16-bit segment-30 pointer overflow at 0x{target:x}')
                    if new_target!=target:
                        result[pos:pos+2]=new_target.to_bytes(2,'little')
                        adjusted_pointers+=1
    else:
        result=bytearray(original)
        for start,end,encoded in patches: result[start:end]=encoded
    destination.parent.mkdir(parents=True,exist_ok=True); destination.write_bytes(result)
    return len(patches), adjusted_pointers

def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='cmd',required=True)
    e=sub.add_parser('extract'); e.add_argument('source',type=Path); e.add_argument('jsonl',type=Path)
    b=sub.add_parser('rebuild'); b.add_argument('source',type=Path); b.add_argument('jsonl',type=Path); b.add_argument('output',type=Path)
    b.add_argument('--allow-resize',action='store_true',help='allow variable-length text; bytes after edits shift and file-level metadata is not adjusted')
    args=parser.parse_args()
    if args.cmd=='extract': print(f'Extracted {len(extract(args.source,args.jsonl))} framed text candidates.')
    else:
        applied,pointers=rebuild(args.source,args.jsonl,args.output,args.allow_resize)
        msg=f'Applied {applied} replacements'+(' with resizing' if args.allow_resize else ' at the original byte lengths')
        if args.allow_resize: msg+=f'; adjusted {pointers} internal text offsets/references'
        print(msg+'.')

if __name__=='__main__': main()


