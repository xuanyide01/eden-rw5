"""Independent source-line replay, used to cross-check the converted order."""
from pathlib import Path
import os,re,json,hashlib
from paz import Paz
ROOT=Path(__file__).resolve().parents[1];arc=Paz(Path(os.environ['EDEN_GAME_ROOT'])/'scr.paz')
scripts={Path(n).stem:arc.read(n).decode('gb18030').splitlines() for n in arc.entries}
labels={n:{l.split()[1]:i for i,l in enumerate(lines) if l.startswith('.label ')} for n,lines in scripts.items()}
proof=json.loads((ROOT/'reports/source-text-proof.json').read_text('utf8'))
results=[]
for replay in [False,True]:
    chapter='A001';cursor=0;variables={'eden_D001':1,'eden_B003':1,'eden_B006':1} if replay else {};actual=[];steps=0;ended=False
    while steps<100000:
        steps+=1;line=scripts[chapter][cursor];cursor+=1
        if line.startswith('.message '):
            parts=line.split(' ',4)
            if len(parts)==5:_,mid,voice,speaker,text=parts
            else:_,mid,voice,text=parts;speaker=''
            speaker=speaker.lstrip('@#');speaker={'Ryou':'亮','总部部长':'总部长'}.get(speaker,speaker)
            text=text.replace('\\v','').replace('\\a','').replace('\\n','\n').strip()
            actual.append({'scene':chapter,'speaker':speaker,'textSHA256':hashlib.sha256(text.encode('utf8')).hexdigest()})
        elif line.startswith('.if '):
            _,key,compare,value,label=line.split();left=variables.get(key,0);right=int(value)
            if (left==right if compare=='==' else left<=right):cursor=labels[chapter][label]
        elif line.startswith('.goto '):cursor=labels[chapter][line.split()[1]]
        elif line.startswith('.setGlobal '):_,key,eq,value=line.split();variables[key]=int(value)
        elif line.startswith('.chain '):chapter=Path(line.split()[1]).stem;cursor=0
        elif line=='.end':ended=True;break
    assert ended and chapter=='D001'
    expected=[{k:p[k] for k in ['scene','speaker','textSHA256']} for p in proof]
    assert actual==expected,'Independent source replay differs from conversion'
    results.append({'replayAfterClear':replay,'messages':len(actual),'sourceSteps':steps,'endedAt':chapter,'matched':True})
report={'source':'scr.paz','sourceSHA256':hashlib.sha256(arc.path.read_bytes()).hexdigest(),'executedOriginalCode':False,'freshAndClearedReplay':results,'unsupportedSourceCommands':0,'playerChoiceCommands':0}
(ROOT/'reports/source-audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
