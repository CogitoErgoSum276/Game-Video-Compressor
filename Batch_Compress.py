import subprocess
import sys
import os
import re
import shutil
from pathlib import Path


# --- 获取 ffmpeg 路径 ---
def get_ffmpeg_path():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'ffmpeg.exe')
    return 'ffmpeg.exe'


FFMPEG_PATH = get_ffmpeg_path()

# --- 配置区 ---
CRF = "26"
PRESET = "slow"
VIDEO_EXTS = {'.mp4', '.mkv', '.flv', '.mov', '.ts'}


def time_to_seconds(time_str):
    try:
        h, m, s = time_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return 0


def compress_video(input_path):
    input_file = Path(input_path)
    if "_x265" in input_file.stem:
        return

    output_file = input_file.parent / f"{input_file.stem}_x265.mp4"

    print(f"\n{'=' * 60}")
    print(f"[正在处理] {input_file.name}")
    print(f"{'=' * 60}")

    cmd = [
        FFMPEG_PATH, "-i", str(input_file),
        "-map", "0:v", "-map", "0:a",
        "-c:v", "libx265", "-preset", PRESET, "-crf", CRF, "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-y", str(output_file)
    ]

    try:
        # bufsize=1 和 universal_newlines=True 配合，确保实时读取
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                   universal_newlines=True, encoding='utf-8', errors='ignore', bufsize=1)

        duration_regex = re.compile(r"Duration:\s*(\d{2}:\d{2}:\d{2}\.?\d*)")
        time_regex = re.compile(r"time=\s*(\d{2}:\d{2}:\d{2}\.?\d*)")
        total_duration = 0

        for line in process.stderr:
            if total_duration == 0:
                match = duration_regex.search(line)
                if match:
                    total_duration = time_to_seconds(match.group(1))

            if "frame=" in line and "time=" in line:
                # 【重要】彻底清理掉 FFmpeg 行末可能存在的各种换行符
                raw_stats = line.replace('\r', '').replace('\n', '').strip()

                # 获取终端宽度并多留几个空格作为缓冲区，防止自动折行
                terminal_width = shutil.get_terminal_size().columns - 5

                if total_duration > 0:
                    match = time_regex.search(line)
                    if match:
                        current_time = time_to_seconds(match.group(1))
                        progress = (current_time / total_duration) * 100
                        progress = min(100.0, max(0.0, progress))

                        # 进度条占 12 格
                        bar_length = 12
                        filled = int(bar_length * progress // 100)
                        bar = '█' * filled + '-' * (bar_length - filled)

                        # 拼接信息
                        output_str = f"进度: [{bar}] {progress:4.1f}% | {raw_stats}"

                        # 截断并填充，确保每一行长度完全一致且不超标
                        final_line = output_str[:terminal_width].ljust(terminal_width)

                        # 使用 sys.stdout.write 配合 \r 是最稳妥的单行刷新方式
                        sys.stdout.write(f"\r{final_line}")
                        sys.stdout.flush()

        process.wait()
        if process.returncode == 0:
            print(f"\n\n[完成] 成功保存至: {output_file.name}")
        else:
            print(f"\n\n[失败] 请检查文件。")

    except Exception as e:
        print(f"\n[异常] {e}")


if __name__ == "__main__":
    dropped_paths = sys.argv[1:]
    if not dropped_paths:
        print("请拖入文件或文件夹。")
        input("\n按回车键退出...")
        sys.exit()

    target_files = []
    for path_str in dropped_paths:
        p = Path(path_str)
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            target_files.append(p)
        elif p.is_dir():
            for ext in VIDEO_EXTS:
                target_files.extend(list(p.rglob(f"*{ext}")))

    if target_files:
        print(f"发现 {len(target_files)} 个任务...")
        for file_path in target_files:
            compress_video(file_path)

    print("\n任务结束。")
    input("按回车键退出...")
