const path = require('path');
const fs = require('fs');
const { VvdManager, VelaImageType, SDKParts, IVvdArchType } = require('@aiot-toolkit/emulator');
const home = process.env.STARRY_EMULATOR_HOME || path.resolve(__dirname, '../.emulator');
const manager = new VvdManager({ sdkHome: process.env.WATCH_SDK_HOME||path.join(home, 'sdk'), vvdHome: path.join(home, 'vvd') });
(async () => {
  // Download the custom-size image and only the host tools this instance uses.
  manager.hasSDKPartUpdate = async () => [SDKParts.EMULATOR, SDKParts.QA, SDKParts.SKINS, SDKParts.MODEM_SIMULATOR]
    .filter(part => !fs.existsSync(manager.getSDKPart(part)));
  const parts=await manager.hasSDKPartUpdate();
  if(parts.length || !fs.existsSync(manager.getLocalSystemPath(VelaImageType.VELA_WATCH_5)||'')) {
    const dl = await manager.downloadSDK({ cliProgress: false, parallelDownloads: 4, parallelStreams: 3,
      imageTypeArr: [VelaImageType.VELA_WATCH_5] });
    let last = 0;
    dl.on('progress', p => { if (Date.now() - last > 12000) { last = Date.now(); console.log('SDK', p.formattedPercentage, p.formatTotal, p.formattedSpeed); }});
    await dl.downlodPromise;
  }
  const name = process.env.WATCH_VVD_NAME || 'EdenRW5-432x514';
  if (!manager.getVvdList().some(x => x.name === name || x.vvdName === name)) {
    manager.createVvd({ name, arch: IVvdArchType.arm, width: '432', height: '514', density: '320',
      shape: 'rect', flavor: 'watch', customLcdRadius: '20', imageType: VelaImageType.VELA_WATCH_5,
      imageDir: path.dirname(manager.getLocalSystemPath(VelaImageType.VELA_WATCH_5)) });
  }
  const config=path.join(manager.vvdHome,name+'.vvd/config.ini');
  fs.writeFileSync(config,fs.readFileSync(config,'utf8').replace(/^hw.ramSize=.*$/m,'hw.ramSize=128'));
  // The Windows Vela launcher ignores ANDROID_AVD_HOME for VVD lookup.
  // Register only this device in its default folder; the images stay in home.
  const registration = path.join(require('os').homedir(), '.vela', 'vvd');
  fs.mkdirSync(registration,{recursive:true});
  const ini=path.join(registration,name+'.ini');
  const source=fs.readFileSync(path.join(manager.vvdHome,name+'.ini'));
  if(fs.existsSync(ini)&&!fs.readFileSync(ini).equals(source))throw new Error('An existing device has the same name: '+ini);
  fs.writeFileSync(ini,source);
  console.log('READY', home, JSON.stringify(manager.getVvdList()));
})().catch(e => { console.error(e); process.exitCode = 1; });

