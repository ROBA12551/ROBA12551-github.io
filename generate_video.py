import os
import json
import random
import requests
from moviepy.editor import *
from moviepy.audio.fx.all import volumex
from gtts import gTTS
import textwrap
import base64
import time

# Load configuration from environment variables
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
PIXABAY_API_KEY = os.getenv('PIXABAY_API_KEY')

# Configuration
CONFIG = {
    "fonts": [
        {"name": "Mystery", "path": "fonts/mistery.ttf"},
        {"name": "Horror", "path": "fonts/horror.ttf"}
    ],
    "color_schemes": [
        {"text": "#ffffff", "stroke": "#000000", "bg": "#1a1a2e"},
        {"text": "#00ffff", "stroke": "#0000ff", "bg": "#0f0f23"},
        {"text": "#ffffff", "stroke": "#ffd700", "bg": "#2d1b69"},
        {"text": "#ff99cc", "stroke": "#66ffcc", "bg": "#1a0033"},
        {"text": "#ffffff", "stroke": "#ff3333", "bg": "#330000"},
        {"text": "#ccccff", "stroke": "#ffcc00", "bg": "#003366"},
        {"text": "#00ff00", "stroke": "#ff0080", "bg": "#1a1a1a"}
    ],
    "transitions": [
        {"type": "fade", "duration": 0.5},
        {"type": "slide", "direction": "left", "duration": 0.5},
        {"type": "slide", "direction": "right", "duration": 0.5},
        {"type": "slide", "direction": "top", "duration": 0.5},
        {"type": "slide", "direction": "bottom", "duration": 0.5},
        {"type": "zoom", "duration": 0.5}
    ],
    "sound_effects": [
        {"name": "mystery", "path": "sounds/mystery.mp3"},
        {"name": "suspense", "path": "sounds/suspense.mp3"},
        {"name": "horror", "path": "sounds/horror.mp3"},
        {"name": "thriller", "path": "sounds/thriller.mp3"},
        {"name": "creepy", "path": "sounds/creepy.mp3"}
    ],
    "background_music": [
        {"name": "ambient", "path": "sounds/ambient.mp3"},
        {"name": "dark", "path": "sounds/dark.mp3"},
        {"name": "mysterious", "path": "sounds/mysterious.mp3"}
    ]
}

def load_stories():
    with open('stories.json', 'r') as f:
        return json.load(f)

def generate_story_segments(duration, story_type="random"):
    stories = load_stories()
    segments = []
    segment_count = max(1, duration // 10)  # 10 seconds per segment
    
    for _ in range(segment_count):
        if story_type == "random":
            digit = str(random.randint(0, 9))
        else:
            type_map = {
                "thriller": ["1", "3", "5"],
                "detective": ["2", "4", "7"],
                "supernatural": ["6", "8", "9", "0"]
            }
            digit = random.choice(type_map.get(story_type, ["0"]))
        
        segment_options = stories.get(digit, [])
        if segment_options:
            segments.append(random.choice(segment_options))
    
    return segments

def text_to_speech(text, output_file, speed=1.0):
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_file)
    
    audio = AudioFileClip(output_file)
    if speed != 1.0:
        audio = audio.fx(volumex, 1.0).fx(lambda c: c.speedx(factor=speed))
    return audio

def download_background_image():
    # Try Pexels first
    if PEXELS_API_KEY:
        try:
            api_url = f"https://api.pexels.com/v1/search?query=mystery&per_page=1&page={random.randint(1, 100)}"
            headers = {"Authorization": PEXELS_API_KEY}
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data['photos']:
                    image_url = data['photos'][0]['src']['large']
                    img_data = requests.get(image_url).content
                    with open('temp_bg.jpg', 'wb') as handler:
                        handler.write(img_data)
                    return 'temp_bg.jpg'
        except Exception as e:
            print(f"Pexels API error: {e}")

    # Fallback to Pixabay
    if PIXABAY_API_KEY:
        try:
            api_url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q=mystery&per_page=200"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                if data['hits']:
                    image_url = random.choice(data['hits'])['largeImageURL']
                    img_data = requests.get(image_url).content
                    with open('temp_bg.jpg', 'wb') as handler:
                        handler.write(img_data)
                    return 'temp_bg.jpg'
        except Exception as e:
            print(f"Pixabay API error: {e}")

    # Final fallback to local image
    return 'assets/default_bg.jpg'

