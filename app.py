import os, random, subprocess, uuid, time, glob, zipfile, io
from flask import Flask, request, jsonify, send_file, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

UPLOAD_DIR = '/tmp/uploads'
OUTPUT_DIR = '/tmp/outputs'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMPLATES = [
    {'id': 'only_few', 'cut': 2.367, 'green': os.path.join(BASE_DIR, 'assets', 'green_only_few.mp4'), 'audio': os.path.join(BASE_DIR, 'assets', 'aud_only_few.mp4')},
    {'id': 'something', 'cut': 3.967, 'green': os.path.join(BASE_DIR, 'assets', 'green_something.mp4'), 'audio': os.path.join(BASE_DIR, 'assets', 'aud_something.mp4')},
    {'id': 'first_move', 'cut': 4.333, 'green': os.path.join(BASE_DIR, 'assets', 'green_first_move.mp4'), 'audio': os.path.join(BASE_DIR, 'assets', 'aud_first_move.mp4')},
    {'id': 'guess', 'cut': 4.000, 'green': os.path.join(BASE_DIR, 'assets', 'green_guess.mp4'), 'audio': os.path.join(BASE_DIR, 'assets', 'aud_guess.mp4')},
]

CAPTIONS = [
    "POV: Before everything was going so well...",
    "This might be a bad idea...",
    "This is your sign to look closer",
    "Only a few people noticed this...",
    "POV: the date was going perfectly...",
    "POV: she said she was a good girl...",
    "POV: you trusted her with your hoodie...",
    "POV: she said I never do this...",
    "POV: he said it was just a friend...",
    "POV: the night started so innocent...",
    "POV: she texted come over I am bored...",
    "POV: you left her alone for 5 minutes...",
    "POV: everything was fine until midnight...",
    "POV: she said lets just watch a movie...",
    "POV: you believed her when she said goodnight...",
    "POV: the party was supposed to be chill...",
    "POV: she promised it was her last drink...",
    "POV: he said I will be home early...",
    "POV: she said we are just talking...",
    "POV: it started as a normal Tuesday...",
    "POV: she looked innocent at first...",
    "POV: you thought the FaceTime was normal...",
    "POV: she said dont worry about him...",
    "POV: the sleepover was just for girls...",
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    try:
        ffmpeg_ok = subprocess.run(['ffmpeg', '-version'], capture_output=True).returncode == 0
    except:
        ffmpeg_ok = False
    assets_dir = os.path.join(BASE_DIR, 'assets')
    assets_exist = os.path.exists(assets_dir)
    assets_list = os.listdir(assets_dir) if assets_exist else []
    return jsonify({'ffmpeg': ffmpeg_ok, 'assets': assets_list, 'base': BASE_DIR})

@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({'error': 'Pas de video'}), 400
    file = request.files['video']
    if not file.filename:
        return jsonify({'error': 'Fichier vide'}), 400

    tmpl = random.choice(TEMPLATES)
    caption = random.choice(CAPTIONS)
    uid = str(uuid.uuid4())[:8]

    input_path = os.path.join(UPLOAD_DIR, f'{uid}_in.mp4')
    girl_path = os.path.join(UPLOAD_DIR, f'{uid}_girl.mp4')
    green_path = os.path.join(UPLOAD_DIR, f'{uid}_green.mp4')
    concat_path = os.path.join(UPLOAD_DIR, f'{uid}.txt')
    video_path = os.path.join(UPLOAD_DIR, f'{uid}_vid.mp4')
    output_path = os.path.join(OUTPUT_DIR, f'reel_{tmpl["id"]}_{uid}.mp4')

    file.save(input_path)

    try:
        cut = str(tmpl['cut'])

        if not os.path.exists(tmpl['green']):
            return jsonify({'error': 'Green clip missing'}), 500

        # Step 1: Girl clip WITH caption text burned in
        safe_caption = caption.replace("'", "'\\''").replace('"', '\\"').replace(':', '\\:')
        drawtext = (
            f"drawtext=text='{safe_caption}'"
            f":fontsize=36:fontcolor=white:borderw=3:bordercolor=black"
            f":x=(w-text_w)/2:y=h*0.48"
            f":font=Sans"
        )

        r1 = subprocess.run([
            'ffmpeg', '-y', '-i', input_path, '-t', cut,
            '-vf', f'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,{drawtext}',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-r', '30', '-pix_fmt', 'yuv420p',
            '-an', girl_path
        ], capture_output=True, text=True, timeout=120)

        if not os.path.exists(girl_path):
            return jsonify({'error': 'Girl clip failed: ' + r1.stderr[-300:]}), 500

        # Step 2: Re-encode green to match
        r2 = subprocess.run([
            'ffmpeg', '-y', '-i', tmpl['green'],
            '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '23', '-r', '30', '-pix_fmt', 'yuv420p',
            '-an', green_path
        ], capture_output=True, text=True, timeout=120)

        if not os.path.exists(green_path):
            return jsonify({'error': 'Green failed'}), 500

        # Step 3: Concat
        with open(concat_path, 'w') as f:
            f.write(f"file '{girl_path}'\nfile '{green_path}'\n")

        r3 = subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_path,
            '-c', 'copy', video_path
        ], capture_output=True, text=True, timeout=120)

        if not os.path.exists(video_path):
            return jsonify({'error': 'Concat failed'}), 500

        # Step 4: Add audio
        r4 = subprocess.run([
            'ffmpeg', '-y', '-i', video_path, '-i', tmpl['audio'],
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-map', '0:v:0', '-map', '1:a:0',
            '-shortest', '-movflags', '+faststart',
            output_path
        ], capture_output=True, text=True, timeout=120)

        if not os.path.exists(output_path):
            return jsonify({'error': 'Audio failed'}), 500

        for f in [input_path, girl_path, green_path, concat_path, video_path]:
            try: os.remove(f)
            except: pass

        filename = f'reel_{tmpl["id"]}_{uid}.mp4'
        return jsonify({
            'ok': True,
            'file': filename,
            'template': tmpl['id'],
            'caption': caption,
            'download': f'/download/{filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Not found'}), 404
    return send_file(path, as_attachment=True, download_name=filename)

@app.route('/download-all')
def download_all():
    files = glob.glob(os.path.join(OUTPUT_DIR, 'reel_*.mp4'))
    if not files:
        return jsonify({'error': 'Aucun reel'}), 404
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, os.path.basename(f))
    zip_buf.seek(0)
    return send_file(zip_buf, as_attachment=True, download_name=f'reels_batch_{int(time.time())}.zip', mimetype='application/zip')

@app.before_request
def cleanup_old():
    for d in [UPLOAD_DIR, OUTPUT_DIR]:
        for f in glob.glob(os.path.join(d, '*')):
            if time.time() - os.path.getmtime(f) > 3600:
                try: os.remove(f)
                except: pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
