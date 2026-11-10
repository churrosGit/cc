"""Make a narration file with Microsoft Edge's read-aloud voices (edge-tts).
Usage: python3 tts.py <narration.txt> <out.wav> [voice] [rate]
  voice: ko-KR-SunHiNeural (female), ko-KR-InJoonNeural (male), ko-KR-HyunsuMultilingualNeural (male)
  rate: e.g. +22% (about 47 s for a 350-character script)
Needs: pip install edge-tts. In cloud sessions the proxy's CA bundle is used (edge-tts pins certifi's own)."""
import os, subprocess, sys, tempfile
import certifi
if os.path.exists('/root/.ccr/ca-bundle.crt'):
    certifi.where = lambda: '/root/.ccr/ca-bundle.crt'
import edge_tts

src, out = sys.argv[1:3]
voice = sys.argv[3] if len(sys.argv) > 3 else 'ko-KR-SunHiNeural'
rate = sys.argv[4] if len(sys.argv) > 4 else '+22%'
mp3 = tempfile.mktemp(suffix='.mp3')
edge_tts.Communicate(open(src, encoding='utf-8').read(), voice, rate=rate).save_sync(mp3)
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', mp3, '-ar', '48000', '-ac', '1', out], check=True)
os.remove(mp3)
print(out, subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out],
                          capture_output=True, text=True).stdout.strip(), 's')