def create_text_clip(text, duration, font_config, color_scheme):
    wrapped_text = "\n".join(textwrap.wrap(text, width=30))
    
    txt_clip = TextClip(
        wrapped_text,
        fontsize=48,
        color=color_scheme['text'],
        font=font_config['path'],
        stroke_color=color_scheme['stroke'],
        stroke_width=2,
        size=(720, 1280),
        method='caption',
        align='center'
    ).set_duration(duration)
    
    return txt_clip

def add_transition(clip1, clip2, transition):
    if transition['type'] == 'fade':
        return CompositeVideoClip([clip1.crossfadeout(transition['duration']),
                                 clip2.crossfadein(transition['duration'])])
    elif transition['type'] == 'slide':
        return concatenate_videoclips([clip1, clip2], transition=transition)
    else:
        return concatenate_videoclips([clip1, clip2])

def add_sound_effects(audio_clip, effect_type):
    effect_path = random.choice(CONFIG['sound_effects'])['path']
    if os.path.exists(effect_path):
        effect = AudioFileClip(effect_path)
        effect = effect.fx(volumex, 0.3)
        return CompositeAudioClip([audio_clip, effect])
    return audio_clip

def generate_video(story_type="random", duration=60, voice_speed=1.0):
    try:
        segments = generate_story_segments(duration, story_type)
        if not segments:
            return None
        
        segment_duration = duration / len(segments)
        
        font_config = random.choice(CONFIG['fonts'])
        color_scheme = random.choice(CONFIG['color_schemes'])
        transition = random.choice(CONFIG['transitions'])
        
        bg_image = download_background_image()
        bg_clip = ImageClip(bg_image).set_duration(duration)
        
        clips = []
        audio_clips = []
        
        for i, segment in enumerate(segments):
            txt_clip = create_text_clip(segment, segment_duration, font_config, color_scheme)
            
            speech_file = f"temp_speech_{i}.mp3"
            speech_audio = text_to_speech(segment, speech_file, voice_speed)
            audio_clips.append(speech_audio)
            
            clip = CompositeVideoClip([bg_clip.subclip(i*segment_duration, (i+1)*segment_duration), 
                                     txt_clip.set_position('center')])
            clips.append(clip)
        
        final_clip = clips[0]
        for i in range(1, len(clips)):
            final_clip = add_transition(final_clip, clips[i], transition)
        
        final_audio = concatenate_audioclips(audio_clips)
        final_audio = add_sound_effects(final_audio, "mystery")
        
        bg_music = random.choice(CONFIG['background_music'])
        if os.path.exists(bg_music['path']):
            music = AudioFileClip(bg_music['path']).fx(volumex, 0.2)
            music = music.subclip(0, duration)
            final_audio = CompositeAudioClip([final_audio, music])
        
        final_clip = final_clip.set_audio(final_audio)
        
        output_file = f"mystery_video_{int(time.time())}.mp4"
        final_clip.write_videofile(
            output_file,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            threads=4,
            preset='fast'
        )
        
        # Clean up
        for i in range(len(segments)):
            if os.path.exists(f"temp_speech_{i}.mp3"):
                os.remove(f"temp_speech_{i}.mp3")
        if os.path.exists("temp_bg.jpg"):
            os.remove("temp_bg.jpg")
        
        return output_file
    
    except Exception as e:
        print(f"Error generating video: {e}")
        return None

def video_to_base64(video_path):
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode('utf-8')

def handler(event, context):
    try:
        body = json.loads(event['body'])
        story_type = body.get('story_type', 'random')
        duration = int(body.get('duration', 60))
        voice_speed = float(body.get('voice_speed', 1.0))
        
        video_path = generate_video(story_type, duration, voice_speed)
        
        if video_path:
            video_data = video_to_base64(video_path)
            os.remove(video_path)
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'video/mp4',
                    'Content-Disposition': f'attachment; filename="{video_path}"'
                },
                'body': video_data,
                'isBase64Encoded': True
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Failed to generate video'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

if __name__ == "__main__":
    # For local testing
    video_path = generate_video()
    if video_path:
        print(f"Video generated: {video_path}")
        # In production, this would be handled by Netlify Functions
    else:
        print("Failed to generate video")