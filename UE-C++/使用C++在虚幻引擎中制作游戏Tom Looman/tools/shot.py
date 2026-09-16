# -*- coding: utf-8 -*-
"""从 B 站视频流直接截帧（不下载整个视频）。用法：
   python shot.py <集数P> <秒数或mm:ss> <输出名（不含扩展名）>
   python shot.py 8 600 P8-01
需先在 tools/sessdata.txt 放入 SESSDATA。
"""
import urllib.request, json, os, sys, subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSDATA = open(os.path.join(BASE, 'tools', 'sessdata.txt'), encoding='utf-8').read().strip()

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Referer': 'https://www.bilibili.com/'}

def api(url):
    req = urllib.request.Request(url, headers={**UA, 'Cookie': f'SESSDATA={SESSDATA}'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

import imageio_ffmpeg
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

pg = sys.argv[1]
pos = sys.argv[2]           # 秒数 或 mm:ss
name = sys.argv[3]

meta = json.load(open(os.path.join(BASE, '_meta.json'), encoding='utf-8'))
BVID = meta['bvid']
cid = [p for p in meta['pages'] if p['page'] == int(pg)][0]['cid']

d = api(f'https://api.bilibili.com/x/player/playurl?bvid={BVID}&cid={cid}&qn=116&fnval=16&fourk=1')
videos = d['data']['dash']['video']
# 选最高清晰度、avc 编码优先（兼容性好）
best = max(videos, key=lambda v: (v.get('height', 0), -v.get('bandwidth', 0)))
url = best['baseUrl']
w, h = best.get('width'), best.get('height')

out = os.path.join(BASE, 'Img', f'{name}.jpg')
cmd = [FFMPEG, '-hide_banner', '-loglevel', 'error',
       '-ss', pos,
       '-headers', 'Referer: https://www.bilibili.com/\r\nUser-Agent: ' + UA['User-Agent'] + '\r\n',
       '-i', url,
       '-frames:v', '1', '-q:v', '2', '-y', out]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
if r.returncode != 0:
    print('FAIL:', r.stderr[:300])
else:
    print(f'ok {w}x{h} -> {out} ({os.path.getsize(out)} bytes)')
