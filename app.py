from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import yt_dlp
import re
import os
import uuid
import base64
import tempfile

app = Flask(__name__)
CORS(app)

BRAND_NAME = "SandeshYTDownloader"


# ✅ Cookie loader (secure)
def get_cookie_file():
    cookies_b64 = os.environ.get("YOUTUBE_COOKIES")
    if cookies_b64:
        cookies_content = base64.b64decode(cookies_b64).decode("utf-8")

        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp.write(cookies_content.encode())
        temp.close()

        return temp.name
    return None


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/get-video", methods=["POST"])
def get_video():
    cookie_file = None
    try:
        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "No URL provided"}), 400

        ydl_opts = {"quiet": True, "no_warnings": True}

        cookie_file = get_cookie_file()
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "Video")

        video_id = None
        if "youtu.be" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        elif "watch?v=" in url:
            video_id = url.split("watch?v=")[1].split("&")[0]

        return jsonify({
            "success": True,
            "title": title,
            "video_id": video_id
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cookie_file and os.path.exists(cookie_file):
            os.unlink(cookie_file)


@app.route("/api/download-video", methods=["POST"])
def download_video():
    cookie_file = None
    output_path = None

    try:
        data = request.get_json()
        url = data.get("url")
        title = data.get("title", "video")

        filename = f"{uuid.uuid4()}.mp4"
        os.makedirs("downloads", exist_ok=True)
        output_path = os.path.join("downloads", filename)

        clean_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        branded_filename = f"{BRAND_NAME} - {clean_title}.mp4"

        ydl_opts = {
            "outtmpl": output_path,
            "format": "best[ext=mp4]",
            "quiet": True,
        }

        cookie_file = get_cookie_file()
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(
            output_path,
            as_attachment=True,
            download_name=branded_filename
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cookie_file and os.path.exists(cookie_file):
            os.unlink(cookie_file)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)


if __name__ == "__main__":
    app.run()
