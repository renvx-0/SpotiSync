import sys
sys.stdout.reconfigure(encoding="utf-8")

import asyncio
import os
import traceback
from datetime import datetime, timezone
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
)
import random
from itertools import cycle
from enum import Enum
from pathlib import Path
import base64
from winsdk.windows.storage.streams import DataReader

script_dir = Path(__file__).resolve().parent

import lyrics_api

from dotenv import load_dotenv
load_dotenv()

class EmojiMode(Enum):
    FIRST_LETTER = "first_letter"
    FACE = "face"
    MUSIC = "music"
    SPINNING_ARROWS = "spinning_arrows"
    SPINNING_SYMBOLS = "spinning_symbols"
    CLOCKS = "clocks"

DECORATOR_LABELS = {
    "First letter": EmojiMode.FIRST_LETTER,
    "Face emojis": EmojiMode.FACE,
    "Music emojis": EmojiMode.MUSIC,
    "Cycling arrows": EmojiMode.SPINNING_ARROWS,
    "Loading symbols": EmojiMode.SPINNING_SYMBOLS,
    "Cronologic cycling clocks": EmojiMode.CLOCKS,
}

def parse_mode(value):
    if value in EmojiMode.__members__:
        return EmojiMode[value]
    return DECORATOR_LABELS.get(value)

# ---------------------

CENSOR_WORDS = False
CENSOR_LANGUAGES = ["es", "en", "ru"]
CENSOR_LOGS_FILE = script_dir / "censor_lists" / "censor_logs.log"
CENSOR_LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)

ADD_EMOJIS = False
EMOJI_MODE = EmojiMode.CLOCKS

SYNC_TO_DISCORD = False

# ---------------------

cycle_emojis = {
    "arrows": cycle(["⬆️", "➡️", "⬇️", "⬅️"]),
    "symbols": cycle(["|", "/", "—", "\\"]),
    "clocks": cycle([
        "🕐", "🕜", "🕑", "🕝", "🕒", "🕞", "🕓", "🕟", "🕔", "🕠", "🕕", "🕡",
        "🕖", "🕢", "🕗", "🕣", "🕘", "🕤", "🕙", "🕥", "🕚", "🕦", "🕛", "🕧"
    ])
}

