from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import yt_dlp
import json
import re

app = Flask(__name__)
CORS(app)

BRAND_NAME = "SandeshYTDownloader"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/get-video', methods=['POST'])
def get_video():
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        if not re.search(r'(youtube\.com|youtu\.be)', url):
            return jsonify({'error': 'Please enter a valid YouTube URL'}), 400
        
        # Options to extract video info without downloading
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'format': 'best[ext=mp4]',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get best video URL
            video_url = None
            formats = info.get('formats', [])
            
            # Find the best MP4 format
            for f in formats:
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                    if video_url is None or f.get('height', 0) > 600:
                        video_url = f.get('url')
            
            if not video_url:
                # Fallback - just get any direct URL
                video_url = info.get('url')
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'Video'),
                'video_url': video_url,
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0)
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    app.run(debug=True)