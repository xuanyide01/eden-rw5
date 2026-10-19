import {catalog} from './catalog.js';
function clone(value){return JSON.parse(JSON.stringify(value));}
export function newState(chapter,story){const id=chapter||catalog.initial;return {chapter:id,rootChapter:id,cursor:0,background:'',regularBackground:'',body:'',bodies:[],speaker:'',text:'',choices:[],history:[],variables:{},ended:false,progression:story?'story':'chapter'};}
export function checkpoint(s){const copy=Object.assign({},s);delete copy.history;return clone(copy);}
export function restore(saved){
 if(!saved||!catalog.scenes[String(saved.chapter)]||!Number.isInteger(saved.cursor)||saved.cursor<0||saved.cursor>=catalog.scenes[String(saved.chapter)].length)throw Error('存档位置无效');
 if(!catalog.scenes[String(saved.rootChapter)]||!saved.variables||typeof saved.variables!=='object'||Array.isArray(saved.variables))throw Error('存档状态无效');
 return Object.assign(newState(),clone(saved),{history:[],bodies:[]});
}
function compare(left,operator,right){if(operator==='==')return left===right;if(operator==='<=')return left<=right;throw Error('未支持的条件');}
export function readFrame(ops,s,base,total){
 base=base||0;total=total===undefined?ops.length:total;
 for(let steps=0;steps<64;steps++){
  if(s.cursor>=total){s.ended=true;return {type:'end'};}
  const local=s.cursor-base;if(local<0||local>=ops.length)return {type:'yield'};
  const op=ops[local];
  if(op.op==='text'){s.speaker=op.speaker;s.text=op.text;s.background=op.background;s.regularBackground=op.background;s.bodies=[];return {type:'text',speaker:s.speaker,text:s.text};}
  if(op.op==='set'){s.variables[op.key]=op.value;s.cursor++;continue;}
  if(op.op==='if'){s.cursor=compare(s.variables[op.key]||0,op.compare,op.value)?op.to:s.cursor+1;continue;}
  if(op.op==='goto'){s.cursor=op.to;continue;}
  if(op.op==='jumpScene'){
   if(!catalog.scenes[String(op.scene)])throw Error('剧情跳转无效');
   s.chapter=op.scene;s.rootChapter=op.scene;s.cursor=0;return {type:'jump'};
  }
  // Choice handling remains explicit: chapter skipping must never choose for a player.
  if(op.op==='choice')return {type:'choice',items:op.items};
  if(op.op==='end'){s.ended=true;return {type:'end'};}
  throw Error('剧情指令无效');
 }
 return {type:'yield'};
}
function remember(s){s.history.push(checkpoint(s));if(s.history.length>8)s.history.shift();}
export function next(s){if(s.ended)return;remember(s);s.cursor++;}
export function previous(s){const last=s.history.pop();if(!last)return false;const history=s.history;Object.assign(s,last,{history});return true;}
export function choose(s,item,index){if(!item||!Number.isInteger(item.to)||item.to<0||item.to>=catalog.scenes[String(s.chapter)].length)throw Error('选项无效');remember(s);s.choices.push(index);s.cursor=item.to;s.ended=false;}
export function nextChapter(s){if(s.ended)return null;remember(s);return {chapter:s.rootChapter};}
export function readChapterSkip(ops,s,context,base,total){
 for(let count=0;count<64;count++){const frame=readFrame(ops,s,base,total);if(frame.type!=='text'||s.rootChapter!==context.chapter)return frame;s.cursor++;}
 return {type:'yield'};
}
export function previewMap(){return [];}
