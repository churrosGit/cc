"""Builds a capture-based shorts video.
Usage: python3 build.py <projectDir> <capDir> <narration.wav> <out.mp4>
<projectDir> holds plan.json and txt/ (from ov_render.js); <capDir> holds the capture PNGs named in plan.json.
Segment types: pieces, montage, text, img, split, video. plan["audio"] mixes extra sounds over the narration."""
import json, os, subprocess, sys

d, cap, audio, out = sys.argv[1:5]
plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8'))
fps, W, H = plan['fps'], 1080, plan['content_h']
segdir = os.path.join(d, 'seg'); os.makedirs(segdir, exist_ok=True)
ENC = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '12', '-pix_fmt', 'yuv420p', '-r', str(fps)]

def run(args):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y'] + args, check=True)

def still(img, n, o, vf):
    run(['-loop', '1', '-framerate', str(fps), '-i', img, '-vf', vf + ',format=yuv420p', '-frames:v', str(n)] + ENC + [o])

parts = []
segs = plan['segments']
for i, s in enumerate(segs):
    end = segs[i + 1]['start'] if i + 1 < len(segs) else plan['duration']
    f0, f1 = round(s['start'] * fps), round(end * fps)
    n = f1 - f0
    if s['type'] == 'pieces':
        # each item: a clean horizontal slice [a,b] of a capture, shown whole on the 4:3 canvas with a blur fill
        items = s['items']
        wts = [it.get('w', 1) for it in items]
        alloc = [round(n * w / sum(wts)) for w in wts]
        alloc[-1] = n - sum(alloc[:-1])
        for k, (it, m) in enumerate(zip(items, alloc)):
            a, b = it['y']
            h = b - a
            fg = 'null' if h <= H else f'scale=-2:{H}'
            fc = (f"[0:v]crop={W}:{h}:0:{a},split[f][g];"
                  f"[g]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=34,"
                  f"colorlevels=romax=0.82:gomax=0.82:bomax=0.82[bg];"
                  f"[f]{fg}[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
            o = os.path.join(segdir, f'seg{i:02d}_{k}.mp4')
            run(['-loop', '1', '-framerate', str(fps), '-i', os.path.join(cap, it['img'] + '.png'),
                 '-filter_complex', fc, '-map', '[v]', '-frames:v', str(m)] + ENC + [o])
            parts.append(o)
        print('seg', i, 'pieces', alloc)
        continue
    if s['type'] == 'montage':
        step = round(s['step'] * fps)
        for k, name in enumerate(s['imgs']):
            m = step if k < len(s['imgs']) - 1 else n - step * (len(s['imgs']) - 1)
            o = os.path.join(segdir, f'seg{i:02d}_{k}.mp4')
            still(os.path.join(cap, name + '.png'), m, o, f'crop={W}:{H}:0:0')
            parts.append(o)
        continue
    o = os.path.join(segdir, f'seg{i:02d}.mp4')
    if s['type'] == 'video':
        # a clip (any aspect) fit to the 4:3 canvas height with a blur fill; its sound is added via plan['audio']
        src = s['src'] if os.path.isabs(s['src']) else os.path.join(d, s['src'])
        fc = (f"[0:v]fps={fps},split[f][g];"
              f"[g]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=34,"
              f"colorlevels=romax=0.82:gomax=0.82:bomax=0.82[bg];"
              f"[f]scale=-2:{H}[fg];[bg][fg]overlay=(W-w)/2:0,format=yuv420p[v]")
        run(['-ss', str(s.get('from', 0)), '-i', src, '-filter_complex', fc, '-map', '[v]', '-an',
             '-frames:v', str(n)] + ENC + [o])
        parts.append(o)
        print('seg', i, 'video', n, 'frames')
        continue
    if s['type'] == 'text':
        still(os.path.join(d, 'txt', f'card{i}.png'), n, o, 'null')
    elif s['type'] == 'img':
        D, P, y0, wh = n / fps, s['pan'], s.get('y0', 0), s.get('wh', H)
        c = f"clip((t-0.3)/{max(D - 0.6, 0.1):.3f},0,1)"
        vf = f"crop={W}:{wh}:0:'{y0}+{P}*(3*pow({c},2)-2*pow({c},3))'"
        if wh != H:
            vf += f",scale=-2:{H},pad={W}:{H}:(ow-iw)/2:0:white"
        still(os.path.join(cap, s['img'] + '.png'), n, o, vf)
    elif s['type'] == 'split':
        a, b = (os.path.join(cap, x + '.png') for x in s['imgs'])
        fc = (f"color=white:s={W}x{H}:r={fps}[bg];[0:v]scale=530:-1[l];[1:v]scale=530:-1[r];"
              f"[bg][l]overlay=6:(H-h)/2[t];[t][r]overlay=544:(H-h)/2,format=yuv420p[v]")
        run(['-loop', '1', '-framerate', str(fps), '-i', a, '-loop', '1', '-framerate', str(fps), '-i', b,
             '-filter_complex', fc, '-map', '[v]', '-frames:v', str(n)] + ENC + [o])
    parts.append(o)
    print('seg', i, s['type'], n, 'frames')

lst = os.path.join(segdir, 'list.txt')
open(lst, 'w').write(''.join(f"file '{p}'\n" for p in parts))
content = os.path.join(segdir, 'content.mp4')
run(['-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', content])

subs = plan['subs']
inputs = ['-f', 'lavfi', '-i', f"color=black:s=1080x1920:r={fps}:d={plan['duration']}",
          '-i', content, '-i', audio, '-loop', '1', '-i', os.path.join(d, 'txt', 'title.png')]
for k in range(len(subs)):
    inputs += ['-loop', '1', '-i', os.path.join(d, 'txt', f'sub{k:02d}.png')]
fc = f"[0:v][1:v]overlay=0:{plan['content_y']}:shortest=1[c0];[c0][3:v]overlay=0:0:shortest=1[c1]"
cur = 'c1'
for k, (st, _) in enumerate(subs):
    en = subs[k + 1][0] if k + 1 < len(subs) else plan['duration'] + 1
    fc += f";[{cur}][{4 + k}:v]overlay=0:0:shortest=1:enable='gte(t,{st})*lt(t,{en})'[s{k}]"
    cur = f's{k}'
# extra sounds (clip sound, sfx): plan['audio'] = [{"src", "at", "from", "dur", "gain_db", "fade"}]
extra = plan.get('audio', [])
amap = '2:a'
if extra:
    base = 4 + len(subs)
    labels = ['[2:a]aresample=48000,aformat=channel_layouts=stereo[a0]']
    for k, a in enumerate(extra):
        src = a['src'] if os.path.isabs(a['src']) else os.path.join(d, a['src'])
        inputs += ['-i', src]
        fd, dur = a.get('fade', 0.15), a['dur']
        labels.append(f"[{base + k}:a]atrim={a.get('from', 0)}:{a.get('from', 0) + dur},asetpts=N/SR/TB,"
                      f"aresample=48000,aformat=channel_layouts=stereo,volume={a.get('gain_db', 0)}dB,"
                      f"afade=t=in:d={fd},afade=t=out:st={max(dur - fd, 0)}:d={fd},"
                      f"adelay={int(a['at'] * 1000)}:all=1[a{k + 1}]")
    mix = ''.join(f'[a{k}]' for k in range(len(extra) + 1))
    fc += ';' + ';'.join(labels) + f";{mix}amix=inputs={len(extra) + 1}:duration=first:normalize=0,alimiter=limit=0.95[aout]"
    amap = '[aout]'
run(inputs + ['-filter_complex', fc, '-map', f'[{cur}]', '-map', amap,
              '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-r', str(fps),
              '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', str(plan['duration']),
              '-movflags', '+faststart', out])
print('final:', out)
