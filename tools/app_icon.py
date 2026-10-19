from pathlib import Path
import io,json,hashlib
import numpy as np
from PIL import Image,ImageOps,ImageDraw
from zopfli.png import optimize

def build_icon(root):
    root=Path(root);source=root/'art/icon-source.jpg';im=Image.open(source).convert('RGB');w,h=im.size
    box=(round(w*.3125),0,round(w*.9375),round(h*.625))
    icon=ImageOps.fit(im.crop(box),(192,192),Image.Resampling.LANCZOS).convert('RGBA')
    mask=Image.new('L',(768,768));ImageDraw.Draw(mask).ellipse((0,0,767,767),fill=255);icon.putalpha(mask.resize((192,192),Image.Resampling.LANCZOS))
    buf=io.BytesIO();icon.save(buf,format='PNG',optimize=True);raw=buf.getvalue();packed=optimize(raw,lossy_transparent=True,num_iterations=15)
    a=np.array(icon);b=np.array(Image.open(io.BytesIO(packed)).convert('RGBA'));assert np.array_equal(a[:,:,3],b[:,:,3]) and np.array_equal(a[a[:,:,3]>0],b[b[:,:,3]>0])
    result=min((raw,packed),key=len);(root/'src/common/logo.png').write_bytes(result)
    report={'source':'art/icon-source.jpg','sourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'sourceSize':[w,h],'crop':box,'output':[192,192],'circularTransparent':True,'originalPixelsUsed':True,'generatedPreviewUsed':False,'sha256':hashlib.sha256(result).hexdigest()}
    (root/'reports/icon013.json').write_text(json.dumps(report,indent=2),encoding='utf8');return report
if __name__=='__main__':print(json.dumps(build_icon(Path(__file__).resolve().parents[1])))
