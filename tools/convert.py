"""Convert literal minori scripts, without executing their commands or EXE.

EDEN_GAME_ROOT points at the user's own Steam installation. A development
cache may be supplied as EDEN_IMAGE_CACHE. All story control statements are
checked; unknown statements fail conversion rather than silently changing flow.
"""
from pathlib import Path
import os,sys,json,io,re,hashlib,collections
from PIL import Image
from paz import Paz
from image_store import ImageStore

ROOT=Path(__file__).resolve().parents[1];COMMON=ROOT/'src/common'
GAME=Path(os.environ['EDEN_GAME_ROOT']);CACHE=Path(os.environ.get('EDEN_IMAGE_CACHE',ROOT.parent/'eden-probe/cache'))
SIZE=int(os.environ.get('EDEN_IMAGE_WIDTH','264'));QUALITY=int(os.environ.get('EDEN_IMAGE_QUALITY','60'))
OUT=COMMON/'images';OUT.mkdir(parents=True,exist_ok=True);REPORT=ROOT/'reports';REPORT.mkdir(exist_ok=True)
bg=Paz(GAME/'bg.paz');scr=Paz(GAME/'scr.paz')
scripts={Path(n).stem:scr.read(n).decode('gb18030') for n in scr.entries}
order=['A001']+['B%03d'%i for i in range(1,7)]+['C%03d'%i for i in range(1,14)]+['D001']
chapter_ids={name:i+1 for i,name in enumerate(order)}
storeImages=ImageStore(OUT,SIZE,QUALITY);assets=storeImages.assets;viewIds={}
def stable(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':'))
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(stable(obj),encoding='utf8')
def load_image(name):
    p=CACHE/name
    if p.exists():return Image.open(p).convert('RGB')
    return Image.open(io.BytesIO(bg.read(name))).convert('RGB')
def store(im,key):
    return storeImages.add(im,key,allowPatch=isinstance(key,str))
cardContent=json.loads((ROOT/'tools/text-card-content.json').read_text('utf8'))
assert len(cardContent)==57
full={}
for i,name in enumerate(sorted(n for n in bg.entries if n.endswith('.png'))):
    if name in cardContent:
        assert hashlib.sha256(bg.read(name)).hexdigest()==cardContent[name]['sourceSHA256'],name
        full[name]=storeImages.addNativeTextCard(name,cardContent[name])
    else:full[name]=store(load_image(name),name)
    if i%400==0:print('IMAGE',i,flush=True)

def view(name,x,y):
    im=load_image(name)
    # Regular 1024x640 frames retain their complete original composition.
    # Larger panning art follows the source camera for story, and remains full in gallery.
    if name in cardContent:return full[name]
    original_size=imageMeta.get(name,{}).get('originalSize')
    if original_size is None:original_size=list(Image.open(io.BytesIO(bg.read(name))).size)
    if list(original_size)==[1024,640]:return full[name]
    key=(name,x,y)
    if key not in viewIds:
        # Crop panning windows before resizing, keeping their available source detail.
        im=Image.open(io.BytesIO(bg.read(name))).convert('RGB');w,h=im.size;sx=1
        left=max(0,min(w-1024,x));top=max(0,min(h-640,y))
        box=(round(left*sx),round(top*sx),round((left+min(w,1024))*sx),round((top+min(h,640))*sx))
        viewIds[key]=store(im.crop(box),{'name':name,'camera':[x,y]})
    return viewIds[key]

