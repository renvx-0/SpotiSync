import sys
sys.stdout.reconfigure(encoding="utf-8")

import asyncio
import os
from datetime import datetime, timezone
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
)
import random
from itertools import cycle
from enum import Enum
from pathlib import Path

script_dir = Path(__file__).resolve().parent

import lyrics_api

from dotenv import load_dotenv
load_dotenv()

class EmojiMode(Enum):
    FIRST_LETTER = "first_letter"
    FACE = "face"
    MUSIC = "music"
    SPINNING_ARROWS = "spinning_arrows"
    SPINNING_SYMBOLS = "spinning_symbols",
    CLOCKS = "clocks"

# ---------------------

CENSOR_WORDS = True
CENSOR_LANGUAGES = ["es", "en", "ru"]
CENSOR_LOGS_FILE = script_dir / "censor_lists" / "censor_logs.txt"

ADD_EMOJIS = True # Add emojis / symbols to the status
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

if CENSOR_WORDS:
    from badwords import ProfanityFilter
    pf = ProfanityFilter()
    pf.init(CENSOR_LANGUAGES)
    pf.add_words([line for line in open(script_dir / "censor_lists" / "blacklist.txt", "r").readlines() if line.strip() != ""])
    pf.add_whitelist([line for line in open(script_dir / "censor_lists" / "whitelist.txt", "r").readlines() if line.strip() != ""])

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
discord = lyrics_api.Discord(DISCORD_TOKEN)

last_song = None
synced_lyrics = {}
last_line_idx = None

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

    return {
        "name": info.title,
        "artist": info.artist,
        "album": info.album_title,
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
        mult = max(1, (i) * 60)
        total_secs += float(num) * mult

    return total_secs

from bisect import bisect_right

def get_current_line(secs, sorted_times=None):
    if sorted_times is None:
        sorted_times = sorted(synced_lyrics.keys())
    
    idx = bisect_right(sorted_times, secs) - 1
    if idx < 0:
        return None, None
    
    return idx, synced_lyrics[sorted_times[idx]]

async def main():
    while True:
        global last_song, synced_lyrics, last_line_idx
        data = await get_spotify_playback()

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
            last_line_idx = None

            try:
                song_lyrics = lyrics_api.search_song_lyrics(
                    data.get("name"),
                    data.get("artist"),
                    data.get("album"),
                    data.get("duration")
                )

                if song_lyrics:
                    for line in song_lyrics:
                        separated = line.split("]", 1)

                        line_start = separated[0].replace("[", "").replace("]", "")
                        line_text: str = separated[1]
                        line_text = line_text.strip().rstrip(",.")

                        if CENSOR_WORDS:
                            matches = pf.find(line_text)

                            if matches:
                                censored_text = pf.censor(line_text)
                                synced_lyrics[time_to_seconds(line_start)] = censored_text

                                with open(CENSOR_LOGS_FILE, "a", encoding="utf-8") as f:
                                    f.write(f"{censored_text}\n    ->    {line_text}\n")

                                continue

                        synced_lyrics[time_to_seconds(line_start)] = line_text

                else:
                    print("<-- No synced lyrics found -->")
            except:
                pass

        elif not data:
            print("<-- No song playing -->")

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
                            first_char = next(
                                (char for char in current_line if char.isalnum()),
                                None
                            )

                            if first_char:
                                if first_char.isdigit():
                                    emoji_icon = f"{first_char}\uFE0F\u20E3"
                                elif first_char.isascii() and first_char.isalpha():
                                    emoji_icon = chr(0x1F1E6 + ord(first_char.upper()) - ord("A"))

                                current_line = current_line[1:]
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

                    discord.change_status(f"{text_prefix} {current_line}", emoji_icon)

        last_song = data
        await asyncio.sleep(0.25)

asyncio.run(main())