from pathlib import Path
import json,hashlib,zipfile,shutil
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'outputs';OUT.mkdir(exist_ok=True)
m=json.loads((ROOT/'src/manifest.json').read_text('utf8'));src=ROOT/'dist'/f'{m["package"]}.debug.{m["versionName"]}.rpk'
data=src.read_bytes();sha=hashlib.sha256(data).hexdigest();assert len(data)<10485760
audit=json.loads((ROOT/'reports/package-audit.json').read_text('utf8'));assert audit['sha256']==sha
native=json.loads((ROOT/'native-test-results/report.json').read_text('utf8'));assert native['result']=='passed' and native['packageSha256']==sha
cold=json.loads((ROOT/'native-test-results/cold-report.json').read_text('utf8'));assert cold['result']=='passed' and cold['packageSHA256']==sha
is014=m['versionName']=='0.1.4'
stressFile=ROOT/('native-test-results/baseline013/gallery-stress-report.json' if is014 else 'native-test-results/gallery-stress-report.json')
stress=json.loads(stressFile.read_text('utf8'));assert stress['result']=='passed'
if is014:assert stress['packageSha256']==json.loads((ROOT/'reports/baseline013-hashes.json').read_text('utf8'))['packageSHA256']
else:assert stress['packageSha256']==sha
name='eden-RW5-'+m['versionName']
for ext in ['bin','rpk']:(OUT/(name+'.'+ext)).write_bytes(data)
report={'game':'《eden》','version':m['versionName'],'target':'REDMI Watch 5 / 432x514','bytes':len(data),'decimalMB':round(len(data)/1000000,3),'sha256':sha,'packageAudit':audit,'sourceAudit':json.loads((ROOT/'reports/source-audit.json').read_text('utf8')),'conversion':json.loads((ROOT/'reports/conversion.json').read_text('utf8')),'visualChanges':json.loads((ROOT/('reports/visual014-audit.json' if is014 else 'reports/visual013-audit.json')).read_text('utf8')),'unitTests':{'passed':24 if is014 else 22,'failed':0},'galleryStress':stress,'icon':json.loads((ROOT/'reports/icon013.json').read_text('utf8')),'nativeTests':native,'coldOverwrite':cold,'physicalDeviceTested':False}
if is014:
    report['galleryStressBaseline013']=report.pop('galleryStress');report['galleryResourcesAndLogicUnchanged']=True;report['titleScreenshots']=json.loads((ROOT/'reports/title014-native-pixels.json').read_text('utf8'))
feedbackPath=ROOT/('reports/hardware-feedback'+m['versionName'].replace('.','')+'.json')
if feedbackPath.exists():
    feedback=json.loads(feedbackPath.read_text('utf8'));assert feedback['version']==m['versionName'] and feedback['packageSHA256']==sha
    report['physicalDeviceTested']=True;report['hardwareEvidenceType']='user-reported physical-device test';report['hardwareFeedback']=feedback
