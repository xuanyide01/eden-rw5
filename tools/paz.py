"""Read-only minori PAZ reader (Steam eden*). Never executes game code.

Format references: GARbro ArcFormats/Musica/ArcPAZ.cs (MIT), and the
Steam eden* parameter table in Inori/FuckGalEngine/Minori/fuckpaz.
Blowfish/ARC4 primitives are provided by PyCryptodome.
"""
from pathlib import Path
import struct, zlib, array, sys, json
try:
    from Crypto.Cipher import Blowfish, ARC4
except ImportError:
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'eden-probe/deps'))
    from Crypto.Cipher import Blowfish, ARC4

def swap32(data):
    words=array.array('I',data);words.byteswap();return words.tobytes()

def decrypt(data,key):
    assert len(data)%8==0
    return swap32(Blowfish.new(bytes.fromhex(key),Blowfish.MODE_ECB).decrypt(swap32(data)))

class Paz:
    def __init__(self,path,params=None):
        self.path=Path(path)
        if params is None:params=json.loads((Path(__file__).with_name('paz-eden.json')).read_text())
        self.params=params;self.keys=params['keys'][self.path.stem.lower()]
        with self.path.open('rb') as f:
            head=f.read(36);n=struct.unpack_from('<I',head,32)[0];self.xor=n>>24
            n^=self.xor*0x01010101
            assert 0<n<16*1024*1024 and n%8==0
            index=decrypt(self.unxor(f.read(n)),self.keys[0])
        count=struct.unpack_from('<I',index)[0];assert 0<count<100000
        pos=4;self.entries={}
        for _ in range(count):
            end=index.index(b'\0',pos);name=index[pos:end].decode('cp932');pos=end+1
            offset,unpacked,size,aligned,packed=struct.unpack_from('<QIIII',index,pos);pos+=24
            assert size<=aligned and aligned%8==0 and offset+aligned<=self.path.stat().st_size
            assert name not in self.entries
            self.entries[name]={'name':name,'offset':offset,'unpacked':unpacked,'size':size,'aligned':aligned,'packed':packed}
    def unxor(self,data):
        return data.translate(bytes(n^self.xor for n in range(256))) if self.xor else data
    def read(self,name):
        e=self.entries[name]
        with self.path.open('rb') as f:f.seek(e['offset']);data=f.read(e['aligned'])
        data=decrypt(self.unxor(data),self.keys[1])
        password=self.params['types'].get(name.rsplit('.',1)[-1],'') if not e['packed'] else ''
        if password:
            seed=(name.lower()+' %08X '%e['unpacked']+password).encode('cp932')
            data=ARC4.new(seed).decrypt(data)
        data=data[:e['size']]
        if e['packed']:data=zlib.decompress(data)
        assert len(data)==e['unpacked'],name
        return data
