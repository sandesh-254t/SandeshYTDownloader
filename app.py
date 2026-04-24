from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import yt_dlp
import os
import re
import uuid

app = Flask(__name__)
CORS(app)

BRAND_NAME = "SandeshYTDownloader"

# Cookie file path - works on both local and Render
if os.path.exists('/etc/secrets/cookies.txt'):
    COOKIE_FILE = '/etc/secrets/cookies.txt'
else:
    COOKIE_FILE = os.path.join(os.path.dirname(__file__), 'cookies.txt')

def get_format_string(quality):
    selectors = {
        '144': 'bestvideo[height<=144]+bestaudio/best[height<=144]',
        '240': 'bestvideo[height<=240]+bestaudio/best[height<=240]',
        '360': 'bestvideo[height<=360]+bestaudio/best[height<=360]',
        '480': 'bestvideo[height<=480]+bestaudio/best[height<=480]',
        '720': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
        '1080': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '1440': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
        '2160': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
    }
    return selectors.get(quality, 'bestvideo[height<=720]+bestaudio/best[height<=720]')

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
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
            }
        }
        
        # Add cookies if available
        if os.path.exists(COOKIE_FILE):
            ydl_opts['cookiefile'] = COOKIE_FILE
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Video')
            
            # Extract video ID for embed
            video_id = None
            if 'youtu.be' in url:
                video_id = url.split('youtu.be/')[1].split('?')[0]
            elif 'watch?v=' in url:
                video_id = url.split('watch?v=')[1].split('&')[0]
            
            return jsonify({
                'success': True,
                'title': title,
                'video_id': video_id,
                'thumbnail': info.get('thumbnail', '')
            })
        
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/download-video', methods=['POST'])
def download_video():
    output_path = None
    try:
        data = request.get_json()
        url = data.get('url')
        title = data.get('title', 'video')
        quality = data.get('quality', '720')
        format_type = data.get('format_type', 'video')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        # Create unique filename
        filename = f"{uuid.uuid4()}.{'mp3' if format_type == 'audio' else 'mp4'}"
        output_path = os.path.join("downloads", filename)
        os.makedirs("downloads", exist_ok=True)
        
        # Base options
        ydl_opts = {
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'player_skip': ['webpage', 'configs'],
                }
            },
            'http_headers': {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            }
        }
        
        # Add cookies if available
        if os.path.exists(COOKIE_FILE):
            ydl_opts['cookiefile'] = COOKIE_FILE
        
        if format_type == 'audio':
            # For MP3 download
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            # For video download with selected quality
            format_string = get_format_string(quality)
            ydl_opts['format'] = format_string
            ydl_opts['merge_output_format'] = 'mp4'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the actual output file (yt-dlp might add extensions)
        final_output = output_path
        if format_type == 'audio':
            if os.path.exists(output_path + '.mp3'):
                final_output = output_path + '.mp3'
            elif os.path.exists(output_path.replace('.mp3', '') + '.mp3'):
                final_output = output_path.replace('.mp3', '') + '.mp3'
        
        # Clean filename for download
        clean_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        extension = 'mp3' if format_type == 'audio' else 'mp4'
        
        if format_type == 'video':
            branded_filename = f"{BRAND_NAME} - {clean_title} - {quality}p.{extension}"
        else:
            branded_filename = f"{BRAND_NAME} - {clean_title} (MP3).{extension}"
        
        return send_file(
            final_output,
            as_attachment=True,
            download_name=branded_filename,
            mimetype='audio/mpeg' if format_type == 'audio' else 'video/mp4'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # Clean up temp files
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass

if __name__ == '__main__':
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("templates", exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))