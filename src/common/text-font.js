const missing="呣";
export function textFont(text){
  const value=String(text||'');for(let i=0;i<missing.length;i++)if(value.indexOf(missing[i])>=0)return 'edenextra';return 'sans-serif';
}
