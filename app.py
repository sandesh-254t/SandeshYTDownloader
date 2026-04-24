from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
import yt_dlp
import re
import os
import requests

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
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            
            video_id = None
            if 'youtu.be' in url:
                video_id = url.split('youtu.be/')[1].split('?')[0]
            elif 'watch?v=' in url:
                video_id = url.split('watch?v=')[1].split('&')[0]
            elif 'shorts/' in url:
                video_id = url.split('shorts/')[1].split('?')[0]
            
            return jsonify({
                'success': True,
                'title': title,
                'video_id': video_id
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-video', methods=['POST'])
def download_video():
    try:
        data = request.get_json()
        url = data.get('url')
        title = data.get('title', 'video')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Clean title - remove special characters and encode properly
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title)
        clean_title = clean_title.encode('ascii', 'ignore').decode('ascii')
        clean_title = clean_title.strip()[:50]
        
        if not clean_title:
            clean_title = "video"
        
        branded_filename = f"{BRAND_NAME} - {clean_title}.mp4"
        # Remove any problematic characters from filename
        branded_filename = re.sub(r'[^\x00-\x7F]+', '', branded_filename)
        
        def stream_video():
            """Stream video directly from YouTube - NO disk storage, minimal RAM"""
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'best[ext=mp4]',
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Get the direct URL without downloading
                info = ydl.extract_info(url, download=False)
                video_url = info['url']
                
                # Stream from YouTube directly
                response = requests.get(video_url, stream=True)
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
        
        return Response(
            stream_video(),
            mimetype='video/mp4',
            headers={
                'Content-Disposition': f'attachment; filename="{branded_filename}"'
            }
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))