"""Reproducible rough-cut render from real CUA captures and local scratch voice."""
from __future__ import annotations

import argparse
import json
import hashlib
from pathlib import Path
import re
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT.parents[1] / 'docs/video_walkthrough_script.md'
FFMPEG = Path(r'C:\Users\brian\AppData\Local\Programs\Python\Python310\lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v7.1.exe')
FONT = Path(r'C:\Windows\Fonts\segoeui.ttf')
BOLD = Path(r'C:\Windows\Fonts\segoeuib.ttf')
W, H = 1920, 1080


def save_json(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def prepare():
    text = SCRIPT.read_text(encoding='utf-8')
    scenes = []
    paragraphs = []
    position = 0
    for number, title, body in re.findall(r'## Scene (\d+) ([^\n]+)\n(.*?)(?=\n## |\Z)', text, re.S):
        speech = ' '.join(line[2:] for line in body.splitlines() if line.startswith('> '))
        # Pronunciation only; the displayed website remains correctly spelled.
        speech = speech.replace('CorrespondenceMatrices.com', 'Correspondence matrices dot com').replace('—', ', ')
        scenes.append({'number': int(number), 'title': title, 'narration': speech, 'character_start': position, 'character_end': position + len(speech)})
        paragraphs.append(speech)
        position += len(speech) + 2
    assert len(scenes) == 6
    (ROOT / 'narration.txt').write_text('\n\n'.join(paragraphs), encoding='utf-8')
    save_json('scenes.json', scenes)
    print('Prepared six scene paragraphs for one continuous local narration.')


def run(args):
    result = subprocess.run([str(FFMPEG), '-hide_banner', '-loglevel', 'error', *map(str, args)], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def wrapped(draw, text, xy, width, size=34, color='#e6edf5', bold=False, leading=1.35):
    face = font(size, bold)
    lines = []
    line = ''
    for word in text.split():
        trial = (line + ' ' + word).strip()
        if line and draw.textlength(trial, font=face) > width:
            lines.append(line)
            line = word
        else:
            line = trial
    if line:
        lines.append(line)
    for i, line in enumerate(lines):
        draw.text((xy[0], xy[1] + i * size * leading), line, font=face, fill=color)
    return xy[1] + len(lines) * size * leading


def frame(title, subtitle):
    image = Image.new('RGB', (W, H), '#0c1423')
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, W, 7), fill='#49c5b6')
    draw.text((70, 35), 'BRIAN THEORY  /  APPLIED AI & R&D', font=font(24, True), fill='#80dace')
    draw.text((W-400, 35), 'ROUGH CUT · SCRATCH VOICE', font=font(21), fill='#aebccc')
    wrapped(draw, title, (70, 85), 1760, size=48, bold=True)
    wrapped(draw, subtitle, (70, 156), 1760, size=27, color='#aebccc')
    draw.text((70, 936), 'Actual browser stills · saved analysis · human review', font=font(23), fill='#aebccc')
    return image, draw


def capture_card(image, capture, box, dest=(630, 236, 1848, 910)):
    shot = Image.open(ROOT / 'captures' / capture).convert('RGB')
    shot = shot.crop(tuple(round(v) for v in box))
    target_w, target_h = dest[2]-dest[0], dest[3]-dest[1]
    factor = min(target_w/shot.width, target_h/shot.height)
    shot = shot.resize((round(shot.width*factor), round(shot.height*factor)), Image.Resampling.LANCZOS)
    left = dest[0] + (target_w-shot.width)//2
    top = dest[1] + (target_h-shot.height)//2
    image.paste(shot, (left, top))
    return (left, top, shot.width, shot.height)


