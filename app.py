from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import yt_dlp
import os
import re
import requests
from urllib.parse import quote

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
        
        # Updated yt-dlp options to bypass YouTube blocking
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                    'skip': ['hls', 'dash']
                }
            },
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Get the best video URL
            video_url = None
            formats = info.get('formats', [])
            
            # Find the best MP4 format
            for f in formats:
                if f.get('ext') == 'mp4' and f.get('vcodec') != 'none':
                    if video_url is None or f.get('height', 0) > 720:
                        video_url = f.get('url')
            
            # Fallback to any URL
            if not video_url:
                video_url = info.get('url')
            
            # Extract video ID for embed
            video_id = None
            if 'youtu.be' in url:
                video_id = url.split('youtu.be/')[1].split('?')[0]
            elif 'watch?v=' in url:
                video_id = url.split('watch?v=')[1].split('&')[0]
            
            return jsonify({
                'success': True,
                'title': info.get('title', 'Video'),
                'video_url': video_url,
                'thumbnail': info.get('thumbnail', ''),
                'video_id': video_id
            })
        
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/download-video', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        title = data.get('title', 'video')
        
        if not video_url:
            return jsonify({'error': 'No video URL provided'}), 400
        
        # Clean filename
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        title = title[:50]
        filename = f"{BRAND_NAME} - {title}.mp4"
        
        # Stream the video from YouTube and force download
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'https://www.youtube.com/'
        }
        
        response = requests.get(video_url, headers=headers, stream=True)
        
        # Force download by setting content-disposition header
        return send_file(
            response.raw,
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
