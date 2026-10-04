import os, random, subprocess, uuid, time, glob
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max

UPLOAD_DIR = '/tmp/uploads'
OUTPUT_DIR = '/tmp/outputs'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

TEMPLATES = [
    {'id': 'only_few', 'cut': 2.367, 'green': 'assets/green_only_few.mp4', 'audio': 'assets/aud_only_few.mp4'},
    {'id': 'something', 'cut': 3.967, 'green': 'assets/green_something.mp4', 'audio': 'assets/aud_something.mp4'},
    {'id': 'first_move', 'cut': 4.333, 'green': 'assets/green_first_move.mp4', 'audio': 'assets/aud_first_move.mp4'},
    {'id': 'guess', 'cut': 4.000, 'green': 'assets/green_guess.mp4', 'audio': 'assets/aud_guess.mp4'},
]

CAPTIONS = [
    "POV: Before everything was going so well...",
    "This might be a bad idea...",
    "This is your sign to look closer",
    "Only a few people noticed this...",
    "POV: the date was going perfectly...",
    "POV: she said she was a good girl...",
    "POV: you trusted her with your hoodie...",
    'POV: she said "I never do this"...',
    "POV: he said it was just a friend...",
    "POV: the night started so innocent...",
    'POV: she texted "come over, I\'m bored"...',
    "POV: you left her alone for 5 minutes...",
    "POV: everything was fine until midnight...",
    'POV: she said "let\'s just watch a movie"...',
    "POV: you believed her when she said goodnight...",
    "POV: the party was supposed to be chill...",
    "POV: she promised it was her last drink...",
    'POV: he said "I\'ll be home early"...',
    'POV: she said "we\'re just talking"...',
    "POV: it started as a normal Tuesday...",
    "POV: she looked innocent at first...",
    "POV: you thought the FaceTime was normal...",
    'POV: she said "don\'t worry about him"...',
    "POV: the sleepover was just for girls...",
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return jsonify({'error': 'Pas de vidéo'}), 400
    
    file = request.files['video']
    if not file.filename:
        return jsonify({'error': 'Fichier vide'}), 400
    
    # Pick random template + caption
    tmpl = random.choice(TEMPLATES)
    caption = random.choice(CAPTIONS)
    
    uid = str(uuid.uuid4())[:8]
    input_path = os.path.join(UPLOAD_DIR, f'{uid}_input.mp4')
    girl_path = os.path.join(UPLOAD_DIR, f'{uid}_girl.mp4')
    concat_path = os.path.join(UPLOAD_DIR, f'{uid}_concat.txt')
    video_path = os.path.join(UPLOAD_DIR, f'{uid}_video.mp4')
    output_path = os.path.join(OUTPUT_DIR, f'reel_{tmpl["id"]}_{uid}.mp4')
    
    file.save(input_path)
    
    try:
        cut = str(tmpl['cut'])
        green = tmpl['green']
        audio = tmpl['audio']
        
        # Step 1: Girl clip (first N seconds, scaled to 720x1280)
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path, '-t', cut,
            '-vf', 'scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-r', '30', '-pix_fmt', 'yuv420p',
            '-an', girl_path
        ], capture_output=True, timeout=60)
        
        # Step 2: Concat girl + green
        with open(concat_path, 'w') as f:
            f.write(f"file '{girl_path}'\nfile '{os.path.abspath(green)}'\n")
        
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_path,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
            video_path
        ], capture_output=True, timeout=60)
        
        # Step 3: Add audio
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path, '-i', os.path.abspath(audio),
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-map', '0:v:0', '-map', '1:a:0',
            '-shortest', '-movflags', '+faststart',
            output_path
        ], capture_output=True, timeout=60)
        
        if not os.path.exists(output_path):
            return jsonify({'error': 'FFmpeg a échoué'}), 500
        
        # Cleanup temp files
        for f in [input_path, girl_path, concat_path, video_path]:
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
        return jsonify({'error': 'Fichier non trouvé'}), 404
    return send_file(path, as_attachment=True, download_name=filename)

# Cleanup old files periodically
@app.before_request
def cleanup():
    for d in [UPLOAD_DIR, OUTPUT_DIR]:
        for f in glob.glob(os.path.join(d, '*')):
            if time.time() - os.path.getmtime(f) > 3600:
                try: os.remove(f)
                except: pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