def read_word_list(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

from badwords import ProfanityFilter
pf = ProfanityFilter()
pf.init(CENSOR_LANGUAGES)
censor_status = None
loaded_langs = None

censor_dir = script_dir / "censor_lists"
censor_dir.mkdir(parents=True, exist_ok=True)

(censor_dir / "blacklist.txt").touch(exist_ok=True)
(censor_dir / "whitelist.txt").touch(exist_ok=True)

_blacklist = read_word_list(script_dir / "censor_lists" / "blacklist.txt")
_whitelist = read_word_list(script_dir / "censor_lists" / "whitelist.txt")
if _blacklist:
    pf.add_words(_blacklist)
if _whitelist:
    pf.add_whitelist(_whitelist)

discord = lyrics_api.Discord("")


def apply_censor_languages(langs):
    """CAMBIO: carga los idiomas de uno en uno para que un código no soportado no tumbe al resto."""
    try:
        pf.unload_languages(pf.loaded_languages())
    except Exception:
        traceback.print_exc()
    for lang in langs:
        try:
            pf.load_languages([lang])
        except Exception as e:
            print(f"Idioma no soportado por badwords: {lang} ({e})", flush=True)


async def get_thumbnail_url(info):
    if info.thumbnail is None:
        return None

    try:
        stream = await info.thumbnail.open_read_async()

        reader = DataReader(stream.get_input_stream_at(0))

        await reader.load_async(stream.size)

        data = bytearray(stream.size)
        reader.read_bytes(data)

        reader.close()
        stream.close()

        return f"data:image/jpeg;base64,{base64.b64encode(data).decode()}"

    except OSError:
        return None

last_song = None
synced_lyrics = {}
raw_lyrics = {}
last_line_idx = None
_logged_censor = set()
_thumb_cache = {"key": None, "value": None}

async def get_spotify_playback():
    sessions = await MediaManager.request_async()

    current_session = sessions.get_current_session()
    if current_session is None:
        return None

    if current_session.source_app_user_model_id != "Spotify.exe":
        for session in sessions.get_sessions():
            if session.source_app_user_model_id == "Spotify.exe":
                current_session = session
                break
        else:
            return None

    info = await current_session.try_get_media_properties_async()
    timeline = current_session.get_timeline_properties()
    playback_info = current_session.get_playback_info()
    is_playing = playback_info.playback_status.value == 4

    position = timeline.position.total_seconds()

    if is_playing:
        now = datetime.now(timezone.utc)
        elapsed = (now - timeline.last_updated_time).total_seconds()
        position += elapsed

    thumb_key = (info.title, info.artist, info.album_title)
    if _thumb_cache["key"] == thumb_key and _thumb_cache["value"]:
        thumbnail = _thumb_cache["value"]
    else:
        thumbnail = await get_thumbnail_url(info)
        if thumbnail:
            _thumb_cache["key"], _thumb_cache["value"] = thumb_key, thumbnail

    return {
        "name": info.title,
        "artist": info.artist,
        "album": info.album_title,
        "thumbnail": thumbnail,
        "position": position,
        "duration": timeline.end_time.total_seconds(),
        "is_playing": is_playing,
    }

def fmt(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"

def time_to_seconds(time: str):
    splitted = time.split(":")

    total_secs = 0

    for i in range(len(splitted)):
        num = splitted[-(i+1)]
        mult = 60 ** i
        total_secs += float(num) * mult

    return total_secs

def parse_lrc(lines):
    raw = {}
    for line in lines:
        try:
            stamp, text = line.split("]", 1)
            t = time_to_seconds(stamp.replace("[", "").strip())
        except ValueError:
            continue
        raw[t] = text.strip().rstrip(",.")
    return raw

def build_synced(raw, censor_on):
    result = {}
    for t in sorted(raw):
        text = raw[t]
        if censor_on and text:
            try:
                if pf.find(text):
                    censored = pf.censor(text)
                    if text not in _logged_censor:
                        _logged_censor.add(text)
                        with open(CENSOR_LOGS_FILE, "a", encoding="utf-8") as f:
                            f.write(f"{censored}\n    ->    {text}\n")
                    result[t] = censored
                    continue
            except Exception:
                traceback.print_exc()
        result[t] = text
    return result

from bisect import bisect_right

def get_current_line(secs, sorted_times=None):
    if sorted_times is None:
        sorted_times = sorted(synced_lyrics.keys())
    
    idx = bisect_right(sorted_times, secs) - 1
    if idx < 0:
        return None, None
    
    return idx, synced_lyrics[sorted_times[idx]]

resolved_artists = None
resolved_song_key = None

async def run_main(cfg, token):
    global last_song, synced_lyrics, raw_lyrics, last_line_idx, resolved_artists, resolved_song_key, CENSOR_WORDS, CENSOR_LANGUAGES, SYNC_TO_DISCORD, ADD_EMOJIS, EMOJI_MODE, censor_status, loaded_langs

    CENSOR_WORDS = bool(cfg["censor"].get("enabled"))
    CENSOR_LANGUAGES = list(cfg["censor"].get("languages") or [])

    censor_key = (CENSOR_WORDS, tuple(CENSOR_LANGUAGES))
    if censor_key != censor_status:
        censor_status = censor_key

        if CENSOR_WORDS and tuple(CENSOR_LANGUAGES) != loaded_langs:
            await asyncio.to_thread(apply_censor_languages, CENSOR_LANGUAGES)
            loaded_langs = tuple(CENSOR_LANGUAGES)

        if raw_lyrics:
            synced_lyrics = await asyncio.to_thread(build_synced, raw_lyrics, CENSOR_WORDS)
            last_line_idx = None

    ADD_EMOJIS = cfg["decorators"]["enabled"] and parse_mode(cfg["decorators"].get("value")) is not None
    EMOJI_MODE = parse_mode(cfg["decorators"].get("value"))
    SYNC_TO_DISCORD = cfg["discord"]["enabled"]

    discord.change_token(token)

    data = await get_spotify_playback()
    song_key = (
        data.get("name"),
        data.get("album"),
    )

    if data and song_key == resolved_song_key and resolved_artists:
        data["artist"] = resolved_artists

    if (last_song and data) and (last_song.get("name") != data.get("name")) or (not last_song and data):
        discord.change_status("")
        print("<-- Song changed -->")

        print(f"""
------------
Track: {data.get("name")}
Artist: {data.get("artist")}
------------
        """)

        synced_lyrics = {}
        raw_lyrics = {}
        last_line_idx = None
        _logged_censor.clear()

        try:
            song_details = await asyncio.to_thread(
                lyrics_api.search_song_lyrics,
                data.get("name"),
                data.get("artist"),
                data.get("album"),
                data.get("duration")
            )

            if song_details and song_details.get("lyrics"):
                if song_details.get("artists"):
                    data["artist"] = song_details["artists"]

                resolved_artists = song_details["artists"]
                resolved_song_key = (
                    data.get("name"),
                    data.get("album"),
                )

                raw_lyrics = parse_lrc(song_details["lyrics"])
                synced_lyrics = await asyncio.to_thread(
                    build_synced,
                    raw_lyrics,
                    CENSOR_WORDS
                )
        except Exception:
            traceback.print_exc()

    elif not data:
        print("<-- No song playing -->")

    line_idx = None

    if data and data.get("is_playing") and synced_lyrics:
        playback_pos = data.get("position")
        line_idx, current_line = get_current_line(playback_pos)

        if last_line_idx != line_idx and current_line is not None:
            last_line_idx = line_idx
            print(f"[{fmt(playback_pos)}] {current_line}")

            if SYNC_TO_DISCORD:
                text_prefix = ""
                emoji_icon = None

                if ADD_EMOJIS:
                    if EMOJI_MODE == EmojiMode.FIRST_LETTER:
                        pos = next((i for i, ch in enumerate(current_line) if ch.isalnum()), None)

                        if pos is not None:
                            ch = current_line[pos]
                            if ch.isascii() and ch.isdigit():
                                emoji_icon = f"{ch}\uFE0F\u20E3"
                            elif ch.isascii() and ch.isalpha():
                                emoji_icon = chr(0x1F1E6 + ord(ch.upper()) - ord("A"))

                            if emoji_icon:
                                current_line = current_line[:pos] + current_line[pos + 1:]
                    elif EMOJI_MODE == EmojiMode.FACE:
                        faces = [
                            "😀", "😃", "😄", "😁", "😆",
                            "😅", "😂", "🤣", "😊", "😇",
                            "🙂", "🙃", "😉", "😌", "😍",
                            "🥰", "😘", "😗", "😙", "😚",
                            "😋", "😛", "😝", "😜", "🤪",
                            "🤨", "🧐", "🤓", "😎", "🥳",
                            "😏", "😒", "🙄", "😬", "🤭",
                            "🤫", "🤔", "😐", "😑", "😶",
                            "🙃", "😴", "🤗", "🤩", "😢",
                            "😭", "😤", "😡", "🤬", "😱"
                        ]
                        emoji_icon = random.choice(faces)

                    elif EMOJI_MODE == EmojiMode.MUSIC:
                        music_emojis = ["🎵", "🎶", "🎼", "🎙️", "🎧", "🎤", "💿"]
                        emoji_icon = random.choice(music_emojis)

                    elif EMOJI_MODE == EmojiMode.SPINNING_ARROWS:
                        emoji_icon = next(cycle_emojis["arrows"])
                    elif EMOJI_MODE == EmojiMode.SPINNING_SYMBOLS:
                        text_prefix = next(cycle_emojis["symbols"])
                    elif EMOJI_MODE == EmojiMode.CLOCKS:
                        emoji_icon = next(cycle_emojis["clocks"])

                discord.change_status(f"{text_prefix} {current_line}".strip(), emoji_icon)

    last_song = data
    return data, synced_lyrics, line_idx

if __name__ == "__main__":
    test_cfg = {
        "censor":     {"enabled": False, "all": False, "languages": []},
        "decorators": {"enabled": False, "value": None},
        "discord":    {"enabled": False},
    }

    async def _loop():
        while True:
            await run_main(test_cfg, None)
            await asyncio.sleep(1)

    asyncio.run(_loop())