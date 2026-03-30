import subprocess
import sys
import os
import re
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

# --- 时间转换辅助函数 ---
def time_to_seconds(time_str):
    """将 HH:MM:SS.xx 格式转换为秒数"""
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)

def compress_video(input_path):
    input_file = Path(input_path)
    
    if "_x265" in input_file.stem:
        print(f"\n[跳过] 文件已是压缩版: {input_file.name}")
        return

    output_file = input_file.parent / f"{input_file.stem}_x265.mp4"
    
    print(f"\n{'='*60}")
    print(f"[正在处理] {input_file.name}")
    print(f" -> 输出至: {output_file.name}")
    print(f"{'='*60}")
    
    cmd = [
        FFMPEG_PATH, "-i", str(input_file),
        "-map", "0:v", "-map", "0:a",
        "-c:v", "libx265", "-preset", PRESET, "-crf", CRF, "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-y", str(output_file)
    ]
    
    try:
        # 启动 FFmpeg 并捕获标准错误输出 (FFmpeg 的日志全在 stderr 里)
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, 
                                   universal_newlines=True, encoding='utf-8', errors='ignore')
        
        # 用于匹配时长和当前进度的正则表达式
        duration_regex = re.compile(r"Duration:\s*(\d{2}:\d{2}:\d{2}\.?\d*)")
        time_regex = re.compile(r"time=\s*(\d{2}:\d{2}:\d{2}\.?\d*)")
        
        total_duration = 0
        
        # 实时逐行读取 FFmpeg 的输出
        for line in process.stderr:
            # 1. 抓取视频总时长 (只抓取一次)
            if total_duration == 0:
                match = duration_regex.search(line)
                if match:
                    total_duration = time_to_seconds(match.group(1))
            
            # 2. 抓取当前处理进度并绘制进度条
            if "time=" in line and total_duration > 0:
                match = time_regex.search(line)
                if match:
                    current_time = time_to_seconds(match.group(1))
                    progress = (current_time / total_duration) * 100
                    progress = min(100.0, progress) # 防止计算误差超过100%
                    
                    # 绘制进度条UI (总长40个字符)
                    bar_length = 40
                    filled_length = int(bar_length * progress // 100)
                    bar = '█' * filled_length + '-' * (bar_length - filled_length)
                    
                    # \r 保证在同一行刷新，不会刷屏
                    print(f"\r压制进度: [{bar}] {progress:.1f}% ", end="")
        
        process.wait()
        if process.returncode == 0:
            # 强制进度条显示 100% 
            bar = '█' * 40
            print(f"\r压制进度: [{bar}] 100.0% ", end="")
            print(f"\n\n[完成] 成功保存至: {output_file.name}")
        else:
            print(f"\n\n[失败] FFmpeg 报错，请检查文件是否损坏。")
            
    except Exception as e:
        print(f"\n[异常] {e}")

if __name__ == "__main__":
    dropped_paths = sys.argv[1:]
    
    if not dropped_paths:
        print("使用说明：直接将【视频文件】或【整个文件夹】拖到此程序图标上即可。")
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

    if not target_files:
        print("未发现可处理的视频文件。")
    else:
        print(f"共发现 {len(target_files)} 个任务，开始压制...")
        for file_path in target_files:
            compress_video(file_path)
            
    print("\n" + "#"*60)
    print("所有任务处理完毕！")
    input("按回车键退出...")
