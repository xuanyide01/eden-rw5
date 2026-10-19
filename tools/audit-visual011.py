from pathlib import Path
import json,hashlib,math,collections,zipfile
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];reports=ROOT/'reports';common=ROOT/'src/common'
cards=json.loads((reports/'text-cards.json').read_text('utf8'));assert len(cards)==51
for c in cards:
    assert c['displayGlyphHeight'] in [26,27] and c['allOriginalInkPreserved'] and c['losslessPNG']
    im=Image.open(common/'images'/c['file']);im.load();assert im.format=='PNG' and im.size==(432,270)
    assert max(c['rowWidths'])<=392
camera=json.loads((reports/'camera-commands.json').read_text('utf8'));assert len(camera)==24
assert collections.Counter(x['command'].split()[0] for x in camera)=={'.vscroll':12,'.hscroll':3,'.scroll':9}
proof=json.loads((reports/'camera-source.json').read_text('utf8'));assert len(proof)==8860
full=next(x for x in proof if x['source']=='ev016a01_mugai.png')
assert full['size']==[1600,1000]
expected='f_'+hashlib.sha256(str({'name':full['source'],'camera':full['camera']}).encode()).hexdigest()[:20]
assert full['frame']==expected,'Oversized 16:10 image still bypasses source camera'
ux=(ROOT/'src/pages/index/index.ux').read_text('utf8');assert 'dialogue-edge' not in ux
old=json.loads((ROOT.parents[1]/'outputs/eden-RW5-0.1.0-检查报告.json').read_text('utf8'))
assert old['conversion']['sourceMessageCount']==len(proof)
with zipfile.ZipFile(ROOT.parents[1]/'outputs/eden-RW5-0.1.0-源码.zip') as z:
    oldproof=json.loads(z.read('eden-rw5/reports/source-text-proof.json'))
newproof=json.loads((reports/'source-text-proof.json').read_text('utf8'))
assert [(x['scene'],x['cursor'],x['textSHA256']) for x in newproof]==[(x['scene'],x['cursor'],x['textSHA256']) for x in oldproof]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
sample_names=['mozi_A001_020.png','mozi_B005_003.png','mozi_C001_002.png','mozi_C011_004.png']
sheet=Image.new('RGB',(964,100+len(sample_names)*324),'#edf0f7');d=ImageDraw.Draw(sheet)
d.text((28,18),'《eden》字卡：旧版缩图 / 新版原字形无损重排',font=font,fill='#262e4c')
d.text((28,58),'左：缩小整幅 CG　右：26–27 像素字形，保留完整内容，适配手表宽度',font=small,fill='#68728e')
cache=ROOT.parent/'eden-probe/text-original'
for i,name in enumerate(sample_names):
    c=next(x for x in cards if x['source']==name);old=Image.open(cache/name).convert('RGB').resize((432,270),Image.Resampling.LANCZOS)
    new=Image.open(common/'images'/c['file']).convert('RGB');y=100+i*324
    sheet.paste(old,(28,y));sheet.paste(new,(504,y));d.text((28,y+282),name,font=small,fill='#454d70')
sheet.save(reports/'text-card-comparison.png')
report={'losslessTextCards':51,'displayGlyphHeight':[26,27],'allInkPreserved':True,'noDialogueSeparator':True,'sourceCameraCommands':24,'sameAspectOversizedImageCorrected':full,'allTextFrameCursorsPreserved':True,'staticCameraEndpoints':True,'originalPCAnimationTimingClaimed':False}
(reports/'visual011-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
