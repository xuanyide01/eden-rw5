from pathlib import Path
import json,io,hashlib
from PIL import Image,ImageOps,ImageDraw

def build_thumbnails(root):
    root=Path(root);common=root/'src/common';directory=common/'gallery-preview';directory.mkdir(exist_ok=True)
    s=(common/'assets.js').read_text('utf8');frames=json.loads(s.split('export const frames=',1)[1].split(';\nexport const assets=',1)[0]);tiles=json.loads(s.split('export const tiles=',1)[1].split(';\n',1)[0]);pages=[]
    def tile(name):
        t=tiles[name];x,y,w,h=t['rect'];return Image.open(common/'images'/t['file']).convert('RGB').crop((x,y,x+w,y+h))
    def picture(name):
        f=frames[name];im=tile(f['base'])
        if f.get('patch'):im.paste(tile(f['patch']),(f['box'][0],f['box'][1]))
        return im
    for p in sorted((common/'gallery').glob('*.txt'),key=lambda p:int(p.stem)):
        groups=json.loads(p.read_text('utf8'));sheet=Image.new('RGB',(198,184),'#edf0f7');d=ImageDraw.Draw(sheet);inputs=[]
        for j,g in enumerate(groups):
            image=g['images'][0];inputs.append(image);x=(j%2)*102;y=(j//2)*92;d.rectangle((x,y,x+95,y+87),fill='#dce2f0');thumb=ImageOps.contain(picture(image),(90,58),Image.Resampling.LANCZOS);sheet.paste(thumb,(x+3+(90-thumb.width)//2,y+3+(58-thumb.height)//2))
        buf=io.BytesIO();sheet.save(buf,format='JPEG',quality=40,optimize=True,progressive=False);data=buf.getvalue();name=p.stem+'.jpg';(directory/name).write_bytes(data);pages.append({'file':name,'firstImagesOnly':inputs,'size':[198,184],'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    report={'pageCount':len(pages),'thumbnailImageWidgetsPerPage':1,'thumbnailSourceRGBABytes':198*184*4,'thumbnailRenderedRGBABytes':396*368*4,'jpegQuality':40,'totalBytes':sum(x['bytes'] for x in pages),'pages':pages}
    (root/'reports/gallery-thumbnails.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    memory=json.loads((root/'reports/gallery-memory.json').read_text('utf8'));memory.update(listImageWidgets=1,listStyle='four-picture grid',firstVariantPreviewOnly=True,previewSourceRGBABytes=198*184*4,previewRenderedRGBABytes=396*368*4)
    (root/'reports/gallery-memory.json').write_text(json.dumps(memory,ensure_ascii=False,indent=2),encoding='utf8');return report
if __name__=='__main__':
    r=build_thumbnails(Path(__file__).resolve().parents[1]);print('GALLERY_PREVIEW_PAGES',r['pageCount'],'BYTES',r['totalBytes'])
