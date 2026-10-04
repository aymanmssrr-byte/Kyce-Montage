import os, random, subprocess, uuid, time, glob, zipfile, io
from flask import Flask, request, jsonify, send_file, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

UPLOAD_DIR = '/tmp/uploads'
OUTPUT_DIR = '/tmp/outputs'
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

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
    "POV the party was supposed to be chill",
    "POV she promised it was her last drink",
    "POV he said I will be home early",
    "POV she said we are just friends",
    "POV he said dont worry about him",
    "POV she said I deleted his number",
    "POV she said she was staying in tonight",
]

CAPTION_TEXTS = [
    "My two cousins wanted to play a game with me",
    "I goon to audios of men whimpering",
    "replace the k with f and a with t",
    "a boy typed 55378008 on calculator",
    "be a good boy and read this backwards",
    "Biology But without b o g",
    "I might be an 18yo blond but I am not stupid",
    "Black without Bla Dirt without rt",
    "acc so small if you like my reels I WILL send you something",
    "I am so single I text everyone who follows me",
    "Is 2008 too young",
    "If you have crush on me pls go for it",
    "I look like 18 because older man",
    "You can only pick two iPhone 18 Pro or Me",
    "he says you just a babyyy instead of blocking me",
    "give me a like and say good morning",
    "i want to call him good boy buy him hot wheels",
    "Is 2007 too young",
    "theep droat Queen Now read every third word",
]


def safe(text):
    return text.replace("'", "").replace(":", "\\:").replace("%", "%%")


def drawtext(text, fontsize, y_expr):
    s = safe(text)
    return "drawtext=fontfile=" + FONT + ":text='" + s + "':fontsize=" + str(fontsize) + ":fontcolor=white:borderw=3:bordercolor=black:x=(w-text_w)/2:y=" + y_expr


@app.route('/debug')
def debug():
    info = {}
    try:
        r = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=10)
        info['ffmpeg'] = r.stdout.split('\n')[0]
    except:
        info['ffmpeg'] = 'NOT FOUND'
    info['font_exists'] = os.path.exists(FONT)
    assets_dir = os.path.join(BASE_DIR, 'assets')
    info['assets'] = os.listdir(assets_dir) if os.path.exists(assets_dir) else 'MISSING'
    return jsonify(info)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_montage():
    if 'video' not in request.files:
        return jsonify({'error': 'Pas de video'}), 400
    video = request.files['video']
    uid = str(uuid.uuid4())[:8]
    tmpl = random.choice(TEMPLATES)
    caption = random.choice(MONTAGE_CAPTIONS)
    ip = os.path.join(UPLOAD_DIR, uid + '_in.mp4')
    gp = os.path.join(UPLOAD_DIR, uid + '_girl.mp4')
    cp = os.path.join(UPLOAD_DIR, uid + '_concat.txt')
    vp = os.path.join(UPLOAD_DIR, uid + '_video.mp4')
    oname = 'reel_' + tmpl['id'] + '_' + uid + '.mp4'
    op = os.path.join(OUTPUT_DIR, oname)
    video.save(ip)
    try:
        green = os.path.abspath(tmpl['green'])
        audio = os.path.abspath(tmpl['audio'])
        if not os.path.exists(green):
            return jsonify({'error': 'Asset manquant'}), 500
        subprocess.run(['ffmpeg','-y','-i',ip,'-t',str(tmpl['cut']),'-vf','scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1','-r','30','-c:v','libx264','-preset','ultrafast','-an',gp], capture_output=True, timeout=120)
        if not os.path.exists(gp):
            return jsonify({'error': 'Cut echoue'}), 500
        with open(cp,'w') as f:
            f.write("file '"+os.path.abspath(gp)+"'\nfile '"+green+"'\n")
        dt = drawtext(caption, 36, "h*0.08")
        subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',cp,'-vf',dt,'-c:v','libx264','-preset','ultrafast','-an',vp], capture_output=True, timeout=120)
        if not os.path.exists(vp):
            return jsonify({'error': 'Concat echoue'}), 500
        subprocess.run(['ffmpeg','-y','-i',vp,'-i',audio,'-c:v','copy','-c:a','aac','-b:a','192k','-map','0:v:0','-map','1:a:0','-shortest','-movflags','+faststart',op], capture_output=True, timeout=120)
        if not os.path.exists(op):
            return jsonify({'error': 'Audio echoue'}), 500
        return jsonify({'ok':True,'file':oname,'template':tmpl['id'],'caption':caption,'download':'/download/'+oname})
    except Exception as e:
        return jsonify({'error':str(e)}), 500
    finally:
        for f in [ip,gp,cp,vp]:
            try: os.remove(f)
            except: pass

