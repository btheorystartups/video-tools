"""Decode, inspect timings, and extract representative encoded rough-cut frames."""
import array
import hashlib
import json
from pathlib import Path
import re
import subprocess
import wave

from PIL import Image, ImageDraw, ImageFont
from render_rough_cut import ROOT, FFMPEG, FONT


def parse_time(raw):
    h,m,s = raw.replace(',', '.').split(':')
    return int(h)*3600+int(m)*60+float(s)


def main():
    video=ROOT/'video-insight-bundler-rough-cut.mp4'
    report=json.loads((ROOT/'render-report.json').read_text(encoding='utf-8'))
    text=(ROOT/'narration.txt').read_text(encoding='utf-8')
    words=json.loads((ROOT/'speech-timing.json').read_text(encoding='utf-8'))['words']
    assert all(text[r['position']:r['position']+r['count']]==r['text'] for r in words)
    cues=re.findall(r'\d+\n(.*?) --> (.*?)\n(.*?)(?=\n\n|\Z)',(ROOT/'rough-cut.srt').read_text(encoding='utf-8'),re.S)
    previous=0
    for start,end,_ in cues:
        a,b=parse_time(start),parse_time(end)
        assert previous<=a<b<=report['duration_seconds']+.01
        previous=b
    payload=json.loads((ROOT/'captures/review-notes-manual-copy.json').read_text(encoding='utf-8'))
    assert 'Leave open pending original-media review.' in payload['notes']
    assert all(item['completed'] for item in payload['checklist'])
    result=subprocess.run([str(FFMPEG),'-hide_banner','-nostdin','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-'],capture_output=True,text=True)
    (ROOT/'decode-check.log').write_text(result.stderr,encoding='utf-8')
    assert result.returncode==0,result.stderr[-4000:]
    assert re.search(r'Video: h264.*1920x1080.*24 fps',result.stderr)
    assert re.search(r'Audio: aac',result.stderr)
    quiet=[]
    with wave.open(str(ROOT/'narration.wav')) as audio:
        rate=audio.getframerate();values=array.array('h',audio.readframes(audio.getnframes()))
    block=round(rate*.02);start=None
    for i in range(0,len(values),block):
        silent=max(map(abs,values[i:i+block]),default=0)<328
        if silent and start is None:start=i/rate
        if not silent and start is not None:
            if i/rate-start>=.8:quiet.append({'start':start,'duration':i/rate-start})
            start=None
    if start is not None and len(values)/rate-start>=.8:
        quiet.append({'start':start,'duration':len(values)/rate-start})
    qa=ROOT/'qa';qa.mkdir(exist_ok=True)
    frames=[]
    for i,shot in enumerate(report['shots']):
        at=(shot['start']+shot['end'])/2
        path=qa/f'{i:02}-{shot["frame"]}.png'
        result=subprocess.run([str(FFMPEG),'-hide_banner','-loglevel','error','-y','-ss',str(at),'-i',str(video),'-frames:v','1',str(path)],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        frames.append(path)
    sheet=Image.new('RGB',(1920,4*398),'#101a2a');draw=ImageDraw.Draw(sheet)
    face=ImageFont.truetype(str(FONT),21)
    for i,path in enumerate(frames):
        x=(i%3)*640;y=(i//3)*398
        image=Image.open(path);assert image.size==(1920,1080)
        sheet.paste(image.resize((640,360),Image.Resampling.LANCZOS),(x,y))
        draw.text((x+10,y+367),path.stem,font=face,fill='white')
    sheet.save(qa/'contact-sheet.jpg',quality=93)
    final={'full_av_decode_passed':True,'resolution':[1920,1080],'fps':24,'video_codec':'H.264','audio_codec':'AAC','duration_seconds':report['duration_seconds'],'word_alignment_verified':True,'subtitle_cues':len(cues),'caption_bounds_verified':True,'representative_frames_extracted':len(frames),'manual_notes_copy_verified':True,'quiet_intervals_over_0_8_seconds':quiet,'longest_quiet_interval_seconds':max((x['duration'] for x in quiet),default=0),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'video_bytes':video.stat().st_size,'visual_review_pending':True}
    (ROOT/'verification.json').write_text(json.dumps(final,indent=2),encoding='utf-8')
    print(json.dumps(final,indent=2))


if __name__=='__main__':
    main()
