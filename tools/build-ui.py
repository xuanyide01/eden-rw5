from pathlib import Path
import os,json
import numpy as np
from PIL import Image,ImageOps,ImageDraw,ImageFont
from paz import Paz
from zopfli.png import optimize
ROOT=Path(__file__).resolve().parents[1];common=ROOT/'src/common';ui=common/'ui';ui.mkdir(parents=True,exist_ok=True)
game=Path(os.environ['EDEN_GAME_ROOT']);arc=Paz(game/'sys.paz')
import io
def original(n):return Image.open(io.BytesIO(arc.read(n))).convert('RGB')
def title_background(source,target):
    im=original(source)
    # Exclude the baked-in PC menu; preserve the original image pixels and ratio.
    title=ImageOps.fit(im.crop((0,0,800,610)),(432,514),Image.Resampling.LANCZOS,centering=(.25,.5)).convert('RGBA')
    shade=Image.new('RGBA',title.size);sd=ImageDraw.Draw(shade)
    for x in range(432):sd.line((x,0,x,514),fill=(18,22,45,round(105*(1-x/432))))
    Image.alpha_composite(title,shade).convert('RGB').save(ui/target,quality=87,optimize=True,progressive=False)

title_background('topmenu0.png','title.jpg')
title_background('topmenu1.png','title-clear.jpg')
im=original('topmenu0.png')
logo=im.crop((839,10,1018,91)).convert('RGBA');a=np.asarray(logo).copy();rgb=a[:,:,:3].astype(float)
a[:,:,3]=(np.clip((rgb.min(2)-200)/55,0,1)*255).astype('uint8');a[:,:,:3]=255
logo=Image.fromarray(a);box=logo.getchannel('A').getbbox();logo=logo.crop(box);logo.save(ui/'title-logo.png')
font=ImageFont.truetype('C:/Windows/Fonts/times.ttf',25)
for key,text in [('start','New Game'),('chapter','Chapter'),('load','Load Game'),('config','System'),('extra','Memories'),('exit','Exit')]:
    image=Image.new('RGBA',(192,30));draw=ImageDraw.Draw(image);draw.text((0,0),text,font=font,fill='white',anchor='lt');image.save(ui/('title-'+key+'.png'))
system=Image.new('RGB',(432,514));d=ImageDraw.Draw(system)
for y in range(514):
    t=min(1,y/200);rgb=tuple(round(a+(b-a)*t) for a,b in zip((200,208,231),(237,240,247)));d.line((0,y,432,y),fill=rgb)
system.save(ui/'system.png',optimize=True)
fill=Image.new('RGB',(432,286));d=ImageDraw.Draw(fill)
for y in range(286):
    t=1-abs(y-143)/143;rgb=tuple(round(a+(b-a)*t) for a,b in zip((48,54,82),(86,94,128)));d.line((0,y,432,y),fill=rgb)
fill.save(ui/'art-fill.png',optimize=True)
fallback=Image.new('RGB',(240,150),'#252a41');fallback.save(common/'title_bg.png',optimize=True)
icon=ImageOps.fit(original('topmenu1.png').crop((0,30,610,640)),(192,192),Image.Resampling.LANCZOS).convert('RGBA')
mask=Image.new('L',(768,768));ImageDraw.Draw(mask).ellipse((0,0,767,767),fill=255);icon.putalpha(mask.resize((192,192),Image.Resampling.LANCZOS));icon.save(common/'logo.png',optimize=True)
raw=(common/'logo.png').read_bytes();packed=optimize(raw,lossy_transparent=True,num_iterations=15)
a=np.array(Image.open(io.BytesIO(raw)).convert('RGBA'));b=np.array(Image.open(io.BytesIO(packed)).convert('RGBA'))
assert np.array_equal(a[:,:,3],b[:,:,3]) and np.array_equal(a[a[:,:,3]>0],b[b[:,:,3]>0])
(common/'logo.png').write_bytes(min((raw,packed),key=len))
if (ROOT/'art/icon-source.jpg').exists():
    from app_icon import build_icon
    build_icon(ROOT)
print('UI_READY')