(OUT/(name+'-检查报告.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
notes=f'''# 《eden》红米手表 5 版 {m['versionName']}

安装文件：{name}.bin（{len(data):,} 字节，约 {len(data)/1000000:.3f} MB）。同名 .rpk 与 .bin 内容相同，选择一种即可。

包含 21 章、8,860 条中文台词及旁白、30 个存档栏位、章节选择、295 组 / 2,341 张 CG 与差分。音乐、语音、音效、OP/ED 及动态演出省略。源脚本没有玩家选项分支；下一章按原章序跳转，保留通关状态。

通过表盘自定义工具传输安装。手机传输完成后还要等待手表处理安装，勿连续重复发送。当前版本已完成 Vela 通用虚拟手表的安装、覆盖安装、退出重开、01/30 号读档、全部章序跳跃、首屏列表刷新、差分图和长文本滑动检查。2026-10-20 维护者反馈 REDMI Watch 5 实测：首次安装导致手表重启，再次安装成功，之后暂未发现其他问题。首次安装重启仍为已知问题；维护者推测可能是安装解包时峰值内存不足或系统负荷过高，尚未证实，尚无设备日志；再次安装成功不代表已修复。

画面与人物一起完整等比例呈现；全幅长图在 CG 鉴赏中保留。普通图片使用共享底图、差分和 778 个小型 JPEG 图集。57 张纯文字画面改为原生 28 像素文字，在黑白背景中居中并自动换行；其中 44 张用于正篇显示，不再保存字形图片。原图文字与下方台词分别保留。手表文件系统的实际占用会大于安装包大小，应留出正常安装空间。

应用图标采用用户原图的圆形面部裁切。未通关仍使用原建筑背景；完成正篇终章后，标题切换为原作蓝色蝴蝶背景，退出重开后保留，也兼容之前版本的通关记录。标题布局保持不变。

保留 0.1.3 针对实机 CG 鉴赏崩溃／重启的内存优化。鉴赏列表保留每页 4 组的四宫格首图预览，每页只解码一张小合成预览；打开组后再逐张加载差分，按原像素大小居中显示。图片显示面积较旧版缩小，全部图片和差分均保留。本次用户反馈未报告其余功能异常；如果使用鉴赏时仍有重启，请先停止反复进入鉴赏，重启手表后使用正文，并记录发生在哪一组、哪一张。

阅读界面已移除内部章节代码，章节与存档列表显示中文章名。

文本有标准/大两种字号；长段落可上滑阅读。滑动不翻页，重新轻点可下一句。首次逐字显示时，轻点先补全当前文字，再次轻点进入下一句。

菜单内可开启自动播放，返回正文后运行。慢速／标准／快速在约 30 毫秒一字显示完成后，分别等待 2.6／1.5／0.8 秒再进入下一句。超过 60 字每字增加 55 毫秒，最多增加 5 秒。菜单、存读档、按住正文、滑动阅读及后台暂停；回到正文重新计时。遇到选项需手动选择，选完继续；本作正篇无玩家选项，已用测试剧情验证相应行为。上一句、返回标题、剧情结束或出错会关闭自动。速度档位保留，但重新打开应用时默认关闭自动。

视野变化来自原作长图镜头指令和图片差分；移植版保留目标镜头，省略中间平滑移动，因此部分切换较突然。新版还修正了一张同宽高比大图误用全幅缩放的问题。原作指令证据和实现范围见同名“画面与镜头说明.md”。

{m['versionName']} 可直接覆盖先前版本；正文位置、应用标识与存档键保持一致。已验证旧版 01／30 号存档兼容，勿为了更新先卸载。

如应用异常，先退出重开，再重启手表，必要时单独重装本应用。卸载可能清除存档。如果其他原先正常的应用也无法安装，应先重启手表及手机工具、等待安装服务恢复；最后才考虑同步数据后恢复出厂设置，重置会清除本地应用和存档。

SHA-256：{sha}

源码和说明另见 {name}-源码.zip；原游戏素材与译文保留各自权利，自编代码采用 MIT。由 Codex 完成工程实现、转换与检查。
'''
(OUT/(name+'-安装说明.md')).write_text(notes,encoding='utf8')
for a,b in [('native-test-results/title.png','-标题.png'),('native-test-results/title-after-reopen.png','-通关后标题.png'),('native-test-results/story-patch.png','-剧情.png'),('reports/image-quality-comparison.png','-画质对比.png'),('reports/text-card-comparison.png','-字卡对比.png'),('reports/gallery013-notes.md','-鉴赏优化说明.md'),('reports/visual012-notes.md','-画面与镜头说明.md'),('src/common/logo.png','-图标.png'),('native-test-results/gallery-low-memory.png','-鉴赏列表.png'),('native-test-results/cg-low-memory.png','-鉴赏实屏.png'),('native-test-results/auto-menu.png','-自动播放菜单.png'),('native-test-results/regression-after.png','-字卡实屏.png'),('native-test-results/text-card-long.png','-长字卡实屏.png')]:
    if is014 and a=='native-test-results/gallery-low-memory.png':a='native-test-results/gallery.png'
    if is014 and a=='native-test-results/cg-low-memory.png':a='native-test-results/cg.png'
    shutil.copyfile(ROOT/a,OUT/(name+b))
sourceZip=OUT/(name+'-源码.zip')
with zipfile.ZipFile(sourceZip,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    files=[]
    for folder in ['src','tools','tests','reports','licenses','art']:
        for p in (ROOT/folder).rglob('*'):
            if p.is_file() and not any(x in ['node_modules','__pycache__'] for x in p.parts) and p.suffix not in ['.pem','.key','.pyc','.log']:files.append(p)
    files += [ROOT/n for n in ['README.md','LICENSE','requirements.txt','package.json','quickapp.config.js','.gitignore','THIRD_PARTY_NOTICES.md']]
    files += [ROOT/'native-test-results'/n for n in ['report.json','cold-report.json','title.png','story-patch.png','long-text-top.png','long-text-bottom.png','gallery.png','cg.png','cg-difference.png','chapter-first-0.png','cold-save-01.png','auto-menu.png','auto-stopped-menu.png','text-card.png','corrected-camera.png','regression-before.png','regression-after.png','text-card-long.png','text-card-b002-start.png','gallery-stress-report.json','gallery-low-memory.png','cg-low-memory.png','gallery-largest-group.png']]
    if is014:files += [ROOT/'native-test-results'/n for n in ['title-after-reopen.png','baseline013/gallery-stress-report.json','baseline013/report.json','baseline013/cold-report.json']]
    for p in sorted(files):
        if p.name.startswith('original-topmenu') or (is014 and p==ROOT/'native-test-results/gallery-stress-report.json'):continue
        z.write(p,'eden-rw5/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(sourceZip) as z:
    assert z.testzip() is None
    assert not any(n.endswith(('.pem','.key','.exe','.dll','.paz','.pyc')) or '/node_modules/' in n for n in z.namelist())
checks=[]
for p in sorted(OUT.glob(name+'*')):
    if p.name.endswith('-SHA256.txt'):continue
    checks.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name)
(OUT/(name+'-SHA256.txt')).write_text('\n'.join(checks)+'\n',encoding='utf8')
print(json.dumps({'packageBytes':len(data),'sha256':sha,'sourceZipBytes':sourceZip.stat().st_size,'outputs':[p.name for p in sorted(OUT.glob(name+'*'))]},ensure_ascii=False))
