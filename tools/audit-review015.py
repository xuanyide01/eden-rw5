"""Audit the exact v0.1.5 payload against the previously tested v0.1.4 RPK."""
from pathlib import Path
from functools import lru_cache
from collections import Counter
import hashlib
import json
import sys
import zipfile
from gallery_dedupe import load_gallery_frames

root = Path(__file__).resolve().parents[1]
common = root / 'src/common'
before, after = (Path(s) for s in sys.argv[1:3])
report = json.loads((root / 'reports/gallery-deduplication.json').read_text('utf8'))

def paged(archive):
    names = sorted((n for n in archive.namelist() if n.startswith('common/gallery/') and n.endswith('.txt')), key=lambda n: int(Path(n).stem))
    assert [int(Path(n).stem) for n in names] == list(range(len(names)))
    return [group for name in names for group in json.loads(archive.read(name))]

def immutable_common(archive):
    return {n: hashlib.sha256(archive.read(n)).hexdigest() for n in archive.namelist()
            if n.startswith('common/') and not n.endswith('/') and not n.startswith(('common/gallery/', 'common/gallery-preview/'))}

picture = load_gallery_frames(common)

@lru_cache(maxsize=None)
def key(name):
    im = picture(name)
    return im.size, hashlib.sha256(im.tobytes()).hexdigest()

with zipfile.ZipFile(before) as old, zipfile.ZipFile(after) as new:
    assert old.testzip() is None and new.testzip() is None
    old_fixed = immutable_common(old)
    assert old_fixed == immutable_common(new), 'Unrelated packaged resources changed'
    for name, digest in old_fixed.items():
        assert hashlib.sha256((root / 'src' / name).read_bytes()).hexdigest() == digest, name
    a, b = json.loads(old.read('manifest-watch.json')), json.loads(new.read('manifest-watch.json'))
    assert (a.pop('versionName'), a.pop('versionCode')) == ('0.1.4', 5)
    assert (b.pop('versionName'), b.pop('versionCode')) == ('0.1.5', 6)
    assert a == b, 'Application identity or platform features changed'
    old_groups, new_groups = paged(old), paged(new)
    old_frames = [key(frame) for group in old_groups for frame in group['images']]
    new_frames = [key(frame) for group in new_groups for frame in group['images']]
    assert (len(old_frames), len(new_frames), len(old_groups), len(new_groups)) == (2341, 2075, 295, 294)
    assert list(dict.fromkeys(old_frames)) == new_frames, 'A distinct image was omitted, added or reordered'
    hashes = Counter(hashlib.sha256(new.read(i)).hexdigest() for i in new.infolist() if not i.is_dir())
    assert max(hashes.values()) == 1, 'Duplicate package payloads'
    package_audit = json.loads((root / 'reports/package-audit.json').read_text('utf8'))
    package_hash = hashlib.sha256(after.read_bytes()).hexdigest()
    assert package_audit['sha256'] == package_hash
    report.update(version='0.1.5', packageSHA256=package_hash, baselineSHA256=hashlib.sha256(before.read_bytes()).hexdigest(),
                  unchangedApplicationID=b['package'], unchangedNonGalleryResources=len(old_fixed),
                  unchangedStoryChunks=sum(n.startswith('common/story/') for n in old_fixed),
                  identicalDistinctPictureSetAndOrder=True, duplicatePackagedFiles=0,
                  physicalDeviceTested=False, platformReviewPassed=None)
(root / 'reports/review-verification015.json').write_text(json.dumps({k:v for k,v in report.items() if k!='removed'}, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps({k:v for k,v in report.items() if k!='removed'}, ensure_ascii=False))
