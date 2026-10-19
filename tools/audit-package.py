"""Validate the exact release payload, not just a development tree."""
from pathlib import Path
import json,hashlib,zipfile,io,re,os
from PIL import Image
from fontTools.ttLib import TTFont
from rpk_signature import audit
ROOT=Path(__file__).resolve().parents[1];manifest=json.loads((ROOT/'src/manifest.json').read_text('utf8'))
package=ROOT/'dist'/f'{manifest["package"]}.debug.{manifest["versionName"]}.rpk'
report=audit(package);assert report['bytes']<10485760
z=zipfile.ZipFile(package);assert z.testzip() is None
assert json.loads(z.read('manifest-watch.json'))==manifest
assert json.loads(z.read('manifest.json'))['package']=='com.codex.eden.rw5'
count=0
for name in z.namelist():
    if name.endswith('/'):continue
    if name.startswith('common/'):
        assert (ROOT/'src'/name).read_bytes()==z.read(name),name
    if name.endswith(('.jpg','.png')):
        im=Image.open(io.BytesIO(z.read(name)));im.load();count+=1
        if name.startswith('common/images/'):
            assert (im.size==(432,270) and name.endswith('.png')) or (im.width<=280 and im.height<=512)
            assert not im.info.get('progressive',False)
logo=Image.open(io.BytesIO(z.read('common/logo.png'))).convert('RGBA');assert logo.size==(192,192)
assert all(logo.getpixel(x)[3]==0 for x in [(0,0),(191,0),(0,191),(191,191)])
default=TTFont(Path(os.environ.get('EDEN_DEFAULT_FONT',ROOT.parent/'clannad-probe/native-default-font.ttf'))).getBestCmap()
extra=TTFont(io.BytesIO(z.read('common/eden-extra.otf'))).getBestCmap()
triggers=set(json.loads((ROOT/'reports/text-font.json').read_text('utf8'))['missingDefaultGlyphs'])
strings=[]
def visit(value):
    if isinstance(value,str):strings.append(value.replace('・','·'))
    elif isinstance(value,list):
        for v in value:visit(v)
    elif isinstance(value,dict):
        for v in value.values():visit(v)
for name in z.namelist():
    if name.startswith('common/story/') and name.endswith('.txt'):visit(json.loads(z.read(name)))
assert 'common/gallery.txt' not in z.namelist()
for n in z.namelist():
    if n.startswith('common/gallery/') and n.endswith('.txt'):
        assert len(z.read(n))<16384
        visit(json.loads(z.read(n)))
assert z.read('pages/index/index.js')==(ROOT/'build/pages/index/index.js').read_bytes()
frameSource=(ROOT/'src/common/assets.js').read_text('utf8');frameCatalog=json.loads(frameSource.split('export const frames=',1)[1].split(';\nexport const assets=',1)[0])
nativeCardStrings=[f['card']['text'] for f in frameCatalog.values() if 'card' in f]
compiled=z.read('pages/index/index.js').decode('utf8')
assert all(t in compiled or json.dumps(t,ensure_ascii=True)[1:-1] in compiled for t in nativeCardStrings)
visit(nativeCardStrings)
for text in strings:
    cmap=extra if triggers.intersection(text) else default
    assert all(ch.isspace() or ord(ch)<32 or ord(ch) in cmap for ch in text),text
report.update(decodedImages=count,circularTransparentIcon=True,allCommonResourcesMatch=True,watchManifestCorrect=True,textGlyphCoverage=True,baselineJPEG=True,physicalDeviceTested=False)
(ROOT/'reports/package-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
