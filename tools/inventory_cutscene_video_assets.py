from __future__ import annotations

import hashlib
import json
import mmap
import struct
import zipfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "work" / "game_probe"
OUTPUT = ROOT / "outputs" / "cutscene_video_asset_inventory.json"
VIDEO_SUFFIXES = {".ogm", ".ogg", ".ogv", ".avi", ".mpg", ".mpeg", ".mp4", ".mkv", ".bik", ".usm", ".wmv", ".mov"}
NISPACK_MAGIC = b"NISPACK\0"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def list_nispack_members(path: Path) -> list[dict]:
    results: list[dict] = []
    with path.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        cursor = 0
        while True:
            table = data.find(NISPACK_MAGIC, cursor)
            if table < 0:
                break
            cursor = table + 1
            if table + 16 > len(data):
                continue
            count = struct.unpack_from("<I", data, table + 12)[0]
            if not 0 < count <= 4096 or table + 16 + count * 44 > len(data):
                continue
            members = []
            valid = True
            for index in range(count):
                row = table + 16 + index * 44
                raw_name = bytes(data[row:row + 32]).split(b"\0", 1)[0]
                if not raw_name or any(byte < 32 or byte > 126 for byte in raw_name):
                    valid = False
                    break
                name = raw_name.decode("ascii")
                relative, size, _tag = struct.unpack_from("<III", data, row + 32)
                if table + relative + size > len(data):
                    valid = False
                    break
                members.append(name)
            if valid:
                results.append({"table_offset": table, "member_count": count, "members": members})
    return results


def read_ogm_summary(path: Path) -> dict:
    with path.open("rb") as stream:
        header = stream.read(64)
    return {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "first_page_signature": header[:4].decode("ascii", errors="replace"),
        "theora_identification_marker_present": b"\x80theora" in header,
        "header_hex": header.hex(" "),
    }


def scan_ogg_pages(path: Path) -> dict:
    starts = []
    page_count = 0
    with path.open("rb") as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        cursor = 0
        while True:
            pos = data.find(b"OggS", cursor)
            if pos < 0:
                break
            cursor = pos + 4
            if pos + 27 > len(data) or data[pos + 4] != 0:
                continue
            segment_count = data[pos + 26]
            table_end = pos + 27 + segment_count
            if table_end > len(data):
                continue
            lacing = data[pos + 27:table_end]
            page_size = 27 + segment_count + sum(lacing)
            if pos + page_size > len(data):
                continue
            page_count += 1
            header_type = data[pos + 5]
            serial = struct.unpack_from("<I", data, pos + 14)[0]
            sequence = struct.unpack_from("<I", data, pos + 18)[0]
            # The initial identification packet is on the BOS page for common Ogg codecs.
            first_packet = b""
            if header_type & 0x02:
                payload = bytes(data[table_end:pos + page_size])
                take = 0
                for size in lacing:
                    first_packet += payload[take:take + size]
                    take += size
                    if size < 255:
                        break
                marker = next((label for raw, label in ((b"\x80theora", "Theora"), (b"\x01vorbis", "Vorbis"), (b"\x01\x7fFLAC", "FLAC"), (b"OpusHead", "Opus"), (b"Speex", "Speex"), (b"fishead", "Ogg Skeleton")) if raw in first_packet), "unrecognized")
                starts.append({
                    "offset": pos,
                    "serial": serial,
                    "sequence": sequence,
                    "codec_marker": marker,
                })
    counts = Counter(item["codec_marker"] for item in starts)
    samples = []
    sampled = Counter()
    for item in starts:
        if sampled[item["codec_marker"]] < 4:
            samples.append(item)
            sampled[item["codec_marker"]] += 1
    return {
        "validated_page_count": page_count,
        "beginning_of_stream_count": len(starts),
        "beginning_of_stream_counts_by_codec": dict(counts),
        "sample_headers": samples,
    }


def main() -> None:
    loose_media = []
    for path in sorted(GAME.rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES:
            loose_media.append(read_ogm_summary(path) if path.suffix.lower() == ".ogm" else {
                "path": str(path), "size_bytes": path.stat().st_size, "sha256": sha256(path), "extension": path.suffix
            })

    zip_path = GAME / "Disgaea2.zip"
    zip_media = []
    with zipfile.ZipFile(zip_path) as archive:
        for item in archive.infolist():
            suffix = Path(item.filename).suffix.lower()
            if suffix in VIDEO_SUFFIXES:
                zip_media.append({"name": item.filename, "size_bytes": item.file_size, "extension": suffix})

    data_members = {name: list_nispack_members(GAME / name) for name in ("DATA.DAT", "SUB_DATA.DAT")}
    result = {
        "experiment": "Read-only inventory of standalone and archived video assets for Disgaea 2 PC",
        "game_directory": str(GAME),
        "standalone_video_assets": loose_media,
        "video_assets_named_inside_clone_zip": zip_media,
        "nispack_archive_member_extensions": {
            "DATA.DAT": sorted({Path(member).suffix.lower() for table in data_members["DATA.DAT"] for member in table["members"]}),
            "SUB_DATA.DAT": sorted({Path(member).suffix.lower() for table in data_members["SUB_DATA.DAT"] for member in table["members"]}),
        },
        "nispack_tables": data_members,
        "ogg_streams_in_main_archives": {},
        "interpretation": "The clone folder contains two loose Ogg/Theora videos. No additional movie/video extension was found in the clone ZIP listing or the validated NISPACK member names. Valid Ogg pages found in the archives are inventoried separately by codec marker. This does not rule out real-time, in-engine scenes assembled from map, animation, and dialogue resources.",
        "official_installation_modified": False,
        "source_files_modified": False,
    }

    # Check for valid Ogg pages and codec headers in the main archives without extraction or modification.
    for name in ("DATA.DAT", "SUB_DATA.DAT"):
        result["ogg_streams_in_main_archives"][name] = scan_ogg_pages(GAME / name)

    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"standalone_video_files={len(loose_media)}; zip_video_entries={len(zip_media)}; report={OUTPUT}")
    print("loose=" + ", ".join(Path(item["path"]).name for item in loose_media))
    print("archive_members=" + json.dumps(result["nispack_archive_member_extensions"]))
    print("ogg_streams=" + json.dumps({name: {"pages": value["validated_page_count"], "streams": value["beginning_of_stream_counts_by_codec"], "samples": value["sample_headers"]} for name, value in result["ogg_streams_in_main_archives"].items()}))


if __name__ == "__main__":
    main()

