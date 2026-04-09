import subprocess
import json
import os

def get_video(path):
    cmd = [
        "ffprobe", 
        "-v", "quiet",
       "-show_format", 
        ##"format=duration", 
        "-show_streams", 
        "-print_format", "json", 
        path
    ]
    out = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(out.stdout)