@app.route('/caption', methods=['POST'])
def process_caption():
    if 'video' not in request.files:
        return jsonify({'error': 'Pas de video'}), 400
    video = request.files['video']
    caption = random.choice(CAPTION_TEXTS)
    uid = str(uuid.uuid4())[:8]
    ip = os.path.join(UPLOAD_DIR, uid + '_in.mp4')
    oname = 'caption_' + uid + '.mp4'
    op = os.path.join(OUTPUT_DIR, oname)
    video.save(ip)
    try:
        dt = drawtext(caption, 32, "(h-text_h)/2")
        r = subprocess.run(['ffmpeg','-y','-i',ip,'-vf',dt,'-c:v','libx264','-preset','fast','-crf','23','-c:a','copy','-movflags','+faststart',op], capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return jsonify({'error':'FFmpeg: '+r.stderr[-500:]}), 500
        return jsonify({'ok':True,'file':oname,'caption':caption,'download':'/download/'+oname})
    except Exception as e:
        return jsonify({'error':str(e)}), 500
    finally:
        if os.path.exists(ip): os.remove(ip)

@app.route('/caption-batch', methods=['POST'])
def process_caption_batch():
    files = request.files.getlist('videos')
    if not files:
        return jsonify({'error':'Pas de videos'}), 400
    zb = io.BytesIO()
    with zipfile.ZipFile(zb,'w',zipfile.ZIP_DEFLATED) as zf:
        for i,video in enumerate(files):
            caption = random.choice(CAPTION_TEXTS)
            uid = str(uuid.uuid4())[:8]
            ip = os.path.join(UPLOAD_DIR, uid+'_in.mp4')
            op = os.path.join(UPLOAD_DIR, uid+'_out.mp4')
            video.save(ip)
            try:
                dt = drawtext(caption, 32, "(h-text_h)/2")
                subprocess.run(['ffmpeg','-y','-i',ip,'-vf',dt,'-c:v','libx264','-preset','fast','-crf','23','-c:a','copy','-movflags','+faststart',op], capture_output=True, timeout=300)
                if os.path.exists(op):
                    zf.write(op,'caption_'+str(i+1)+'.mp4')
            except: pass
            finally:
                for p in [ip,op]:
                    if os.path.exists(p): os.remove(p)
    zb.seek(0)
    return send_file(zb, mimetype='application/zip', as_attachment=True, download_name='captions_batch.zip')

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'error':'Non trouve'}), 404
    return send_file(path, as_attachment=True, download_name=filename)

@app.route('/download-all')
def download_all():
    files = glob.glob(os.path.join(OUTPUT_DIR,'reel_*.mp4'))
    if not files:
        return jsonify({'error':'Aucun reel'}), 404
    zb = io.BytesIO()
    with zipfile.ZipFile(zb,'w',zipfile.ZIP_DEFLATED) as zf:
        for f in files: zf.write(f, os.path.basename(f))
    zb.seek(0)
    return send_file(zb, as_attachment=True, download_name='reels_batch.zip', mimetype='application/zip')

@app.before_request
def cleanup_old():
    for d in [UPLOAD_DIR, OUTPUT_DIR]:
        for f in glob.glob(os.path.join(d,'*')):
            if time.time()-os.path.getmtime(f)>3600:
                try: os.remove(f)
                except: pass

if __name__=='__main__':
    port = int(os.environ.get('PORT',5000))
    app.run(host='0.0.0.0', port=port, debug=False)
