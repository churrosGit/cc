"""Builds a capture-based shorts video.
Usage: python3 build.py <projectDir> <capDir> <narration.wav> <out.mp4>
<projectDir> holds plan.json and txt/ (from ov_render.js); <capDir> holds the capture PNGs named in plan.json.
Segment types: pieces, montage, text, img, split, video, meme. plan["audio"] mixes extra sounds over the narration."""
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
        # each item: a clean horizontal slice [a,b] of a capture, shown whole on the 4:3 canvas with a blur fill;
        # optional "ko": {"img": layer, "lines": [[y0,y1,x0,x1],...], "bounce": [[t0,t1,[line idx]]], "pop": 0.08}
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
            ins = ['-loop', '1', '-framerate', str(fps), '-i', os.path.join(cap, it['img'] + '.png')]
            ko = it.get('ko')
            if ko:
                # interlinear Korean layer (transparent PNG at the same coordinates). Lines sit still, except during
                # each "bounce" entry [t0, t1, [line idx]]: those lines are cut out together as ONE group image and
                # pop out toward the viewer as a unit (grow by up to 'pop', default 8%, around the group's centre;
                # abs(sin(2*pi*t)) = 2 pops per second), so lines read together always pop in sync.
                from PIL import Image
                kf = min(1, H / h)
                fw, fh = round(W * kf), round(h * kf)
                fx, fy = (W - fw) // 2, (H - fh) // 2
                pop = ko.get('pop', 0.08)
                layer = Image.open(os.path.join(cap, ko['img'] + '.png')).convert('RGBA')
                lines = [(ln[0], ln[1], ln[2], ln[3]) if len(ln) > 3 else (ln[0], ln[1], 0, W) for ln in ko['lines']]
                bounces = ko.get('bounce', [])

                def box(idx):  # union box of some lines (source px), padded
                    return (max(0, min(lines[j][2] for j in idx) - 12), max(0, min(lines[j][0] for j in idx) - 8),
                            min(W, max(lines[j][3] for j in idx) + 12), min(layer.height, max(lines[j][1] for j in idx) + 8))

                fc = fc.replace(',format=yuv420p[v]', '[b0]')
                cur_l, nin = 'b0', 1
                for j in range(len(lines)):
                    busy = '+'.join(f'between(t,{b0},{b1})' for b0, b1, idx in bounces if j in idx)
                    g = os.path.join(segdir, f'ko{i:02d}_{k}_l{j}.png')
                    layer.crop(box([j])).save(g)
                    x0, y0, x1, y1 = box([j])
                    ins += ['-i', g]
                    en = f":enable='not({busy})'" if busy else ''
                    fc += (f";[{nin}:v]scale={round((x1 - x0) * kf)}:{round((y1 - y0) * kf)}[s{nin}];"
                           f"[{cur_l}][s{nin}]overlay={fx + round((x0) * kf)}:{fy + round((y0 - a) * kf)}{en}[o{nin}]")
                    cur_l = f'o{nin}'; nin += 1
                for q, (b0, b1, idx) in enumerate(bounces):
                    x0, y0, x1, y1 = box(idx)
                    grp = Image.new('RGBA', (x1 - x0, y1 - y0))
                    for j in idx:  # only the listed lines, even if others lie between them
                        lb = box([j]); grp.alpha_composite(layer.crop(lb), (lb[0] - x0, lb[1] - y0))
                    g = os.path.join(segdir, f'ko{i:02d}_{k}_g{q}.png'); grp.save(g)
                    sw, sh = round((x1 - x0) * kf), round((y1 - y0) * kf)
                    cx, cy = fx + (x0 * kf) + sw / 2, fy + (y0 - a) * kf + sh / 2
                    f = f"(1+{pop}*abs(sin(2*PI*t)))"
                    ins += ['-loop', '1', '-framerate', str(fps), '-i', g]
                    fc += (f";[{nin}:v]scale={sw * 2}:{sh * 2},format=rgba,"
                           f"scale=w='trunc({sw}*{f}/2)*2':h='trunc({sh}*{f}/2)*2':eval=frame:flags=bicubic[s{nin}];"
                           f"[{cur_l}][s{nin}]overlay=x='{cx:.1f}-w/2':y='{cy:.1f}-h/2':eval=frame:enable='between(t,{b0},{b1})'[o{nin}]")
                    cur_l = f'o{nin}'; nin += 1
                fc += f";[{cur_l}]format=yuv420p[v]"
            run(ins + ['-filter_complex', fc, '-map', '[v]', '-frames:v', str(m)] + ENC + [o])
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
    if s['type'] == 'meme':
        # meme image centered, aspect kept, scaled to about 95% of the 4:3 area, blur fill behind
        src = s['src'] if os.path.isabs(s['src']) else os.path.join(d, s['src'])
        mw, mh = round(W * 0.95), round(H * 0.95)
        fc = (f"[0:v]split[f][g];"
              f"[g]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=34,"
              f"colorlevels=romax=0.82:gomax=0.82:bomax=0.82[bg];"
              f"[f]scale={mw}:{mh}:force_original_aspect_ratio=decrease:flags=lanczos[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]")
        run(['-loop', '1', '-framerate', str(fps), '-i', src, '-filter_complex', fc, '-map', '[v]',
             '-frames:v', str(n)] + ENC + [o])
        parts.append(o)
        print('seg', i, 'meme', n, 'frames')
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
