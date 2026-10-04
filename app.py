import os, random, subprocess, uuid, time, glob, zipfile, io
from flask import Flask, request, jsonify, send_file, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

UPLOAD_DIR = '/tmp/uploads'
OUTPUT_DIR = '/tmp/outputs'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ──────────────────────────────────────────
# MONTAGE VERT — templates portal effect
# ──────────────────────────────────────────
TEMPLATES = [
    {'id': 'only_few', 'cut': 2.367, 'green': os.path.join(BASE_DIR, 'assets', 'green_only_few.mp4'), 'audio': os.path.join(BASE_DIR, 'assets', 'aud_only_few.mp4')},
    {'id': 'something', 'cut': 3.967, 'green': os.path.join(BASE_DIR, 'assets', 'green_something.mp4'), 'audio': os.path.join(BASE_DIR, 'assets', 'aud_something.mp4')},
    {'id': 'first_move', 'cut': 4.333, 'green': os.path.join(BASE_DIR, 'assets', 'green_first_move.mp4'), 'audio': os.path.join(BASE_DIR, 'assets', 'aud_first_move.mp4')},
    {'id': 'guess', 'cut': 4.000, 'green': os.path.join(BASE_DIR, 'assets', 'green_guess.mp4'), 'audio': os.path.join(BASE_DIR, 'assets', 'aud_guess.mp4')},
]

MONTAGE_CAPTIONS = [
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
    "POV: she said we are just friends...",
    "POV: he said dont worry about him...",
    "POV: it was supposed to be a quiet night...",
    "POV: she said I deleted his number...",
    "POV: the uber was supposed to go home...",
    "POV: she said she was staying in tonight...",
]

# ──────────────────────────────────────────
# CAPTION MODE — captions engagement
# ──────────────────────────────────────────
CAPTION_TEXTS = [
    "My two cousins wanted to play a game with me... it hurt",
    "I goon to audios of men whimpering but no one's ever gonna know cuz I barely have any followers and I'm not using any hashtags",
    "I want to kiss me but replace the k with f and a with t",
    "when I was 14, a boy in my class typed 55378008 on calculator, turned it upside down and said, that's you.",
    "be a good boy and read this\nbackwards:\n\nelihc dna emina hctaw ew elihw\nstyttit gib esehc kcus ot nam a rof\ngnikool mi",
    "Biology\nBut without\n\"b, o, g\"",
    "I might be an 18yo blond but I'm not stupid. I know you have a card hock rn.\n\nNow change c with h",
    "What I really need:\n\nBlack (without Bla)\nDirt (without rt)\nFour (without Fo)\nYOLO (without LO)",
    "Missionary cause I'm pretty,\nbashots cause my 🍰 fat\n\nNow change R with S",
    "If it doesn't slip out when he leans\ndown to kiss me so he can talk to me\nhowever he wants idc\n(Read every 4th word)",
    "Amazing cook,\nlegs for days,\ntheep droat Queen\n\nNow read every third word",
    "acc so small that if you like or interact w any of my reels I WILL definitely send you something in dms",
    "I'm so single I literally text everyone who follows me.. I get excited thinking we might be friends. Send me this post and I'll",
    "Is 2008 too young?",
    "this mommy stuff ain't no joke. i genuinely want to call him good boy, buy him hot wheels and ill be the race track",
    "Is 2007 too young?",
    "If you have crush on me, pls go for it, you literally have no competition at all",
    "What I really need:\nVehicle (without hicle)\nLobby (without bby)\nUrban (without ban)\nYoga (without ga)\n\nNow read it backwards",
    "I look\nlike 18\nbecause\nolder man\nDon't take\nme\nSerious\n\nNow read:\n4,5,6,7,3,2,1",
    "You can only pick two:\n\niPhone 18 Pro\n$500\nMe ?\nInfinite beer",
    "when i tell older guy my\nage and he says you just a\nbabyyy instead of blocking\nme",
    "let's make a deal, you give\nme a like and say good\nmorning and i'll message\nyou if i like you",
]


# ──────────────────────────────────────────
# ROUTES
# ──────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html',
                           montage_captions=MONTAGE_CAPTIONS,
                           caption_texts=CAPTION_TEXTS)


# ── MONTAGE VERT ──

