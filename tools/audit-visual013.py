from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
for name,sha in json.loads((ROOT/'reports/title-baseline013.json').read_text('utf8')).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
assert hashlib.sha256((ROOT/'reports/source-text-proof.json').read_bytes()).hexdigest()=='98dabb0568a9e5179e4c4256101ce202cd231dc1815663da56bb0100f3639d01'
report=json.loads((ROOT/'reports/gallery-memory.json').read_text('utf8'));assert report['groups']==295 and report['variants']==2341 and report['listImageWidgets']==1 and report['maxReadBytes']<16384
items=json.loads((ROOT/'reports/gallery-source.json').read_text('utf8'));assert len(items)==2341
all_images=[]
for page in range(report['pages']):
 p=ROOT/'src/common/gallery'/(str(page)+'.txt');assert p.stat().st_size<=report['maxReadBytes']
 for g in json.loads(p.read_text('utf8')):all_images+=g['images']
assert all_images==[i['image'] for i in items]
assert not (ROOT/'src/common/gallery.txt').exists()
logo=Image.open(ROOT/'src/common/logo.png').convert('RGBA');assert logo.size==(192,192);assert all(logo.getpixel(p)[3]==0 for p in [(0,0),(191,0),(0,191),(191,191)])
icon=json.loads((ROOT/'reports/icon013.json').read_text('utf8'));assert icon['originalPixelsUsed'] and not icon['generatedPreviewUsed']
ux=(ROOT/'src/pages/index/index.ux').read_text('utf8');gallery=ux.split("mode === 'gallery'")[1].split("mode === 'cg'")[0];assert gallery.count('<image ')==1 and 'gallery-sheet' in gallery;assert 'galleryTop' in ux and '_galleryCatalog' not in ux
previews=json.loads((ROOT/'reports/gallery-thumbnails.json').read_text('utf8'));assert previews['pageCount']==report['pages'] and previews['thumbnailImageWidgetsPerPage']==1
for i,p in enumerate(previews['pages']):
 data=(ROOT/'src/common/gallery-preview'/p['file']).read_bytes();assert hashlib.sha256(data).hexdigest()==p['sha256'];im=Image.open(ROOT/'src/common/gallery-preview'/p['file']);im.load();assert im.size==(198,184) and not im.info.get('progressive',False)
 groups=json.loads((ROOT/'src/common/gallery'/(str(i)+'.txt')).read_text('utf8'));assert p['firstImagesOnly']==[g['images'][0] for g in groups]
out={'titleResourcesUnchanged':True,'circularIconFromUserOriginal':True,'all8860StoryLocationsUnchanged':True,'galleryContentPreserved':True,'fourPictureFirstVariantPreview':True,'previewTotalBytes':previews['totalBytes'],'galleryMemory':report,'physicalDeviceRetestPending':True}
(ROOT/'reports/visual013-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in out.items() if k!='galleryMemory'},ensure_ascii=False))
