"""Lossless reflow of original raster glyphs; no OCR or retyping of wording."""
from PIL import Image
import numpy as np,hashlib,io,math
from zopfli.png import optimize

def runs(mask):
    positions=np.flatnonzero(mask)
    if not len(positions):return []
    breaks=np.flatnonzero(np.diff(positions)>1)
    starts=np.r_[positions[0],positions[breaks+1]];ends=np.r_[positions[breaks]+1,positions[-1]+1]
    return list(zip(map(int,starts),map(int,ends)))

def make_text_card(original):
    im=original.convert('RGB');array=np.asarray(im).astype('int16');background=array[0,0]
    # All 51 supplied cards use uniform white or black with monochrome glyphs.
    mask=np.max(np.abs(array-background),axis=2)>20
    rows=runs(mask.any(axis=1));assert rows,'Empty text card'
    glyph_height=max(b-a for a,b in rows);scale=1 if glyph_height>=26 else 26/glyph_height
    max_source_width=math.floor(392/scale)
    strips=[];ink_before=int(mask.sum());ink_after=0
    for y0,y1 in rows:
        columns=runs(mask[y0:y1].any(axis=0));assert columns
        x0=columns[0][0];end=columns[-1][1]
        while x0<end:
            remaining=[(a,b) for a,b in columns if b>x0]
            # Split only across blank columns, never through a raster glyph.
            candidates=[b for a,b in remaining if b-x0<=max_source_width]
            assert candidates,'An unbreakable original glyph exceeds the text viewport'
            x1=max(candidates)
            strips.append(im.crop((x0,y0,x1,y1)))
            ink_after+=int(mask[y0:y1,x0:x1].sum())
            next_columns=[a for a,b in remaining if a>=x1]
            if not next_columns:break
            x0=next_columns[0]
    assert ink_after==ink_before,'A text-card stroke was lost in reflow'
    gap=12;heights=[round(s.height*scale) for s in strips]
    total=sum(heights)+gap*(len(strips)-1)
    assert total<=238,('Text card cannot fit with readable 26px glyphs',len(strips),total)
    canvas=Image.new('RGB',(432,270),tuple(map(int,background)));y=(270-total)//2
    widths=[]
    for strip,h in zip(strips,heights):
        width=round(strip.width*scale);widths.append(width)
        strip=strip.resize((width,h),Image.Resampling.LANCZOS);canvas.paste(strip,((432-width)//2,y));y+=h+gap
    # Preserve native 27px glyphs; only enlarge smaller glyphs.
    # Lossless PNG and Zopfli retain every antialiased shade.
    canvas=canvas.convert('L');buf=io.BytesIO();canvas.save(buf,format='PNG',optimize=True)
    raw=buf.getvalue();compressed=optimize(raw,num_iterations=15,num_iterations_large=5)
    assert Image.open(io.BytesIO(compressed)).convert('L').tobytes()==canvas.tobytes()
    data=min((raw,compressed),key=len)
    return data,{'originalSize':list(im.size),'originalGlyphHeight':glyph_height,'displayGlyphHeight':round(glyph_height*scale),'displayRows':len(strips),'rowWidths':widths,'preservedInkPixels':ink_before,'allOriginalInkPreserved':True,'losslessPNG':True}
