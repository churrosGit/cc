"""Narration with edge-tts (ko-KR-InJoonNeural, +22%), one sentence at a time so the word timings are exact.
Usage: python3 make_audio.py <workDir>   -> <workDir>/narration.wav and ./words.json
Each sentence is trimmed to its speech (+0.12 s), then joined with GAP of silence; the result is levelled to -16 LUFS."""
import json, os, subprocess, sys
import certifi
if os.path.exists('/root/.ccr/ca-bundle.crt'):
    certifi.where = lambda: '/root/.ccr/ca-bundle.crt'
import edge_tts

work = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
os.makedirs(work, exist_ok=True)
VOICE, RATE, LEAD, GAP, TAIL = 'ko-KR-InJoonNeural', '+22%', 0.15, 0.35, 0.12


def ff(args):
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y'] + args, check=True)


lines = [l.strip() for l in open(os.path.join(here, 'narration.txt'), encoding='utf-8') if l.strip()]
parts, out, t = [], [], LEAD
for k, line in enumerate(lines):
    mp3 = os.path.join(work, f's{k:02d}.mp3')
    audio, words = b'', []
    for ch in edge_tts.Communicate(line, VOICE, rate=RATE, boundary='WordBoundary').stream_sync():
        if ch['type'] == 'audio':
            audio += ch['data']
        else:
            words.append([ch['offset'] / 1e7, (ch['offset'] + ch['duration']) / 1e7, ch['text']])
    open(mp3, 'wb').write(audio)
    a, b = max(words[0][0] - 0.05, 0), words[-1][1] + TAIL
    wav = os.path.join(work, f's{k:02d}.wav')
    ff(['-i', mp3, '-af', f'atrim={a}:{b},asetpts=N/SR/TB', '-ar', '48000', '-ac', '1', wav])
    out.append({'text': line, 'start': round(t, 3), 'end': round(t + b - a, 3),
                'words': [[round(t + w0 - a, 3), round(t + w1 - a, 3), w] for w0, w1, w in words]})
    parts.append(wav)
    t += b - a + GAP
dur = t - GAP + 0.6
inp = ['-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=mono:d={LEAD}']
for p in parts:
    inp += ['-i', p, '-f', 'lavfi', '-i', f'anullsrc=r=48000:cl=mono:d={GAP}']
n = 1 + 2 * len(parts)
ff(inp + ['-filter_complex', ''.join(f'[{i}:a]' for i in range(n)) + f'concat=n={n}:v=0:a=1,apad=whole_dur={dur},'
          'loudnorm=I=-16:TP=-1.5:LRA=11[o]', '-map', '[o]', '-ar', '48000', '-ac', '1', os.path.join(work, 'narration.wav')])
json.dump({'duration': round(dur, 2), 'sentences': out}, open(os.path.join(here, 'words.json'), 'w'), ensure_ascii=False, indent=1)
for s in out:
    print(f"{s['start']:6.2f}-{s['end']:6.2f} {s['text']}")
print('total', round(dur, 2))
