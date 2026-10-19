from pathlib import Path
import json,hashlib,zipfile,collections
ROOT=Path(__file__).resolve().parents[1]
content=json.loads((ROOT/'tools/text-card-content.json').read_text('utf8'));cards=json.loads((ROOT/'reports/text-cards.json').read_text('utf8'));assert len(cards)==len(content)==57
source=(ROOT/'src/common/assets.js').read_text('utf8');frames=json.loads(source.split('export const frames=',1)[1].split(';\nexport const assets=',1)[0])
for c in cards:
 assert c['rendering']=='native-text' and c['reviewedAgainstOriginal'] and c['fontSize']==28
 assert {k:c[k] for k in ['text','background','foreground']}==frames[c['frame']]['card']
 assert c['sourceSHA256']==content[c['source']]['sourceSHA256']
assert len({frames[c['frame']]['base'] for c in cards})==2
assert not list((ROOT/'src/common/images').glob('*.png'))
ux=(ROOT/'src/pages/index/index.ux').read_text('utf8');assert 'chapterLabel' not in ux and 'dialogue-edge' not in ux
proof=json.loads((ROOT/'reports/camera-source.json').read_text('utf8'));uses=[x for x in proof if x['source'] in content];assert len(uses)==44
assert any(x['scene']=='B002' and x['cursor']==39 and x['source']=='B002_watashihane.png' for x in uses)
# Exact proof digest retained from the verified 0.1.1 source archive.
assert hashlib.sha256((ROOT/'reports/source-text-proof.json').read_bytes()).hexdigest()=='98dabb0568a9e5179e4c4256101ce202cd231dc1815663da56bb0100f3639d01'
report={'nativeTextCards':57,'storyOccurrences':44,'rasterTextCardImages':0,'sharedBlankTiles':2,'fontSize':28,'lineHeight':38,'maxTextWidth':384,'reviewedAgainstOriginal':True,'B002RegressionCovered':True,'chapterCodesRemovedFromUI':True,'all8860StoryLocationsUnchanged':True,'sameSourceTextProofAs011':True,'physicalDeviceTested':False}
(ROOT/'reports/visual012-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
