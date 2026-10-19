from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
sheet=Image.new('RGB',(928,622),'#edf0f7');d=ImageDraw.Draw(sheet)
d.text((24,15),'《eden》同一剧情画面：图片文字 → 原生文字',font=font,fill='#262e4c')
d.text((24,52),'0.1.1',font=small,fill='#68728e');d.text((472,52),'0.1.2：自动换行，去除内部章节代码',font=small,fill='#68728e')
for file,x in [('regression-before.png',24),('regression-after.png',472)]:
 im=Image.open(ROOT/'native-test-results'/file).convert('RGB');assert im.size==(432,514);sheet.paste(im,(x,84))
sheet.save(ROOT/'reports/text-card-comparison.png');print('NATIVE_COMPARISON_READY')
