from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("downloads", exist_ok=True)
os.makedirs("clips", exist_ok=True)

@app.post("/api/process-video")
def process_video(data: dict):
    video_url = data.get("url")
    start_time = data.get("start", 0)
    duration = data.get("duration", 30)
    
    if not video_url:
        raise HTTPException(status_code=400, detail="URL wajib diisi")

    job_id = str(uuid.uuid4())[:8]
    raw_video = f"downloads/{job_id}.mp4"
    output_clip = f"clips/clip_{job_id}.mp4"

    try:
        dl_cmd = [
            "yt-dlp",
            "-f", "mp4[height<=720]",
            "-o", raw_video,
            video_url
        ]
        subprocess.run(dl_cmd, check=True)

        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", raw_video,
            "-t", str(duration),
            "-vf", "crop=ih*(9/16):ih",
            "-c:v", "libx264",
            "-c:a", "aac",
            output_clip
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        if os.path.exists(raw_video):
            os.remove(raw_video)

        return {
            "status": "success",
            "download_url": f"/api/download/{os.path.basename(output_clip)}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{filename}")
def download_file(filename: str):
    file_path = f"clips/{filename}"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="video/mp4", filename=filename)
    raise HTTPException(status_code=404, detail="File tidak ditemukan")
      
