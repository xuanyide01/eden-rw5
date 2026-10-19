from pathlib import Path
import json,collections

def packGallery(common,items,reports):
    common=Path(common);reports=Path(reports);directory=common/'gallery';directory.mkdir(exist_ok=True)
    groups={}
    for item in items:
        g=groups.setdefault(item['group'],{'label':item['label'],'images':[]});g['images'].append(item['image'])
    groups=list(groups.values());pages=[]
    for start in range(0,len(groups),4):
        data=json.dumps(groups[start:start+4],ensure_ascii=False,separators=(',',':')).encode('utf8')
        assert len(data)<16384
        p=directory/(str(start//4)+'.txt');p.write_bytes(data);pages.append({'file':p.name,'bytes':len(data),'groups':len(groups[start:start+4]),'variants':sum(len(g['images']) for g in groups[start:start+4])})
    for p in directory.glob('*.txt'):
        if p.name not in {x['file'] for x in pages}:p.unlink()
    old=common/'gallery.txt'
    if old.exists():old.unlink()
    info={'groups':len(groups),'variants':len(items),'pages':len(pages),'pageSize':4}
    helper="""import {frames,baseLayer,frameLayer} from './assets.js';
export const galleryInfo=INFO;
export function groupGallery(items){const groups=[],by={};for(const item of items){const id=item.group||item.source;let g=by[id];if(!g){g={id,image:item.image,label:item.label,variants:[]};by[id]=g;groups.push(g);}g.variants.push(item);}return groups;}
export function stepVariant(index,delta,count){return count?((index+delta)%count+count)%count:0;}
export function galleryLayer(name,patch){const f=frames[name];if(!f)return {src:''};const w=Math.min(264,f.size[0]),h=Math.min(270,f.size[1]),layer=patch?frameLayer(name,w,h):baseLayer(name,w,h);layer.left+=Math.round((432-w)/2);layer.top+=Math.round((432-h)/2);return layer;}
""".replace('INFO',json.dumps(info,separators=(',',':')))
    (common/'gallery.js').write_text(helper,encoding='utf8')
    report=dict(info,pageFiles=pages,maxReadBytes=max(p['bytes'] for p in pages),listImageWidgets=0,maxSimultaneousCGImages=2,maxLayerPixels=280*512,maxTwoLayerRGBABytes=2*280*512*4,realDeviceRetestPending=True)
    (reports/'gallery-memory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    return report