metaPath=CACHE.parent/'image-meta.json'
imageMeta=json.loads(metaPath.read_text('utf8')) if metaPath.exists() else {}
commands=collections.Counter();sourceProof=[];scenes={};warnings=[];movies=[];cameraProof=[];cameraCommands=[]
ignore={'transition','panel','playBGM','playVoice','playSE','playSE2','pragma','wait','endScroll','shakeScreen','effect'}
names={'Ryou':'亮','总部部长':'总部长'}
for chapter in order:
    ops=[];labels={};jumps=[];background='BLACK.png';x=y=0
    for lineNo,line in enumerate(scripts[chapter].splitlines(),1):
        if not line or line.startswith(';'):continue
        if not line.startswith('.'):raise ValueError((chapter,lineNo,line))
        tag=line[1:].split(' ',1)[0];commands[tag]+=1
        if tag=='message':
            m=re.fullmatch(r'\.message (\d+) ([^ ]*) ([^ ]*) (.*)',line)
            if m:mid,voice,speaker,text=m.groups()
            else:
                # Two original C006 lines omit the speaker field; preserve their full narration.
                m=re.fullmatch(r'\.message (\d+) ([^ ]*) (.+)',line);assert m,(chapter,lineNo,line)
                mid,voice,text=m.groups();speaker='';warnings.append({'scene':chapter,'line':lineNo,'repair':'missing-speaker-field'})
            speaker=speaker.lstrip('#@');speaker=names.get(speaker,speaker)
            text=text.replace('\\n','\n').replace('\\v','').replace('\\a','').strip()
            assert '\\' not in text and '\ufffd' not in text,(chapter,lineNo,text)
            op={'op':'text','speaker':speaker,'text':text,'background':view(background,x,y),'bodies':[]}
            cameraProof.append({'scene':chapter,'line':lineNo,'cursor':len(ops),'source':background,'camera':[x,y],'size':imageMeta.get(background,{}).get('originalSize'),'frame':op['background']})
            sourceProof.append({'scene':chapter,'line':lineNo,'messageId':mid,'cursor':len(ops),'speaker':speaker,'textSHA256':hashlib.sha256(text.encode()).hexdigest()});ops.append(op)
        elif tag=='stage':
            _,star,background,xx,yy=line.split();assert star=='*' and background in full,line;x=int(xx);y=int(yy)
        elif tag in ['vscroll','hscroll','scroll']:
            start_camera=[x,y]
            if tag=='vscroll':y=int(line.split()[1])
            elif tag=='hscroll':x=int(line.split()[1])
            else:x,y=map(int,line.split()[1:3])
            cameraCommands.append({'scene':chapter,'line':lineNo,'command':line,'source':background,'from':start_camera,'to':[x,y],'sourceSize':imageMeta.get(background,{}).get('originalSize')})
        elif tag=='label':labels[line.split()[1]]=len(ops)
        elif tag=='if':
            _,key,compare,value,label=line.split();assert compare in ['==','<='] and re.fullmatch(r'eden_\w+',key),line
            jumps.append((len(ops),label));ops.append({'op':'if','key':'sf.'+key,'compare':compare,'value':int(value),'to':0})
        elif tag=='goto':jumps.append((len(ops),line.split()[1]));ops.append({'op':'goto','to':0})
        elif tag in ['set','setGlobal']:
            _,key,eq,value=line.split();assert eq=='=' and re.fullmatch(r'[\w]+',key),line
            ops.append({'op':'set','key':('sf.' if tag=='setGlobal' else 'local.')+key,'value':int(value)})
        elif tag=='chain':
            target=Path(line.split()[1]).stem;assert target in chapter_ids,line;ops.append({'op':'jumpScene','scene':chapter_ids[target]})
        elif tag=='end':ops.append({'op':'end'})
        elif tag=='movie':movies.append({'scene':chapter,'line':lineNo,'source':line.split()[2]})
        elif tag in ignore:pass
        else:raise ValueError('Unsupported source command '+line)
    for pos,label in jumps:assert label in labels,(chapter,label);ops[pos]['to']=labels[label]
    assert ops and ops[-1]['op'] in ['jumpScene','end'],chapter
    sid=chapter_ids[chapter];scenes[str(sid)]=ops
    for block,start in enumerate(range(0,len(ops),512)):write(COMMON/'story'/str(sid)/(str(block)+'.txt'),ops[start:start+512])
    print('STORY',chapter,len(ops),flush=True)

gallery=[]
for name in sorted(full):
    if name in cardContent or name in ['BLACK.png','WHITE.png'] or name.startswith(('mozi_','mikage','trial_title','yakata_end')):continue
    stem=Path(name).stem
    m=re.match(r'([ABC]\d{3}_\d{4})',stem)
    if m:group=m[1];label=('序章' if chapter_ids[group[:4]]==1 else '第 '+str(chapter_ids[group[:4]]-1)+' 章')+' · 场景 '+str(int(group[-4:]))
    else:
        m=re.match(r'(ev\d+)',stem)
        if m:group=m[1];label='CG '+group[2:].zfill(3)
        elif stem.startswith('B002_top'):
            group=stem;label='天空 · '+('日景' if stem.endswith('2') else '夜景')
        elif stem.startswith('maisou_bg'):
            m=re.match(r'(maisou_bg\d+)',stem);group=m[1];label='背景 '+group.removeprefix('maisou_bg')
        else:group=stem;label='CG · '+stem
    gallery.append({'image':full[name],'source':name,'group':group,'label':label})
