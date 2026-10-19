"""Bounded two-layer JPEG frames; no recursive patches or decompression tricks.

Each source keeps its full aspect ratio. Similar frames in the same source
scene can reuse a JPEG base and add one rectangular JPEG patch. This is static
image compression, not execution of original animation instructions.
"""
import re,io,hashlib,math
from pathlib import Path
import numpy as np
from PIL import Image

class ImageStore:
    def __init__(self,out,width=288,quality=62):
        self.out=Path(out);self.out.mkdir(parents=True,exist_ok=True)
        self.width=width;self.quality=quality;self.assets={};self.frames={};self.files={};self.bases={};self.byDigest={};self.proof=[];self.rawTiles={}
        self.textTiles={};self.textProof=[]
    def addNativeTextCard(self,key,content):
        # Runtime text replaces raster glyphs; all cards share two blank tiles.
        blank=self.add(Image.new('RGB',(1024,640),content['background']),'native-card-'+content['background'],allowPatch=False)
        ident='f_'+hashlib.sha256(str(key).encode()).hexdigest()[:20]
        card={k:content[k] for k in ['text','background','foreground']}
        self.frames[ident]=dict(self.frames[blank],card=card);self.assets[ident]=self.frames[blank]['base']
        self.textProof.append(dict(source=key,frame=ident,rendering='native-text',fontSize=28,lineHeight=38,maxWidth=384,**content))
        return ident
    def encode(self,im,quality=None):
        buf=io.BytesIO();im.save(buf,format='JPEG',quality=quality or self.quality,optimize=True,progressive=False);return buf.getvalue()
    def file(self,data,raw=None):
        sha=hashlib.sha256(data).hexdigest();name='e_'+sha[:20]+'.jpg'
        if name not in self.files:
            (self.out/name).write_bytes(data);self.files[name]={'file':name,'bytes':len(data),'sha256':sha}
            if raw is not None:self.rawTiles[name]=raw.copy()
        return name
    def add(self,im,key,allowPatch=True):
        im=im.convert('RGB');im.thumbnail((self.width,256),Image.Resampling.LANCZOS)
        full=self.encode(im);digest=hashlib.sha256(full).hexdigest()
        if digest in self.byDigest:return self.byDigest[digest]
        ident='f_'+hashlib.sha256(str(key).encode()).hexdigest()[:20]
        arr=np.asarray(im,dtype=np.int16)
        # Related camera/scene prefixes form independent, small base pools.
        match=re.match(r'([ABC]\d{3}_\d{4}|ev\d+)',str(key));group=match[1] if match else str(key)
        if getattr(self,'lastGroup',None)!=group:self.bases={};self.lastGroup=group
        candidates=self.bases.setdefault(group,[]);best=None;cost=len(full)
        if allowPatch and im.width==self.width and abs(im.width/im.height-1.6)<.02:
            for base in candidates:
                if base['array'].shape!=arr.shape:continue
                changed=np.any(np.abs(arr-base['array'])>2,axis=2)
                ys,xs=np.nonzero(changed)
                if len(xs)==0:
                    best=(base,None,None,0);break
                x0=max(0,int(xs.min())//8*8);y0=max(0,int(ys.min())//8*8)
                x1=min(im.width,math.ceil((int(xs.max())+1)/8)*8);y1=min(im.height,math.ceil((int(ys.max())+1)/8)*8)
                if (x1-x0)*(y1-y0)>im.width*im.height*.66:continue
                patch=self.encode(im.crop((x0,y0,x1,y1)),self.quality+3)
                newCost=len(patch)+110
                if newCost<cost:cost=newCost;best=(base,patch,[x0,y0,x1-x0,y1-y0],int(changed.sum()))
        if best:
            base,patch,box,changed=best
            frame={'base':base['file'],'size':list(im.size)}
            if patch:frame.update(patch=self.file(patch,im.crop((box[0],box[1],box[0]+box[2],box[1]+box[3]))),box=box)
            self.frames[ident]=frame;self.assets[ident]=base['file']
            self.proof.append({'frame':ident,'source':key,'baseSource':base['source'],'size':list(im.size),'box':box,'originalJPEGBytes':len(full),'storedNewBytes':len(patch) if patch else 0,'tolerance':2})
        else:
            filename=self.file(full,im);self.assets[ident]=filename;self.frames[ident]={'base':filename,'size':list(im.size)}
            # Limit cache memory and comparisons even if a source group is malformed.
            if len(candidates)<32:candidates.append({'file':filename,'array':arr,'source':key})
        self.byDigest[digest]=ident
        return ident
    def report(self):
        return {'width':self.width,'quality':self.quality-4,'patchSelectionQuality':self.quality,'atlasMaxSize':[self.width+16,512],'maxDecodedRGBABytesPerAtlas':(self.width+16)*512*4,'frameCount':len(self.frames),'files':len(self.files),'bytes':sum(x['bytes'] for x in self.files.values()),'patchFrames':sum('patch'in x for x in self.frames.values()),'approximatePlainJPEGBytesSavedBeforeAtlas':sum(p['originalJPEGBytes']-p['storedNewBytes'] for p in self.proof),'maxLayers':2,'differenceThreshold':2}
    def packAtlases(self):
        """One JPEG encode from original pixels; pad every tile to avoid bleed.

        Each decoded atlas is <= 280x512, limiting per-layer RGBA decode memory
        to 573,440 bytes. Only source rectangles are visible in clipped widgets.
        """
        tiles=dict(self.textTiles);atlasFiles={k:v for k,v in self.files.items() if v.get('kind')=='text-card'};pending=[];height=0
        def flush():
            nonlocal pending,height
            if not pending:return
            canvas=Image.new('RGB',(self.width+16,height),'black')
            for name,im,y in pending:
                # Eight-pixel edge replication also aligns JPEG MCU boundaries.
                border=Image.new('RGB',(im.width+16,im.height+16))
                border.paste(im,(8,8));border.paste(im.crop((0,0,1,im.height)).resize((8,im.height)),(0,8));border.paste(im.crop((im.width-1,0,im.width,im.height)).resize((8,im.height)),(im.width+8,8))
                border.paste(border.crop((0,8,border.width,9)).resize((border.width,8)),(0,0));border.paste(border.crop((0,im.height+7,border.width,im.height+8)).resize((border.width,8)),(0,im.height+8))
                canvas.paste(border,(0,y));tiles[name]={'rect':[8,y+8,im.width,im.height]}
            data=self.encode(canvas,self.quality-4);sha=hashlib.sha256(data).hexdigest();filename='a_'+sha[:20]+'.jpg';(self.out/filename).write_bytes(data)
            atlasFiles[filename]={'file':filename,'bytes':len(data),'sha256':sha,'size':list(canvas.size)}
            for name,im,y in pending:tiles[name].update(file=filename,size=list(canvas.size))
            pending=[];height=0
        for name,im in self.rawTiles.items():
            block=math.ceil((im.height+16)/8)*8
            if height+block>512:flush()
            pending.append((name,im,height));height+=block
        flush();self.tiles=tiles;self.files=atlasFiles;self.rawTiles={}
        return tiles
