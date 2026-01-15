import subprocess
import os

class VideoEditorService:
    def stitch_clips(self, input_path: str, timestamps: list, output_name: str):
        """
        Cuts segments from input and stitches them into one video.
        timestamps: [{'start': 10, 'end': 20}, ...]
        """
        temp_files = []
        os.makedirs("data/temp", exist_ok=True)

        for i, ts in enumerate(timestamps):
            temp_output = f"data/temp/clip_{i}.mp4"
            # FFmpeg command to cut without re-encoding (very fast)
            cmd = [
                'ffmpeg', '-y', '-ss', str(ts['start']), '-to', str(ts['end']),
                '-i', input_path, '-c', 'copy', temp_output
            ]
            subprocess.run(cmd, check=True)
            temp_files.append(temp_output)

        # Create a list file for FFmpeg concat
        list_path = "data/temp/concat_list.txt"
        with open(list_path, "w") as f:
            for file in temp_files:
                f.write(f"file '{os.path.abspath(file)}'\n")

        final_output = f"data/outputs/{output_name}"
        os.makedirs("data/outputs", exist_ok=True)
        
        # Concat the clips
        concat_cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', 
            '-i', list_path, '-c', 'copy', final_output
        ]
        subprocess.run(concat_cmd, check=True)
        return final_output