"""
本地一鍵轉錄腳本（請在你自己的電腦上執行，需要網路下載模型約 1.5GB）
用法：python scripts/transcribe_wav_local.py
"""
from pathlib import Path
import sys

try:
    import whisper
except ImportError:
    print("請先執行：pip install openai-whisper")
    sys.exit(1)

WAV = Path("raw/wav/愛鄉之聲電臺_pcm16.wav")  # PCM 格式，Whisper 處理更快
if not WAV.exists():
    WAV = Path("raw/wav/第一題題目-愛鄉之聲電臺.wav")  # fallback 原始檔

OUT_DIR = Path("skills/cameo-interview/references/wav")
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_FILE = OUT_DIR / "第一題題目-愛鄉之聲電臺.md"

print(f"載入模型（medium，首次執行需下載約 1.5GB）...")
model = whisper.load_model("medium")

print(f"開始轉錄 {WAV.name}（約 20-30 分鐘）...")
result = model.transcribe(str(WAV), language="zh", verbose=True, task="transcribe")

# 整理成 markdown
segments = []
for seg in result["segments"]:
    t = seg["start"]
    mm, ss = divmod(int(t), 60)
    hh, mm2 = divmod(mm, 60)
    ts = f"{hh:02d}:{mm2:02d}:{ss:02d}"
    segments.append(f"**[{ts}]** {seg['text'].strip()}")

content = "# 第一題題目-愛鄉之聲電臺.wav — 逐字稿\n\n"
content += f"轉錄完成，共 {len(segments)} 段，總長 {result['segments'][-1]['end']/60:.1f} 分鐘\n\n---\n\n"
content += "\n\n".join(segments)

OUT_FILE.write_text(content, encoding="utf-8")
print(f"\n✓ 完成！輸出：{OUT_FILE}")
print("下一步：git add skills/ && git push")
