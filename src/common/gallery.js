import {frames,baseLayer,frameLayer} from './assets.js';
export const galleryInfo={"groups":295,"variants":2341,"pages":74,"pageSize":4};
export function groupGallery(items){const groups=[],by={};for(const item of items){const id=item.group||item.source;let g=by[id];if(!g){g={id,image:item.image,label:item.label,variants:[]};by[id]=g;groups.push(g);}g.variants.push(item);}return groups;}
export function stepVariant(index,delta,count){return count?((index+delta)%count+count)%count:0;}
export function galleryLayer(name,patch){const f=frames[name];if(!f)return {src:''};const w=Math.min(264,f.size[0]),h=Math.min(270,f.size[1]),layer=patch?frameLayer(name,w,h):baseLayer(name,w,h);layer.left+=Math.round((432-w)/2);layer.top+=Math.round((432-h)/2);return layer;}
