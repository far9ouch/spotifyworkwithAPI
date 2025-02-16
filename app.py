from flask import Flask, request, jsonify, send_file, render_template, url_for
import yt_dlp
import io
import tempfile
import os
import logging
import re
import json
import urllib.parse
import requests
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import time

app = Flask(__name__)
app.static_folder = 'static'
logging.basicConfig(level=logging.DEBUG)

# Update FFmpeg path to work in both local and production
FFMPEG_PATH = "ffmpeg" if os.getenv("RENDER") else r"C:\ffmpeg\bin\ffmpeg.exe"

def clean_filename(title):
    # Remove invalid characters and clean up the title
    # Replace invalid characters with spaces
    clean_title = re.sub(r'[\\/*?:"<>|]', '', title)
    # Remove extra spaces
    clean_title = ' '.join(clean_title.split())
    # Limit filename length
    if len(clean_title) > 50:
        clean_title = clean_title[:47] + "..."
    return clean_title

def extract_title_from_info(info):
    # Get the title from the video info
    title = info.get('title', '')
    
    # Remove common suffixes from YouTube titles
    title = re.sub(r'\(Official Video\)|\(Official Music Video\)|\(Lyrics\)|\[.*?\]|\(.*?\)', '', title)
    
    # If title contains a hyphen, assume it's in "Artist - Track" format
    if ' - ' in title:
        parts = title.split(' - ', 1)
        artist = parts[0].strip()
        track = parts[1].strip()
        return f"{artist} - {track}"
    
    # Try to get artist and track from metadata
    artist = info.get('artist', info.get('creator', info.get('uploader', '')))
    track = info.get('track', title)
    
    if artist and track:
        return f"{artist} - {track}"
    
    return title.strip()

def is_spotify_url(url):
    return 'spotify.com' in url.lower()

def is_youtube_url(url):
    return 'youtube.com' in url.lower() or 'youtu.be' in url.lower()

def get_spotify_track_info(url):
    # Extract track ID from Spotify URL
    try:
        if '/track/' in url:
            track_id = url.split('/track/')[1].split('?')[0]
        else:
            return None
        
        # Use Spotify's OEmbed API (public API, no auth needed)
        oembed_url = f"https://open.spotify.com/oembed?url=https://open.spotify.com/track/{track_id}"
        response = requests.get(oembed_url)
        
        if response.ok:
            data = response.json()
            # The title from OEmbed includes both artist and track name
            title = data.get('title', '')
            author = data.get('author_name', '')
            
            if title and author:
                # Remove "by Author" from title if present
                title = title.replace(f" by {author}", "")
                return f"{author} - {title}"
            elif title:
                return title
            
    except Exception as e:
        print(f"Error getting Spotify info: {e}")
        print(f"URL: {url}")
        print(f"Response: {response.text if 'response' in locals() else 'No response'}")
    
    return None

def search_youtube(query):
    # Create safe search query
    # Remove special characters and extra spaces
    clean_query = re.sub(r'[^\w\s-]', ' ', query)
    clean_query = ' '.join(clean_query.split())
    search_query = urllib.parse.quote(f"{clean_query} official audio")
    return f"https://www.youtube.com/results?search_query={search_query}"

@app.route('/')
def index():
    return render_template('index.html')

def get_youtube_video(url):
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(2)  # Wait for page to load
        # Get video title
        title = driver.find_element(By.CSS_SELECTOR, 'h1.title').text
        return {'title': title, 'url': url}
    finally:
        driver.quit()

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_path = temp_file.name

        # Configure yt-dlp with additional options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': temp_path[:-4],
            'ffmpeg_location': FFMPEG_PATH,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'add_metadata': True,
            'embed_metadata': True,
            'parse_metadata': True,
            'cookiefile': 'cookies.txt',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Sec-Fetch-Mode': 'navigate',
                'Referer': 'https://www.youtube.com/'
            },
            'socket_timeout': 30,  # Added timeout
            'retries': 3,  # Added retries
            'verbose': True  # Added verbose logging
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("Starting download...")
                try:
                    # Extract info first to get the title
                    info = ydl.extract_info(url, download=False)
                    
                    if not info:
                        raise Exception("Could not extract video information")
                    
                    # Get a better formatted filename
                    filename = extract_title_from_info(info)
                    
                    # Clean the filename
                    filename = clean_filename(filename)
                    print(f"Final filename: {filename}")

                    # Download with updated options
                    download_result = ydl.download([url])
                    
                    if download_result != 0:
                        raise Exception("Download failed")

                    print(f"Download complete, checking file: {temp_path}")

                    if not os.path.exists(temp_path):
                        raise Exception("File not created after download")

                    if os.path.getsize(temp_path) == 0:
                        raise Exception("Downloaded file is empty")

                    print(f"File exists, size: {os.path.getsize(temp_path)}")
                    
                    # Send file with cleaned filename
                    return send_file(
                        temp_path,
                        mimetype='audio/mpeg',
                        as_attachment=True,
                        download_name=f"{filename}.mp3"
                    )
                except Exception as e:
                    print(f"Download error: {str(e)}")
                    raise Exception(f"Download failed: {str(e)}")
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    print(f"Cleaned up temp file: {temp_path}")
                except Exception as e:
                    print(f"Failed to clean up temp file: {e}")

    except Exception as e:
        error_message = str(e)
        print(f"Error: {error_message}")
        if "Sign in to confirm" in error_message:
            return jsonify({'error': 'Video requires authentication. Please try a different video.'}), 403
        elif "not available" in error_message.lower():
            return jsonify({'error': 'Video is not available. Please try a different video.'}), 404
        else:
            return jsonify({'error': f'Conversion failed: {error_message}'}), 500

@app.route('/get_youtube_link', methods=['POST'])
def get_youtube_link():
    try:
        data = request.get_json()
        spotify_url = data.get('url')

        if not spotify_url or not is_spotify_url(spotify_url):
            return jsonify({'error': 'Invalid Spotify URL'}), 400

        # Get track info from Spotify
        track_info = get_spotify_track_info(spotify_url)
        if not track_info:
            return jsonify({'error': 'Could not get track information. Please make sure it\'s a valid Spotify track URL'}), 400

        # Generate YouTube search URL
        youtube_search_url = search_youtube(track_info)

        return jsonify({
            'youtube_search': youtube_search_url,
            'track_info': track_info
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_youtube_url', methods=['POST'])
def get_youtube_url():
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'No search query provided'}), 400

        # Configure yt-dlp to search YouTube
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'default_search': 'ytsearch1:'  # Only get the first result
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in result and result['entries']:
                video = result['entries'][0]
                return jsonify({
                    'url': f"https://www.youtube.com/watch?v={video['id']}",
                    'title': video.get('title', '')
                })

        return jsonify({'error': 'No results found'}), 404

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_youtube_cookies():
    # You can get these cookies by logging into YouTube and extracting them
    return {
        'CONSENT': 'YES+',
        'VISITOR_INFO1_LIVE': 'your_visitor_info',
        'LOGIN_INFO': 'your_login_info',
        'SID': 'your_sid',
        'HSID': 'your_hsid',
        'SSID': 'your_ssid',
        'APISID': 'your_apisid',
        'SAPISID': 'your_sapisid',
        '__Secure-1PSID': 'your_1psid',
        '__Secure-3PSID': 'your_3psid',
    }

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port) 