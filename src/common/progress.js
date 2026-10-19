export const PROGRESS_KEY='eden_rw5_progress_v1';
export function emptyProgress(){return {version:1,variables:{}};}
export function decodeProgress(raw){if(!raw)return emptyProgress();const p=typeof raw==='string'?JSON.parse(raw):raw;if(!p||p.version!==1||!p.variables||typeof p.variables!=='object'||Array.isArray(p.variables))throw Error('通关记录格式无效');const variables={};for(const key of Object.keys(p.variables))if(/^sf\.\w+(?:\[\d+\])?$/.test(key)&&['number','boolean'].indexOf(typeof p.variables[key])>=0)variables[key]=p.variables[key];return {version:1,variables};}
export function progressFromState(s){const variables={};for(const key of Object.keys(s.variables))if(key.indexOf('sf.')===0)variables[key]=s.variables[key];return {version:1,variables};}
export function withProgress(s,p){for(const key of Object.keys(p.variables))s.variables[key]=p.variables[key];return s;}
