from PIL import Image
import requests
import subprocess
import re
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from io import BytesIO
import eyed3
from eyed3.id3.frames import ImageFrame
from mutagen.id3 import ID3, COMM
import os
import sys
#funcs
#titles = get('title', channel_url).split('\n')[:-1]

folder = 'ChiCity1Entertainment'

def get_path(string, format):
    return f'/Users/jimmywootton/Music/{folder}/{string}{format}'

check_paths = [get_path('raw', '.mp3'),
                get_path('raw', '.webm'),
                get_path('raw', '.webm.part'),
                get_path('raw', '.m4a.part')]

raw_path = check_paths[0]

def get_song(url): 
    return (
        f'yt-dlp --extract-audio --audio-format mp3 --output '
        f'"/Users/jimmywootton/Music/{folder}/raw.%(ext)s" ' 
        f'"{url}"'
    )

def get(string, url):
    command = f'yt-dlp --flat-playlist --print {string} "{url}"'
    return subprocess.run(command , shell = True, text = True, capture_output = True).stdout

def get_song(url): 
    return (
        f'yt-dlp --extract-audio --audio-format mp3 --output '
        f'"{raw_path[:-4]}.%(ext)s" ' 
        f'"{url}"'
    )

def crop(thumbnail):
    width, height = thumbnail.size
    side_length = min(width, height) - 60
    left = (width - side_length) / 2
    right = (width + side_length) / 2
    top = (height - side_length)/ 2
    bottom = (height + side_length)/2
    return thumbnail.crop((left, top, right, bottom))

def remove_extra_spaces(string):
    return re.sub(r'\s+', ' ', string).strip()
     
def remove_parentheses_content(string):
    string_without_closed_parentheses = re.sub(r'\(.*\)', '', string)
    return string_without_closed_parentheses.split('(')[0].strip()

def get_artist_and_title_raw(string):
    if ' - ' in string:
        parse_substr = ' - '
    elif '- ' in string:
        parse_substr = '- '
    elif ' -' in string:
        parse_substr = ' -'
    else:
        return [string]
    return string.split(parse_substr)

def get_artist_and_title_from_name(string):
    string = remove_extra_spaces(string.replace('/', '\\').replace('‎', '').replace('–', '-'))
    get_artist_and_title_raw_array = get_artist_and_title_raw(string)
    if len(get_artist_and_title_raw_array) > 1:
        artist_raw = get_artist_and_title_raw_array[0]
        artist = remove_extra_spaces(artist_raw)
        title_raw = get_artist_and_title_raw_array[1]
    else:
        artist = ''
        title_raw = get_artist_and_title_raw_array[0]
    title_raw_no_parentheses = remove_parentheses_content(title_raw)
    title = remove_extra_spaces(title_raw_no_parentheses)
    return [artist, title]

def get_artist_and_album(description_raw, artist_from_name, title):
    description_array = description_raw.split("\n")
    description_types = [item.split(":",1)[0].lower() for item in description_array]
    description_features = [item.split(":",1)[-1] for item in description_array]
    if 'artist' in description_types:
        artist = remove_extra_spaces(description_features[description_types.index('artist')])
    else:
        artist = artist_from_name
    if 'album' in description_types:
        album = remove_extra_spaces(description_features[description_types.index('album')])
    else:
        album = title
    return [artist, album]

def embed_thumbnail(thumbnail_raw, new_path):
    thumbnail = crop(Image.open(BytesIO(requests.get(thumbnail_raw.strip()).content)))
    audiofile = eyed3.load(new_path)
    img_byte_arr = BytesIO()
    thumbnail.save(img_byte_arr, format='JPEG')  # Ensure it's saved as a valid image format
    img_byte_arr = img_byte_arr.getvalue()  # Get the raw bytes from the BytesIO buffer
    audiofile.tag.images.set(ImageFrame.FRONT_COVER, img_byte_arr, 'image/jpeg')
    audiofile.tag.save()

def embed_metadata(title, artist, album, new_path):
    audio = MP3(new_path , ID3 = EasyID3)
    audio['title'] = title
    audio['artist'] = artist
    audio['album'] = album
    audio.save()

def add_key(new_path, url):
    try:
        if not os.path.exists(new_path):
            raise Exception
        audio = ID3(new_path)
        audio.add(COMM(encoding = 3, lang = "eng", desc = "", text = url))
        audio.save()
    except Exception:
        sys.exit('Add key to nonexistent file path')

def get_key(new_path):
    try:
        if not os.path.exists(new_path):
            raise Exception
        audio = ID3(new_path)
        return audio.getall("COMM")[0].text[0]
    except IndexError:
        return None
    except Exception:
        return None
    
def driver(url):
    [os.remove(pathway) for pathway in check_paths if os.path.exists(pathway)]
    title_raw = get('title',  url)
    if title_raw:
        duration = get('duration',  url)
        if 60 < int(duration) < 420:
            j = 2            
            artist_and_title_from_name_array = get_artist_and_title_from_name(title_raw)
            title = artist_and_title_from_name_array[1]
            numbered_title = title + ' 1'
            modified_title = title
            new_path = get_path(f'{title}', '.mp3')
            while get_key(new_path) != url:
                if os.path.exists(new_path):
                    modified_title = numbered_title[:-2] + ' ' + str(j)
                    new_path = get_path(f'{modified_title}', '.mp3')
                    j += 1
                else:
                    exit = os.system(get_song(url))
                    if exit != 0:
                        raise Exception
                    add_key(raw_path, url)
                    os.rename(raw_path, new_path)
            artist_from_name = artist_and_title_from_name_array[0]
            description_raw = get('description',  url)
            artist_and_album_array = get_artist_and_album(description_raw, artist_from_name, title)
            artist = artist_and_album_array[0]
            album = artist_and_album_array[1]
            embed_metadata(title, artist, album, new_path)
            thumbnail_raw = get('thumbnail',  url)
            embed_thumbnail(thumbnail_raw, new_path)



