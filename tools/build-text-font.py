"""Build the OFL font subset needed by text missing from Vela's default font.

python tools/build-text-font.py NotoSansMonoCJKsc-Regular.otf [--default-font FONT]
The optional default font is read only, for coverage analysis, and not distributed.
Later builds reuse reports/text-font.json. Requires fontTools.
"""
import argparse,json,re
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('source');parser.add_argument('--default-font');args=parser.parse_args()
strings=[]
def visit(value):
    if isinstance(value,str):strings.append(value.replace('・','·'))
    elif isinstance(value,list):
        for item in value:visit(item)
    elif isinstance(value,dict):
        for item in value.values():visit(item)
for path in (root/'src/common/story').rglob('*.txt'):visit(json.loads(path.read_text(encoding='utf-8')))
visit(json.loads((root/'reports/gallery-source.json').read_text(encoding='utf-8')))
catalog=(root/'src/common/catalog.js').read_text(encoding='utf-8')
visit(json.loads(catalog.removeprefix('export const catalog=').strip().removesuffix(';')))
cards=json.loads((root/'tools/text-card-content.json').read_text('utf8'))
visit([c['text'] for c in cards.values()])
report_path=root/'reports/text-font.json'
if args.default_font:
    default_cmap=TTFont(args.default_font).getBestCmap()
    triggers=sorted({ch for value in strings for ch in value if not ch.isspace() and ord(ch)>=32 and ord(ch) not in default_cmap})
else:triggers=json.loads(report_path.read_text(encoding='utf-8'))['missingDefaultGlyphs']
trigger_set=set(triggers);affected=[s for s in strings if trigger_set.intersection(s)]
chars=set(chr(i) for i in range(32,127))
for value in affected:chars.update(value)
# Save metadata/confirmation and labels add these characters around original text.
chars.update((root/'src/pages/index/index.ux').read_text(encoding='utf-8'))
chars.update((root/'src/common/saves.js').read_text(encoding='utf-8'))
chars.update(catalog)
options=subset.Options();options.name_IDs=['*'];options.name_languages=['*']
font=subset.load_font(args.source,options);original_map=font.getBestCmap()
unsupported=sorted(ch for ch in chars if not ch.isspace() and ord(ch)>=32 and ord(ch) not in original_map)
assert not unsupported,repr(unsupported)
coverage={ord(ch) for ch in chars if ord(ch) in original_map}
subsetter=subset.Subsetter(options=options);subsetter.populate(unicodes=coverage);subsetter.subset(font)
for record in font['name'].names:
    if record.nameID in (1,3,4,6,16):record.string='EdenExtraSubset'.encode(record.getEncoding(),errors='replace')
if 'CFF ' in font:font['CFF '].cff.fontNames=['EdenExtraSubset']
output=root/'src/common/eden-extra.otf';subset.save_font(font,str(output),options)
assert set(TTFont(output).getBestCmap())==coverage
report={'font':'EdenExtraSubset','sourceFamily':'Noto Sans Mono CJK SC','license':'SIL OFL 1.1','missingDefaultGlyphs':triggers,'affectedStrings':len(affected),'codepoints':sorted(coverage),'fontBytes':output.stat().st_size,'conditionalFont':True}
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(root/'src/common/text-font.js').write_text('const missing='+json.dumps(''.join(triggers),ensure_ascii=False)+';\nexport function textFont(text){\n  const value=String(text||\'\');for(let i=0;i<missing.length;i++)if(value.indexOf(missing[i])>=0)return \'edenextra\';return \'sans-serif\';\n}\n',encoding='utf-8')
print('TEXT_FONT',len(coverage),output.stat().st_size,'affected',len(affected),'triggers',len(triggers))

