import os
import random
import subprocess
import uuid
import time
import glob
import zipfile
import io
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

MONTAGE_CAPTIONS = [
    "POV Before everything was going so well",
    "This might be a bad idea",
    "This is your sign to look closer",
    "Only a few people noticed this",
    "POV the date was going perfectly",
    "POV she said she was a good girl",
    "POV you trusted her with your hoodie",
    "POV she said I never do this",
    "POV he said it was just a friend",
    "POV the night started so innocent",
    "POV she texted come over I am bored",
    "POV you left her alone for 5 minutes",
    "POV everything was fine until midnight",
    "POV she said lets just watch a movie",
    "POV you believed her when she said goodnight",
    "POV the party was supposed to be chill",
    "POV she promised it was her last drink",
    "POV he said I will be home early",
    "POV she said we are just friends",
    "POV he said dont worry about him",
    "POV it was supposed to be a quiet night",
    "POV she said I deleted his number",
    "POV the uber was supposed to go home",
    "POV she said she was staying in tonight",
]

CAPTION_TEXTS = [
    "My two cousins wanted to play a game with me it hurt",
    "I goon to audios of men whimpering but no one is ever gonna know cuz I barely have any followers",
    "I want to kiss me but replace the k with f and a with t",
    "when I was 14 a boy typed 55378008 on calculator turned it upside down and said thats you",
    "be a good boy and read this backwards elihc dna emina hctaw ew elihw",
    "Biology But without b o g",
    "I might be an 18yo blond but I am not stupid",
    "What I really need Black without Bla Dirt without rt Four without Fo YOLO without LO",
    "acc so small that if you like any of my reels I WILL send you something in dms",
    "I am so single I literally text everyone who follows me",
    "Is 2008 too young",
    "If you have crush on me pls go for it you literally have no competition at all",
    "I look like 18 because older man Dont take me Serious",
    "You can only pick two iPhone 18 Pro or 500 dollars or Me or Infinite beer",
    "when i tell older guy my age and he says you just a babyyy instead of blocking me",
    "lets make a deal you give me a like and say good morning and ill message you",
    "this mommy stuff aint no joke i want to call him good boy buy him hot wheels",
    "Is 2007 too young",
    "Amazing cook legs for days theep droat Queen Now read every third word",
]


# ── DEBUG ──
@app.route('/debug')
def debug():
    info = {}
    # Check FFmpeg
    try:
        r = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        info['ffmpeg'] = r.stdout.split('\n')[0] if r.returncode == 0 else 'NOT FOUND'
    except:
        info['ffmpeg'] = 'NOT FOUND'

    # Check assets
    assets_dir = os.path.join(BASE_DIR, 'assets')
    if os.path.exists(assets_dir):
        info['assets'] = os.listdir(assets_dir)
    else:
        info['assets'] = 'FOLDER MISSING'

    # Check templates dir
    tmpl_dir = os.path.join(BASE_DIR, 'templates')
    if os.path.exists(tmpl_dir):
        info['templates'] = os.listdir(tmpl_dir)
    else:
        info['templates'] = 'FOLDER MISSING'

    info['base_dir'] = BASE_DIR
    info['upload_dir'] = UPLOAD_DIR
    info['output_dir'] = OUTPUT_DIR

    return jsonify(info)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/captions')
def get_captions():
    return jsonify({'montage': MONTAGE_CAPTIONS, 'caption': CAPTION_TEXTS})


