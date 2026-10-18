from pathlib import Path
from collections import Counter
import hashlib, json, re

ROOT=Path(__file__).resolve().parent
INP=ROOT/'inputs'
OUT=ROOT/'analysis'
OUT.mkdir(exist_ok=True)

def printable(b):
    try: s=b.decode('utf-8')
    except UnicodeDecodeError: return False
    # U+3000 IDEOGRAPHIC SPACE is the game's visible word separator.
    return all(c.isprintable() or c in '\r\n\t\u3000\u00a0' for c in s)

def spans(data):
    # Overlapping candidates framed by 0x01 ... 0x00, preserving source offsets.
    result=[]
    for m in re.finditer(b'(?=(\x01([^\x00]{1,})\x00))',data):
        p=m.group(2)
        if printable(p) and len(p.decode('utf-8'))>=4: result.append((m.start(),m.start()+1,m.start()+len(m.group(1))-1,p))
    return result

def main():
    report=[]
    for path in sorted(INP.glob('talk*.dat')):
        data=path.read_bytes(); ss=spans(data); count=int.from_bytes(data[:4],'little')
        deltas=[ss[i+1][0]-ss[i][0] for i in range(len(ss)-1)]
        rec={'file':path.name,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
             'header_count_u32':count,'table_end_if_32_byte_rows':16+count*32,
             'candidate_spans':len(ss),'unique_payloads':len(set(x[3] for x in ss)),
             'first16':[(x[0],x[3][:80].decode('utf-8','replace')) for x in ss[:16]],
             'delta_top':Counter(deltas).most_common(12),'prefix_hex':data[:64].hex(' ')}
        report.append(rec)
        with (OUT/f'{path.stem}.strings.jsonl').open('w',encoding='utf-8') as f:
            for i,(start,begin,end,p) in enumerate(ss):
                f.write(json.dumps({'index':i,'offset':start,'payload_offset':begin,'end_offset':end,
                                    'text':p.decode('utf-8')},ensure_ascii=False)+'\n')
    (OUT/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for r in report:
        print(f"{r['file']}: {r['size']} bytes; header={r['header_count_u32']}; 01..00 candidates={r['candidate_spans']}; assumed table end=0x{r['table_end_if_32_byte_rows']:x}")

    # No-op rebuild plus an isolated equal-byte-length edit probe.
    probes=OUT/'repack_probe'; probes.mkdir(exist_ok=True)
    src=INP/'talk01.dat'; original=src.read_bytes()
    roundtrip=probes/'talk01_roundtrip.dat'; roundtrip.write_bytes(original)
    if roundtrip.read_bytes()!=original: raise RuntimeError('no-op roundtrip differs')
    needle=b'Please'; pos=original.find(needle)
    if pos<0: raise RuntimeError('probe word not found')
    patched=bytearray(original); patched[pos:pos+len(needle)]=b'PR0BE!'
    probe=probes/'talk01_probe.dat'; probe.write_bytes(patched)
    rebuilt=probe.read_bytes()
    valid=(len(rebuilt)==len(original) and rebuilt[:pos]==original[:pos] and
           rebuilt[pos:pos+len(needle)]==b'PR0BE!' and rebuilt[pos+len(needle):]==original[pos+len(needle):])
    if not valid: raise RuntimeError('equal-length patch validation failed')
    validation={'no_op_roundtrip':'byte-identical','probe_file':probe.name,'probe_offset':pos,
                 'before':'Please','after':'PR0BE!','same_size':True,'only_probe_span_changed':True}
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
    print(f"Validation: exact no-op copy; 6-byte probe edit at 0x{pos:x}; unchanged size and all other bytes.")

if __name__=='__main__': main()