def write_frame(name, title, subtitle, capture=None, box=None, takeaway='', bullets=()):
    image, draw = frame(title, subtitle)
    if capture:
        placed = capture_card(image, capture, box)
        if name == '03-timeline':
            focus = json.loads((ROOT/'capture-layout.json').read_text(encoding='utf-8'))['timeline']['focus']
            scale = placed[2]/(box[2]-box[0])
            bounds = [placed[0]+(focus['x']-box[0])*scale, placed[1]+(focus['y']-box[1])*scale, placed[0]+(focus['right']-box[0])*scale, placed[1]+(focus['bottom']-box[1])*scale]
            draw.rectangle(bounds, outline='#49c5b6', width=5)
    y = wrapped(draw, takeaway, (70, 280), 500, size=40, bold=True)
    for bullet in bullets:
        y = wrapped(draw, bullet, (70, y+38), 500, size=29, color='#b6d7dc')
    image.save(ROOT / f'{name}.png')


def srt_time(seconds):
    ms = round(seconds*1000)
    return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'


def subtitles(words, duration):
    full = (ROOT/'narration.txt').read_text(encoding='utf-8')
    chunks, current = [], []
    for row in words:
        current.append(row)
        text = ' '.join(x['text'] for x in current)
        punctuation = full[row['position']+row['count']:row['position']+row['count']+1]
        if len(text) >= 74 or len(current) >= 13 or (len(current) >= 5 and punctuation in ('.', '?', ';')):
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    cues = []
    for i, group in enumerate(chunks):
        end_position = chunks[i+1][0]['position'] if i+1 < len(chunks) else len(full)
        text = ' '.join(full[group[0]['position']:end_position].split())
        tokens = text.split()
        midpoint = len(tokens)//2
        lines = text if len(text) <= 52 else ' '.join(tokens[:midpoint]) + '\n' + ' '.join(tokens[midpoint:])
        end = chunks[i+1][0]['seconds']-.04 if i+1 < len(chunks) else duration-.1
        cues.append(f'{i+1}\n{srt_time(group[0]["seconds"])} --> {srt_time(max(end,group[0]["seconds"]+.3))}\n{lines}\n')
    (ROOT / 'rough-cut.srt').write_text('\n'.join(cues), encoding='utf-8')
    return len(cues)