write(REPORT/'gallery-source.json',gallery)
from gallery_pack import packGallery
packGallery(COMMON,gallery,REPORT)
tiles=storeImages.packAtlases()
catalog={'game':'eden','initial':1,'flowScene':1,'routes':[{'name':'正篇','scenes':list(range(1,22))}],
         'chapters':[{'id':chapter_ids[n],'route':0,'name':('序章' if n=='A001' else '终章' if n=='D001' else '第 '+str(chapter_ids[n]-1)+' 章')} for n in order],
         'scenes':{str(chapter_ids[n]):{'name':n,'displayName':('序章' if n=='A001' else '终章' if n=='D001' else '第 '+str(chapter_ids[n]-1)+' 章'),'length':len(scenes[str(chapter_ids[n])])} for n in order},'endings':{'21':'正篇'}}
(COMMON/'catalog.js').write_text('export const catalog='+stable(catalog)+';\n',encoding='utf8')
(COMMON/'assets.js').write_text('export const frames='+stable(storeImages.frames)+';\nexport const assets=frames;\nexport const tiles='+stable(tiles)+';\n'+'''
export function imagePath(name){const f=frames[name],t=f&&tiles[f.base];return t?'/common/images/'+t.file:'/common/title_bg.png';}
function rectLayer(tile,scale,left,top){const t=tiles[tile];if(!t)return {src:'',left:0,top:0,width:1,height:1,imageLeft:0,imageTop:0,imageWidth:1,imageHeight:1};
 return {src:'/common/images/'+t.file,left:Math.round(left),top:Math.round(top),width:Math.round(t.rect[2]*scale),height:Math.round(t.rect[3]*scale),imageLeft:-Math.round(t.rect[0]*scale),imageTop:-Math.round(t.rect[1]*scale),imageWidth:Math.round(t.size[0]*scale),imageHeight:Math.round(t.size[1]*scale)};
}
export function baseLayer(name,width,height){const f=frames[name];if(!f)return rectLayer('',1,0,0);const scale=Math.min(width/f.size[0],height/f.size[1]);return rectLayer(f.base,scale,(width-f.size[0]*scale)/2,(height-f.size[1]*scale)/2);}
export function frameLayer(name,width,height){
 const frame=frames[name];if(!frame||!frame.patch)return rectLayer('',1,0,0);
 const scale=Math.min(width/frame.size[0],height/frame.size[1]),box=frame.box;
 return rectLayer(frame.patch,scale,(width-frame.size[0]*scale)/2+box[0]*scale,(height-frame.size[1]*scale)/2+box[1]*scale);
}
''',encoding='utf8')
(COMMON/'portrait-layout.js').write_text('export function portraitBox(){return {width:1,height:1,top:285,left:0};}\n',encoding='utf8')
write(REPORT/'source-text-proof.json',sourceProof);write(REPORT/'assets.json',list(storeImages.files.values()));write(REPORT/'image-patches.json',storeImages.proof);write(REPORT/'image-storage.json',storeImages.report());write(REPORT/'image-tiles.json',tiles)
write(REPORT/'text-cards.json',storeImages.textProof);write(REPORT/'camera-source.json',cameraProof);write(REPORT/'camera-commands.json',cameraCommands)
assert OUT.resolve().parent==COMMON.resolve()
for old in OUT.iterdir():
    if old.suffix in ['.jpg','.png'] and old.name not in storeImages.files:old.unlink()
report={'scenes':len(order),'sourceMessageCount':len(sourceProof),'sourceCommands':dict(commands),'playerChoices':0,'chapterOrder':order,'allJumpLabelsResolved':True,'warnings':warnings,'omittedMovies':movies,
        'imageWidth':SIZE,'jpegQuality':QUALITY-4,'uniqueFrameCount':len(assets),'atlasImageFiles':len(storeImages.files),'jpegAtlasFiles':len(list(OUT.glob('*.jpg'))),'losslessTextCardFiles':len(list(OUT.glob('*.png'))),'nativeTextCards':len(cardContent),'nativeTextCardOccurrences':sum(x['source'] in cardContent for x in cameraProof),'sourcePNGCount':len(full),'galleryVariants':len(gallery),'galleryGroups':len({g['group'] for g in gallery}),'imageBytes':sum(p.stat().st_size for p in OUT.iterdir() if p.suffix in ['.jpg','.png']),'sourceEXEExecuted':False}
from gallery_thumbnails import build_thumbnails
build_thumbnails(ROOT)
write(REPORT/'conversion.json',report);print(stable(report),flush=True)
