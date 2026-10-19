from pathlib import Path
import hashlib,io,json,struct,zlib,zipfile
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import padding

BASE=Path(__file__).resolve().parents[2]
def u32(data,at):return struct.unpack_from('<I',data,at)[0]
def sized(data,at):
    size=u32(data,at);return data[at+4:at+4+size],at+4+size
def verify_signed_zip(raw,check_files=True):
    z=zipfile.ZipFile(io.BytesIO(raw));cd=z.start_dir
    assert raw[cd-16:cd]==b'RPK Sig Block 42'
    size=struct.unpack_from('<Q',raw,cd-24)[0];start=cd-size-8
    assert struct.unpack_from('<Q',raw,start)[0]==size
    entries={};at=start+8
    while at<cd-24:
        length=struct.unpack_from('<Q',raw,at)[0]
        ident=u32(raw,at+8);entries[ident]=raw[at+12:at+8+length];at+=length+8
    assert at==cd-24
    signers,end=sized(entries[0x1000101],0);assert end==len(entries[0x1000101])
    signer,end=sized(signers,0);assert end==len(signers)
    signed,at=sized(signer,0);signatures,at=sized(signer,at);pub,at=sized(signer,at);assert at==len(signer)
    signature,end=sized(signatures,0);assert end==len(signatures) and u32(signature,0)==259
    sig,end=sized(signature,4);assert end==len(signature)
    digests,at=sized(signed,0);certificates,at=sized(signed,at)
    cert,end=sized(certificates,0);assert end==len(certificates)
    certificate=x509.load_der_x509_certificate(cert);key=certificate.public_key()
    key.verify(sig,signed,padding.PKCS1v15(),hashes.SHA256())
    assert serialization.load_der_public_key(pub).public_numbers()==key.public_numbers()
    digest,end=sized(digests,0);assert end==len(digests) and u32(digest,0)==259
    expected,end=sized(digest,4);assert end==len(digest)
    footer=raw.rfind(b'PK\x05\x06')
    assert footer>=cd
    restored_footer=bytearray(raw[footer:]);struct.pack_into('<I',restored_footer,16,start)
    chunks=[raw[:start],raw[cd:footer],bytes(restored_footer)]
    section_hashes=[hashlib.sha256(b'\xa5'+struct.pack('<I',len(chunk))+chunk).digest() for chunk in chunks]
    actual=hashlib.sha256(b'\x5a'+struct.pack('<I',3)+b''.join(section_hashes)).digest()
    assert expected==actual,'RPK chunk digest mismatch'
    signed_files,end=sized(entries[0x1000201],0);assert end==len(entries[0x1000201])
    records,at=sized(signed_files,0)
    signature,end=sized(signed_files,at);assert end==len(signed_files)
    assert u32(records,0)==259 and u32(signature,0)==259
    sig,end=sized(signature,4);assert end==len(signature)
    key.verify(sig,records,padding.PKCS1v15(),hashes.SHA256())
    if check_files:
        files={zlib.crc32(n.encode('utf8')):n for n in z.namelist() if not n.endswith('/')}
        assert len(files)==sum(not n.endswith('/') for n in z.namelist())
        seen=set();at=4
        while at<len(records):
            crc=u32(records,at);length=struct.unpack_from('<H',records,at+4)[0];digest=records[at+6:at+6+length];at+=6+length
            name=files[crc];assert hashlib.sha256(z.read(name)).digest()==digest,name;seen.add(name)
        assert seen==set(files.values()),'unsigned files present'
    return hashlib.sha256(cert).hexdigest()

def audit(path):
    raw=path.read_bytes();z=zipfile.ZipFile(io.BytesIO(raw));assert z.testzip() is None
    cert=verify_signed_zip(raw)
    inner_raw=z.read('META-INF/CERT');inner=zipfile.ZipFile(io.BytesIO(inner_raw))
    assert verify_signed_zip(inner_raw,False)==cert
    manifest=json.loads(z.read('manifest.json'))
    declared=json.loads(inner.read('hash.json'))['digests']
    for name,digest in declared.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
    unsigned=set(n for n in z.namelist() if not n.endswith('/') and n!='META-INF/CERT')-set(declared)
    assert not unsigned,unsigned
    return {'file':path.name,'version':manifest['versionName'],'bytes':len(raw),
        'expandedBytes':sum(i.file_size for i in z.infolist()),'entries':len(z.infolist()),
        'sha256':hashlib.sha256(raw).hexdigest(),'certificateSha256':cert,
        'zipCRCValid':True,'outerSignatureValid':True,'innerSignatureValid':True,
        'allFileDigestsValid':True,'signedFiles':len(declared)}

