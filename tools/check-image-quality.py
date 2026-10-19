"""Compare final two-layer resources to the same original cached static frames."""
from pathlib import Path
import json,io,math,re,os,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];cache=Path(os.environ.get('EDEN_IMAGE_CACHE',ROOT.parent/'eden-probe/cache'))
source=(ROOT/'src/common/assets.js').read_text('utf8');frames=json.loads(source.split('export const frames=',1)[1].split(';\n',1)[0])
tiles=json.loads((ROOT/'reports/image-tiles.json').read_text('utf8'))
patches=json.loads((ROOT/'reports/image-patches.json').read_text('utf8'))
samples=['B001_0003_0007.png','B004_0004_0006.png','C007_0004_0004.png','ev087a01.png','ev013b01.png','ev005a01.png']
def compose(frame):
    t=tiles[frame['base']];x,y,w,h=t['rect'];im=Image.open(ROOT/'src/common/images'/t['file']).convert('RGB').crop((x,y,x+w,y+h))
    if frame.get('patch'):
        t=tiles[frame['patch']];tx,ty,tw,th=t['rect'];patch=Image.open(ROOT/'src/common/images'/t['file']).crop((tx,ty,tx+tw,ty+th));x,y,w,h=frame['box'];assert patch.size==(w,h);im.paste(patch,(x,y))
    return im
sheet=Image.new('RGB',(1000,100+len(samples)*320),'#edf0f7');d=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
d.text((32,24),'《eden》压缩后的原作画面保留情况',font=font,fill='#262e4c')
d.text((32,62),'左：原作等比例缩小到显示尺寸　右：安装包内的底图与差分合成',font=small,fill='#68728e')
results=[]
for i,name in enumerate(samples):
    fid='f_'+__import__('hashlib').sha256(name.encode()).hexdigest()[:20]
    assert fid in frames,name
    frame=frames[fid];im=Image.open(cache/name).convert('RGB');im.thumbnail((264,256),Image.Resampling.LANCZOS)
    actual=compose(frame);assert actual.size==im.size
    a=np.asarray(im,dtype=float);b=np.asarray(actual,dtype=float);mse=float(np.mean((a-b)**2));psnr=10*math.log10(255**2/mse)
    # Mean non-overlapping 8x8 luminance SSIM, independent of external binary ABI.
    def luminance(x):return x[:,:,0]*.299+x[:,:,1]*.587+x[:,:,2]*.114
    aa=luminance(a);bb=luminance(b);h,w=aa.shape;h=h//8*8;w=w//8*8
    aa=aa[:h,:w].reshape(h//8,8,w//8,8).transpose(0,2,1,3).reshape(-1,64)
    bb=bb[:h,:w].reshape(h//8,8,w//8,8).transpose(0,2,1,3).reshape(-1,64)
    ma=aa.mean(1);mb=bb.mean(1);va=aa.var(1);vb=bb.var(1);cov=((aa-ma[:,None])*(bb-mb[:,None])).mean(1)
    ssim=float(np.mean(((2*ma*mb+6.5025)*(2*cov+58.5225))/((ma*ma+mb*mb+6.5025)*(va+vb+58.5225))))
    results.append({'source':name,'frame':fid,'size':im.size,'patch':bool(frame.get('patch')),'PSNR':psnr,'blockSSIM':ssim})
    y=105+i*320
    for col,image in enumerate([im,actual]):
        enlarged=image.resize((432,270),Image.Resampling.LANCZOS);sheet.paste(enlarged,(32+col*480,y))
    d.text((32,y+279),name+'   /   '+('共享底图＋局部差分' if frame.get('patch') else '独立画面'),font=small,fill='#454d70')
sheet.save(ROOT/'reports/image-quality-comparison.png')
report={'method':'PSNR and non-overlapping 8x8 luminance block SSIM on 6 representative original frames; not a perceptual user study','samples':results,'meanBlockSSIM':sum(r['blockSSIM'] for r in results)/len(results),'sampleCount':len(results)}
(ROOT/'reports/image-quality.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False))