@app.route('/process', methods=['POST'])
def process_montage():
    if 'video' not in request.files:
        return jsonify({'error': 'Pas de vidéo'}), 400

    video = request.files['video']
    uid = str(uuid.uuid4())[:8]
    tmpl = random.choice(TEMPLATES)
    caption = random.choice(MONTAGE_CAPTIONS)

    input_path = os.path.join(UPLOAD_DIR, f'{uid}_in.mp4')
    girl_path = os.path.join(UPLOAD_DIR, f'{uid}_girl.mp4')
    concat_path = os.path.join(UPLOAD_DIR, f'{uid}_concat.txt')
    video_path = os.path.join(UPLOAD_DIR, f'{uid}_video.mp4')
    output_path = os.path.join(OUTPUT_DIR, f'reel_{tmpl["id"]}_{uid}.mp4')

    video.save(input_path)

    try:
        green = os.path.abspath(tmpl['green'])
        audio = os.path.abspath(tmpl['audio'])

        if not os.path.exists(green):
            return jsonify({'error': f'Asset manquant: {green}'}), 500

        # Step 1: Cut girl video
        subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-t', str(tmpl['cut']),
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
            '-r', '30', '-c:v', 'libx264', '-preset', 'ultrafast',
            '-an', girl_path
        ], capture_output=True, timeout=120)

        # Step 2: Concat girl + green
        with open(concat_path, 'w') as f:
            f.write(f"file '{os.path.abspath(girl_path)}'\nfile '{green}'\n")

        # Drawtext caption
        safe_caption = caption.replace("'", "'\\''").replace(":", "\\:").replace("%", "%%")
        drawtext = (
            f"drawtext=text='{safe_caption}':"
            f"fontsize=36:fontcolor=white:borderw=2:bordercolor=black:"
            f"x=(w-text_w)/2:y=h*0.08"
        )

        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_path,
            '-vf', drawtext,
            '-c:v', 'libx264', '-preset', 'ultrafast', '-an',
            video_path
        ], capture_output=True, timeout=120)

        # Step 3: Add audio
        subprocess.run([
            'ffmpeg', '-y', '-i', video_path, '-i', audio,
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-map', '0:v:0', '-map', '1:a:0',
            '-shortest', '-movflags', '+faststart',
            output_path
        ], capture_output=True, timeout=120)

        if not os.path.exists(output_path):
            return jsonify({'error': 'FFmpeg a échoué'}), 500

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
    finally:
        for f in [input_path, girl_path, concat_path, video_path]:
            try: os.remove(f)
            except: pass


# ── CAPTION MODE ──

@app.route('/caption', methods=['POST'])
def process_caption():
    """Single video — random caption overlay."""
    if 'video' not in request.files:
        return jsonify({'error': 'Pas de vidéo'}), 400

    video = request.files['video']
    caption = random.choice(CAPTION_TEXTS)
    uid = str(uuid.uuid4())[:8]
    ext = os.path.splitext(video.filename)[1] or '.mp4'
    input_path = os.path.join(UPLOAD_DIR, f'{uid}_in{ext}')
    output_path = os.path.join(OUTPUT_DIR, f'caption_{uid}.mp4')

    video.save(input_path)

    try:
        _add_caption_ffmpeg(input_path, output_path, caption)
        filename = f'caption_{uid}.mp4'
        return jsonify({
            'ok': True,
            'file': filename,
            'caption': caption,
            'download': f'/download/{filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


@app.route('/caption-batch', methods=['POST'])
def process_caption_batch():
    """Multiple videos — each gets a random caption, return zip."""
    files = request.files.getlist('videos')
    if not files:
        return jsonify({'error': 'Pas de vidéos'}), 400

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, video in enumerate(files):
            caption = random.choice(CAPTION_TEXTS)
            uid = str(uuid.uuid4())[:8]
            ext = os.path.splitext(video.filename)[1] or '.mp4'
            input_path = os.path.join(UPLOAD_DIR, f'{uid}_in{ext}')
            output_path = os.path.join(UPLOAD_DIR, f'{uid}_out.mp4')

            video.save(input_path)

            try:
                _add_caption_ffmpeg(input_path, output_path, caption)
                zf.write(output_path, f'caption_{i+1}.mp4')
            except Exception as e:
                print(f'Caption batch error on video {i+1}: {e}')
            finally:
                for p in [input_path, output_path]:
                    if os.path.exists(p):
                        os.remove(p)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'captions_batch_{int(time.time())}.zip'
    )


def _add_caption_ffmpeg(input_path, output_path, caption):
    """Overlay white text + black outline on video, keep audio."""
    safe = caption.replace("\\", "\\\\\\\\")
    safe = safe.replace("'", "'\\''")
    safe = safe.replace(":", "\\:")
    safe = safe.replace("%", "%%")

    drawtext = (
        f"drawtext=text='{safe}':"
        f"fontsize=(w/18):"
        f"fontcolor=white:"
        f"borderw=3:"
        f"bordercolor=black:"
        f"x=(w-text_w)/2:"
        f"y=(h-text_h)/2:"
        f"line_spacing=8"
    )

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-vf', drawtext,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'copy',
        '-movflags', '+faststart',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise Exception(f'FFmpeg error: {result.stderr[-500:]}')


# ── SHARED ──

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Fichier non trouvé'}), 404
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
    return send_file(zip_buf, as_attachment=True,
                     download_name=f'reels_batch_{int(time.time())}.zip',
                     mimetype='application/zip')


@app.before_request
def cleanup_old():
    for d in [UPLOAD_DIR, OUTPUT_DIR]:
        for f in glob.glob(os.path.join(d, '*')):
            if time.time() - os.path.getmtime(f) > 3600:
                try: os.remove(f)
                except: pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
