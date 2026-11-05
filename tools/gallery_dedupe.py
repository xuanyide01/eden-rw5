"""Keep the first occurrence of each identical rendered CG in gallery order."""
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
import hashlib
import json
from PIL import Image


def load_gallery_frames(common):
    source = (common / 'assets.js').read_text('utf8')
    frames = json.loads(source.split('export const frames=', 1)[1].split(';\nexport const assets=', 1)[0])
    tiles = json.loads(source.split('export const tiles=', 1)[1].split(';\n', 1)[0])

    @lru_cache(maxsize=16)
    def atlas(name):
        with Image.open(common / 'images' / name) as im:
            return im.convert('RGB')

    def tile(name):
        t = tiles[name]
        x, y, w, h = t['rect']
        return atlas(t['file']).crop((x, y, x+w, y+h))

    def picture(name):
        f = frames[name]
        assert 'card' not in f, 'Text cards are not CG entries'
        im = tile(f['base'])
        assert list(im.size) == f['size'] and im.width <= 264 and im.height <= 270
        if f.get('patch'):
            patch = tile(f['patch'])
            x, y, w, h = f['box']
            assert patch.size == (w, h) and x >= 0 and y >= 0 and x+w <= im.width and y+h <= im.height
            im.paste(patch, (x, y))
        return im

    return picture


def dedupe_gallery(common, items, reports):
    groups = defaultdict(list)
    for item in items:
        groups[item['group']].append(item)
    picture = load_gallery_frames(common)

    @lru_cache(maxsize=None)
    def fingerprint(frame):
        im = picture(frame)
        return im.size, hashlib.sha256(im.tobytes()).hexdigest()

    seen, kept, removed = {}, [], []
    for group in groups.values():
        local = set()
        for item in group:
            key = fingerprint(item['image'])
            if key in seen:
                removed.append({'source': item['source'], 'frame': item['image'], 'group': item['group'],
                                'keptSource': seen[key]['source'], 'keptFrame': seen[key]['image'],
                                'keptGroup': seen[key]['group'], 'rgbSHA256': key[1], 'size': key[0],
                                'withinGroup': key in local})
            else:
                seen[key] = item
                kept.append(item)
            local.add(key)
    assert len(kept) + len(removed) == len(items)
    kept_groups = {item['group'] for item in kept}
    report = {'method': 'identical width, height and decoded RGB after composing the displayed base and patch',
              'beforeEntries': len(items), 'afterEntries': len(kept), 'removedEntries': len(removed),
              'withinGroupDuplicates': sum(item['withinGroup'] for item in removed),
              'betweenGroupDuplicates': sum(not item['withinGroup'] for item in removed),
              'beforeGroups': len(groups), 'afterGroups': len(kept_groups),
              'removedGroups': [group[0]['label'] for key, group in groups.items() if key not in kept_groups],
              'removed': removed}
    (reports / 'gallery-deduplication.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    return kept


if __name__ == '__main__':
    from gallery_pack import packGallery
    from gallery_thumbnails import build_thumbnails
    root = Path(__file__).resolve().parents[1]
    common, reports = root / 'src/common', root / 'reports'
    before = reports / 'gallery-source-before-dedupe.json'
    source = reports / 'gallery-source.json'
    if not before.exists():
        before.write_bytes(source.read_bytes())
    items = dedupe_gallery(common, json.loads(before.read_text('utf8')), reports)
    source.write_text(json.dumps(items, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    gallery = packGallery(common, items, reports)
    build_thumbnails(root)
    conversion = reports / 'conversion.json'
    report = json.loads(conversion.read_text('utf8'))
    report.update(galleryVariants=gallery['variants'], galleryGroups=gallery['groups'])
    conversion.write_text(json.dumps(report, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    print('GALLERY', gallery['groups'], gallery['variants'])