def render():
    previous_frames = {path.stem: hashlib.sha256(path.read_bytes()).hexdigest() for path in ROOT.glob('*.png')}
    previous_report = json.loads((ROOT/'render-report.json').read_text(encoding='utf-8')) if (ROOT/'render-report.json').is_file() else {}
    previous_shots = {row['frame']: row for row in previous_report.get('shots', [])}
    scenes = json.loads((ROOT / 'scenes.json').read_text(encoding='utf-8'))
    timing = json.loads((ROOT / 'speech-timing.json').read_text(encoding='utf-8'))
    words = sorted(timing['words'], key=lambda row: row['seconds'])
    with wave.open(str(ROOT / 'narration.wav')) as audio:
        duration = audio.getnframes()/audio.getframerate()
    assert len(words) > 200, 'Speech timing did not capture the narration'
    assert words[-1]['seconds'] < duration, 'Speech event times exceed the WAV duration'
    for scene in scenes:
        scene['start_seconds'] = next(row['seconds'] for row in words if row['position'] >= scene['character_start'])
    scenes[0]['start_seconds'] = 0
    for i, scene in enumerate(scenes):
        scene['end_seconds'] = scenes[i+1]['start_seconds'] if i+1 < len(scenes) else duration
    save_json('scene-timing.json', scenes)
    layout = json.loads((ROOT/'capture-layout.json').read_text(encoding='utf-8'))
    boxes = layout['walkthrough']['boxes']
    title_box = (layout['walkthrough']['main_x'], 20, layout['walkthrough']['main_right'], boxes['segment-evidence']['y']-20)
    def rect(box, pad=8):
        return (box['x']-pad, box['y']-pad, box['x']+box['width']+pad, box['y']+box['height']+pad)
    write_frame('01-problem','What supports this recommendation?', 'A working prototype for a familiar review problem', 'walkthrough.jpg', rect(boxes['segment-recommendation']), 'Make the analysis usable.', ('Which evidence?', 'Which review decision?', 'What happens next?'))
    write_frame('02-design','Separate the signals, connect the decisions', 'Video Insight Bundler · working prototype · saved analysis', 'walkthrough.jpg', title_box, 'Evidence people can inspect.', ('Recorded signals', 'Source references', 'Human review'))
    write_frame('03-timeline','Locate the opening segment','One example video · 0.00–14.64 seconds', 'timeline.jpg', layout['timeline']['crop'], 'Find the relevant moment.', ('Opening fifteen seconds', 'Read the context before deciding'))
    write_frame('04-context','Inspect the segment context','Actual review guidance · original media requires separate review', 'context.jpg', layout['context']['crop'], 'Preserve intentional choices.', ('What to preserve', 'What to review', 'What not to infer'))
    write_frame('05-signals','Read the recorded signals','Review cues, not conclusions', 'walkthrough.jpg', rect(boxes['segment-evidence']), 'Frame a review question.', ('Signals guide inspection', 'They are not probabilities'))
    write_frame('06-recommendation','Assess the linked recommendation','Human review before editorial changes', 'walkthrough.jpg', rect(boxes['segment-recommendation']), 'Is a clearer transition needed?', ('Check the original media', 'Record the next step'))
    note_layout=layout['notes']
    write_frame('07-note','Give the next reviewer a starting point','Demonstration note · editorial decision remains open', 'notes.jpg', note_layout['crop'], 'A clear review record.', ('Evidence checked', 'Uncertainty preserved', 'Next action identified'))
    write_frame('08-export','Keep the review record with the package','Explicit external save · no autosave', 'notes.jpg', note_layout['export_crop'], 'Export the note and checklist.', ('Payload verified on screen', 'Manual-save fallback available'))
    concept, draw = frame('Video is the example, not the limit','Possible custom applications · scoped and evaluated for each client')
    draw.rectangle((0,927,W,977),fill='#0c1423')
    draw.text((70,936),'Conceptual workflow · possible custom applications',font=font(23),fill='#aebccc')
    stages=['Inputs','Evidence','Human review','Decision record']
    for i, stage in enumerate(stages):
        x=70+i*465
        draw.rounded_rectangle((x,300,x+400,455),radius=16,fill='#183248',outline='#49c5b6',width=3)
        wrapped(draw,stage,(x+25,350),350,size=34,bold=True)
        if i<3: draw.text((x+411,346),'→',font=font(43),fill='#49c5b6')
    for i, domain in enumerate(['Research documents','Engineering evidence','Internal review']):
        x=70+i*610
        draw.rounded_rectangle((x,560,x+550,760),radius=16,fill='#152235')
        wrapped(draw,domain,(x+28,615),490,size=36,bold=True)
    draw.text((70,821),'The decision, inputs and constraints determine the system.',font=font(31),fill='#c9d9e7')
    concept.save(ROOT/'09-possibilities.png')
    close, draw=frame('What decision does your team need to make?','A focused conversation about goals, constraints and a practical next step')
    draw.rectangle((0,927,W,977),fill='#0c1423')
    draw.text((70,936),'CorrespondenceMatrices.com · Applied AI and R&D consulting',font=font(23),fill='#aebccc')
    draw.text((100,310),'Brian Theory',font=font(66,True),fill='#edf4fa')
    draw.text((100,410),'Applied AI and R&D consulting',font=font(40),fill='#80dace')
    draw.rounded_rectangle((100,550,1810,740),radius=20,fill='#183248')
    draw.text((145,580),'CorrespondenceMatrices.com',font=font(62,True),fill='#edf4fa')
    draw.text((145,664),'Request a 20-minute fit call',font=font(34),fill='#80dace')
    close.save(ROOT/'10-invitation.png')
    a=[s['start_seconds'] for s in scenes]+[duration]
    # Shot cuts follow actual speech-word positions, not padded scene targets.
    def phrase_time(needle, fallback):
        full=(ROOT/'narration.txt').read_text(encoding='utf-8')
        at=full.find(needle)
        return next((r['seconds'] for r in words if r['position']>=at),fallback) if at>=0 else fallback
    shots=[('01-problem',a[0],a[1]),('02-design',a[1],a[2]),('03-timeline',a[2],phrase_time('its context',a[2]+7)),('04-context',phrase_time('its context',a[2]+7),phrase_time("I'll compare",a[2]+11)),('05-signals',phrase_time("I'll compare",a[2]+11),phrase_time('inspect whether',a[2]+17)),('06-recommendation',phrase_time('inspect whether',a[2]+17),a[3]),('07-note',a[3],phrase_time('I can export',a[3]+17)),('08-export',phrase_time('I can export',a[3]+17),a[4]),('09-possibilities',a[4],a[5]),('10-invitation',a[5],a[6])]
    cue_count=subtitles(words,duration)
    part_dir=ROOT/'parts';part_dir.mkdir(exist_ok=True)
    for i,(name,start,end) in enumerate(shots):
        seconds=end-start
        assert seconds>0
        frames=round(end*24)-round(start*24)
        old = previous_shots.get(name, {})
        part = part_dir/f'{i:02}.mp4'
        fingerprint = hashlib.sha256((ROOT/f'{name}.png').read_bytes()).hexdigest()
        if part.is_file() and previous_frames.get(name) == fingerprint and old.get('start') == start and old.get('end') == end:
            print('Reused unchanged shot', name, flush=True)
            continue
        # Very gentle editorial zoom on captured stills, no fake cursor actions.
        zoom="zoompan=z='min(1.018,1+on*0.000025)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1920x1080:fps=24"
        run(['-y','-loop','1','-framerate','24','-i',ROOT/f'{name}.png','-vf',zoom,'-frames:v',frames,'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p',part])
        print('Encoded',name,round(seconds,2),'seconds',flush=True)
    concat=''.join(f"file '{(part_dir/f'{i:02}.mp4').as_posix()}'\n" for i in range(len(shots)))
    (ROOT/'concat.txt').write_text(concat,encoding='utf-8')
    run(['-y','-f','concat','-safe','0','-i',ROOT/'concat.txt','-c','copy',ROOT/'picture.mp4'])
    # ASS subtitles are placed in a dedicated footer below the capture area.
    ass_header="[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,Segoe UI,36,&H00FFFFFF,&H00FFFFFF,&H0023140C,&H0023140C,0,0,0,0,100,100,0,0,1,2,0,2,100,100,26,1\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    def ass_time(s):
        return f'{int(s)//3600}:{int(s)//60%60:02}:{s%60:05.2f}'
    events=[]
    for match in re.finditer(r'\d+\n(.*?) --> (.*?)\n(.*?)(?=\n\n|\Z)',(ROOT/'rough-cut.srt').read_text(encoding='utf-8'),re.S):
        def seconds(raw):
            h,m,s=raw.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(s)
        subtitle=match[3].strip().replace('\n',r'\N')
        events.append(f'Dialogue: 0,{ass_time(seconds(match[1]))},{ass_time(seconds(match[2]))},Default,,0,0,0,,{subtitle}')
    (ROOT/'captions.ass').write_text(ass_header+'\n'.join(events),encoding='utf-8')
    ass_path=(ROOT/'captions.ass').as_posix().replace(':',r'\:')
    run(['-y','-i',ROOT/'picture.mp4','-i',ROOT/'narration.wav','-vf',f"ass='{ass_path}'",'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-t',duration,'-movflags','+faststart',ROOT/'video-insight-bundler-rough-cut.mp4'])
    save_json('render-report.json',{'duration_seconds':duration,'resolution':[W,H],'fps':24,'narration':timing['kind'],'voice':timing['voice'],'subtitle_cues':cue_count,'shots':[{'frame':n,'start':s,'end':e} for n,s,e in shots],'capture_kind':'actual CUA browser stills with editorial crops and restrained zoom; not a continuous screen recording','external_services_used':False})
    print('Rendered rough cut',round(duration,2),'seconds',flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['prepare','render'])
    args=parser.parse_args()
    prepare() if args.mode=='prepare' else render()
