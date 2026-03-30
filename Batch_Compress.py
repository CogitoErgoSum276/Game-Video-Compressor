import subprocess
import sys
import os
from pathlib import Path

# --- 核心修改：动态获取 ffmpeg 路径 ---
def get_ffmpeg_path():
    """获取 ffmpeg 的绝对路径。兼容直接运行和 PyInstaller 打包后的运行环境。"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # 如果是打包后的 exe，去临时目录找 ffmpeg.exe
        return os.path.join(sys._MEIPASS, 'ffmpeg.exe')
    else:
        # 如果是直接跑 .py 脚本，默认在当前目录或系统环境变量里找
        return 'ffmpeg.exe'

FFMPEG_PATH = get_ffmpeg_path()

# --- 配置区 ---
CRF = "26"
PRESET = "slow"
VIDEO_EXTS = {'.mp4', '.mkv', '.flv', '.mov', '.ts'}

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
        process = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, 
                                   universal_newlines=True, encoding='utf-8', errors='ignore')
        
        for line in process.stdout:
            if "frame=" in line:
                print(f"\r{line.strip()}", end="")
        
        process.wait()
        if process.returncode == 0:
            print(f"\n\n[完成] 成功保存至: {output_file.name}")
        else:
            print(f"\n\n[失败] FFmpeg 报错，请检查文件。")
            
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