# ── MONTAGE VERT ──
@app.route('/process', methods=['POST'])
def process_montage():
    if 'video' not in request.files:
        return jsonify({'error': 'Pas de video'}), 400

    video = request.files['video']
    uid = str(uuid.uuid4())[:8]
    tmpl = random.choice(TEMPLATES)
    caption = random.choice(MONTAGE_CAPTIONS)

    input_path = os.path.join(UPLOAD_DIR, uid + '_in.mp4')
    girl_path = os.path.join(UPLOAD_DIR, uid + '_girl.mp4')
    concat_path = os.path.join(UPLOAD_DIR, uid + '_concat.txt')
    video_path = os.path.join(UPLOAD_DIR, uid + '_video.mp4')
    txt_path = os.path.join(UPLOAD_DIR, uid + '_cap.txt')
    output_name = 'reel_' + tmpl['id'] + '_' + uid + '.mp4'
    output_path = os.path.join(OUTPUT_DIR, output_name)

    video.save(input_path)

    try:
        green = os.path.abspath(tmpl['green'])
        audio = os.path.abspath(tmpl['audio'])

        if not os.path.exists(green):
            return jsonify({'error': 'Asset manquant: ' + green}), 500
        if not os.path.exists(audio):
            return jsonify({'error': 'Audio manquant: ' + audio}), 500

        # Step 1: Cut girl video
        r1 = subprocess.run([
            'ffmpeg', '-y', '-i', input_path,
            '-t', str(tmpl['cut']),
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
            '-r', '30', '-c:v', 'libx264', '-preset', 'ultrafast',
            '-an', girl_path
        ], capture_output=True, text=True, timeout=120)

        if not os.path.exists(girl_path):
            return jsonify({'error': 'Step1 fail: ' + r1.stderr[-300:]}), 500

        # Step 2: Concat girl + green with caption
        with open(concat_path, 'w') as f:
            f.write("file '" + os.path.abspath(girl_path) + "'\n")
            f.write("file '" + green + "'\n")

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(caption)

        drawtext = "drawtext=textfile='" + txt_path + "':fontsize=36:fontcolor=white:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h*0.08"

        r2 = subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_path,
            '-vf', drawtext,
            '-c:v', 'libx264', '-preset', 'ultrafast', '-an',
            video_path
        ], capture_output=True, text=True, timeout=120)

        if not os.path.exists(video_path):
            return jsonify({'error': 'Step2 fail: ' + r2.stderr[-300:]}), 500

        # Step 3: Add audio
        r3 = subprocess.run([
            'ffmpeg', '-y', '-i', video_path, '-i', audio,
            '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
            '-map', '0:v:0', '-map', '1:a:0',
            '-shortest', '-movflags', '+faststart',
            output_path
        ], capture_output=True, text=True, timeout=120)

        if not os.path.exists(output_path):
            return jsonify({'error': 'Step3 fail: ' + r3.stderr[-300:]}), 500

        return jsonify({
            'ok': True,
            'file': output_name,
            'template': tmpl['id'],
            'caption': caption,
            'download': '/download/' + output_name
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        for f in [input_path, girl_path, concat_path, video_path, txt_path]:
            try: os.remove(f)
            except: pass


# ── CAPTION MODE ──
@app.route('/caption', methods=['POST'])
def process_caption():
    if 'video' not in request.files:
        return jsonify({'error': 'Pas de video'}), 400

    video = request.files['video']
    caption = random.choice(CAPTION_TEXTS)
    uid = str(uuid.uuid4())[:8]
    input_path = os.path.join(UPLOAD_DIR, uid + '_in.mp4')
    output_name = 'caption_' + uid + '.mp4'
    output_path = os.path.join(OUTPUT_DIR, output_name)

    video.save(input_path)

    try:
        _add_caption(input_path, output_path, caption, uid)
        return jsonify({
            'ok': True,
            'file': output_name,
            'caption': caption,
            'download': '/download/' + output_name
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)


@app.route('/caption-batch', methods=['POST'])
def process_caption_batch():
    files = request.files.getlist('videos')
    if not files:
        return jsonify({'error': 'Pas de videos'}), 400

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, video in enumerate(files):
            caption = random.choice(CAPTION_TEXTS)
            uid = str(uuid.uuid4())[:8]
            input_path = os.path.join(UPLOAD_DIR, uid + '_in.mp4')
            output_path = os.path.join(UPLOAD_DIR, uid + '_out.mp4')
            video.save(input_path)
            try:
                _add_caption(input_path, output_path, caption, uid)
                zf.write(output_path, 'caption_' + str(i + 1) + '.mp4')
            except Exception as e:
                print('Batch error ' + str(i + 1) + ': ' + str(e))
            finally:
                for p in [input_path, output_path, os.path.join(UPLOAD_DIR, uid + '_cap.txt')]:
                    if os.path.exists(p): os.remove(p)

    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name='captions_batch.zip')


def _add_caption(input_path, output_path, caption, uid):
    txt_path = os.path.join(UPLOAD_DIR, uid + '_cap.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(caption)

    drawtext = "drawtext=textfile='" + txt_path + "':fontsize=42:fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=(h-text_h)/2"

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-vf', drawtext,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-movflags', '+faststart',
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    try: os.remove(txt_path)
    except: pass

    if result.returncode != 0:
        raise Exception('FFmpeg: ' + result.stderr[-500:])


@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error': 'Fichier non trouve'}), 404
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
    return send_file(zip_buf, as_attachment=True, download_name='reels_batch.zip', mimetype='application/zip')


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
