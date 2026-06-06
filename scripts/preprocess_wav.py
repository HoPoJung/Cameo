"""
WAV 前處理：Whisper 語音轉文字，存成 references/wav/
用法：python scripts/preprocess_wav.py data/wav/
需要：pip install openai-whisper
"""
import sys
from pathlib import Path

try:
    import whisper
except ImportError:
    print("請先執行：pip install openai-whisper")
    sys.exit(1)


def process_wav(wav_path: Path, out_dir: Path, model_name: str = "medium"):
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (wav_path.stem + ".md")

    print(f"正在轉錄 {wav_path.name}（模型：{model_name}）...")
    model = whisper.load_model(model_name)
    result = model.transcribe(str(wav_path), language="zh", verbose=False)

    segments = []
    for seg in result["segments"]:
        t = seg["start"]
        mm, ss = divmod(int(t), 60)
        hh, mm = divmod(mm, 60)
        timestamp = f"{hh:02d}:{mm:02d}:{ss:02d}"
        segments.append(f"**[{timestamp}]** {seg['text'].strip()}")

    content = f"# {wav_path.name} — 逐字稿\n\n" + "\n\n".join(segments)
    out_file.write_text(content, encoding="utf-8")
    print(f"✓ {wav_path.name} → {out_file}")
    return out_file


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/wav")
    model_name = sys.argv[2] if len(sys.argv) > 2 else "medium"
    out = Path("skills/cameo-interview/references/wav")

    wavs = list(src.glob("*.wav")) + list(src.glob("*.mp3")) + list(src.glob("*.m4a"))
    if not wavs:
        print(f"找不到音訊檔案：{src}")
        sys.exit(1)

    for w in wavs:
        process_wav(w, out, model_name)

    print(f"\n完成。輸出位置：{out}/")


if __name__ == "__main__":
    main()
