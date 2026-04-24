from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import yt_dlp
import re
import uuid
import os

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
            'format': 'best[ext=mp4]',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            
            # Get video ID for embed
            video_id = None
            if 'youtu.be' in url:
                video_id = url.split('youtu.be/')[1].split('?')[0]
            elif 'watch?v=' in url:
                video_id = url.split('watch?v=')[1].split('&')[0]
            
            return jsonify({
                'success': True,
                'title': title,
                'video_id': video_id
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-video', methods=['POST'])
def download_video():
    output_path = None
    try:
        data = request.get_json()
        url = data.get('url')
        title = data.get('title', 'video')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Create unique filename
        filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join("downloads", filename)
        os.makedirs("downloads", exist_ok=True)
        
        ydl_opts = {
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Clean title for filename
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        
        # Add your BRAND NAME to the filename
        branded_filename = f"{BRAND_NAME} - {clean_title}.mp4"
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=branded_filename,
            mimetype='video/mp4'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass

if __name__ == '__main__':
    os.makedirs("downloads", exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))