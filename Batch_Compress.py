import subprocess
import sys
import os
import re
import time
from datetime import timedelta
from pathlib import Path


# --- 获取 ffmpeg 路径 ---
def get_ffmpeg_path():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'ffmpeg.exe')
    return 'ffmpeg.exe'


FFMPEG_PATH = get_ffmpeg_path()
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

    print(f"\n{'─' * 60}")
    print(f"🎬 处理中: {input_file.name}")

    cmd = [
        FFMPEG_PATH, "-i", str(input_file),
        "-map", "0:v", "-map", "0:a",
        "-c:v", "libx265", "-preset", "slow", "-crf", "26", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-y", str(output_file)
    ]

    start_wall_time = time.time()  # 记录开始压制的实际时间

    try:
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                                   universal_newlines=True, encoding='utf-8', errors='ignore')

        duration_regex = re.compile(r"Duration:\s*(\d{2}:\d{2}:\d{2})")
        time_regex = re.compile(r"time=(\d{2}:\d{2}:\d{2})")

        total_duration_str = "00:00:00"
        total_seconds = 0

        for line in process.stderr:
            # 1. 抓取总时长
            if total_seconds == 0:
                match = duration_regex.search(line)
                if match:
                    total_duration_str = match.group(1)
                    total_seconds = time_to_seconds(total_duration_str)

            # 2. 抓取当前进度并刷新 UI
            if "time=" in line and total_seconds > 0:
                match = time_regex.search(line)
                if match:
                    current_time_str = match.group(1)
                    current_seconds = time_to_seconds(current_time_str)

                    # 计算百分比
                    percent = (current_seconds / total_seconds) * 100
                    percent = min(100.0, percent)

                    # 计算已经跑了多久（实际耗时）
                    elapsed_seconds = int(time.time() - start_wall_time)
                    elapsed_str = str(timedelta(seconds=elapsed_seconds))

                    # 绘制 20 格进度条
                    bar = '█' * int(percent // 5) + '-' * (20 - int(percent // 5))

                    # 拼接极简输出：进度条 | 百分比 | 视频总长 | 已经耗时
                    # 使用 \r 覆盖上一行，末尾加空格清除残影
                    output = f"\r进度: [{bar}] {percent:>5.1f}% | 视频时长: {total_duration_str} | 已用时: {elapsed_str} "
                    sys.stdout.write(output)
                    sys.stdout.flush()

        process.wait()
        if process.returncode == 0:
            print(f"\n✅ 压制完成！")
        else:
            print(f"\n❌ 压制出错，请检查原文件。")

    except Exception as e:
        print(f"\n⚠️ 异常: {e}")


if __name__ == "__main__":
    dropped_paths = sys.argv[1:]
    if not dropped_paths:
        print("请将视频或文件夹拖到此处。")
        input("\n回车退出...")
        sys.exit()

    target_files = []
    for p_str in dropped_paths:
        p = Path(p_str)
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS:
            target_files.append(p)
        elif p.is_dir():
            for ext in VIDEO_EXTS:
                target_files.extend(list(p.rglob(f"*{ext}")))

    if target_files:
        print(f"找到 {len(target_files)} 个任务，开始排队压制...")
        for file_path in target_files:
            compress_video(file_path)

    print("\n" + "─" * 60)
    print("所有任务已处理完毕。")
    input("按回车键退出...")
