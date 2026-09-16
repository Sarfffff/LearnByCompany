# -*- coding: utf-8 -*-
"""拉取 B 站 AI 字幕。用法：
   python fetch_sub.py          # 全部 114 集
   python fetch_sub.py 8 9 10   # 仅指定集
需先在 tools/sessdata.txt 放入 SESSDATA。
"""
import urllib.request, urllib.parse, json, os, sys, time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SESSDATA = open(os.path.join(BASE, 'tools', 'sessdata.txt'), encoding='utf-8').read().strip()

UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
      'Referer': 'https://www.bilibili.com/'}

def api(url):
    req = urllib.request.Request(url, headers={**UA, 'Cookie': f'SESSDATA={SESSDATA}'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fmt(sec):
    m, s = divmod(int(sec), 60)
    return f'{m:02d}:{s:02d}'

meta = json.load(open(os.path.join(BASE, '_meta.json'), encoding='utf-8'))
pages = meta['pages']
BVID = meta['bvid']

want = {int(a) for a in sys.argv[1:]} if len(sys.argv) > 1 else None
os.makedirs(os.path.join(BASE, 'subtitles'), exist_ok=True)

ok, fail = 0, []
for p in pages:
    pg, cid = p['page'], p['cid']
    if want and pg not in want:
        continue
    out_json = os.path.join(BASE, 'subtitles', f'P{pg}.json')
    if os.path.exists(out_json):
        ok += 1
        continue
    try:
        d = api(f'https://api.bilibili.com/x/player/v2?bvid={BVID}&cid={cid}')
        subs = d.get('data', {}).get('subtitle', {}).get('subtitles', [])
        if not subs:
            print(f'P{pg}: 无字幕')
            fail.append((pg, 'no-sub'))
            continue
        saved = []
        for s in subs:
            lan = s.get('lan', '')
            surl = s['subtitle_url']
            if surl.startswith('//'):
                surl = 'https:' + surl
            body = api(surl)  # 字幕 json 本身也是 json
            fn = os.path.join(BASE, 'subtitles', f'P{pg}-{lan}.json')
            with open(fn, 'w', encoding='utf-8') as f:
                json.dump(body, f, ensure_ascii=False)
            saved.append((lan, len(body.get('body', []))))
        # 生成可读 txt（取第一个字幕轨）
        lan = subs[0].get('lan', '')
        src = os.path.join(BASE, 'subtitles', f'P{pg}-{lan}.json')
        body = json.load(open(src, encoding='utf-8'))['body']
        with open(out_json, 'w', encoding='utf-8') as f:
            json.dump(body, f, ensure_ascii=False)
        with open(os.path.join(BASE, 'subtitles', f'P{pg}.txt'), 'w', encoding='utf-8') as f:
            for it in body:
                f.write(f'[{fmt(it["from"])}] {it["content"]}\n')
        ok += 1
        print(f'P{pg}: ok {saved}')
    except Exception as e:
        print(f'P{pg}: FAIL {e}')
        fail.append((pg, str(e)))
    time.sleep(0.4)

print(f'\ndone ok={ok} fail={len(fail)}')
for pg, e in fail:
    print(' ', pg, e)
