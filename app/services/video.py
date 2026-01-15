import subprocess

def create_short(input_path, output_path, start, end):
    # This command trims the video and crops it to 9:16 (Vertical)
    cmd = [
        'ffmpeg', '-i', input_path,
        '-ss', str(start), '-to', str(end),
        '-vf', "crop=ih*9/16:ih", # Crop to center vertical
        '-c:a', 'copy', output_path
    ]
    subprocess.run(cmd)