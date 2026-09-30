import requests
import time

def search_song_lyrics(song_name, song_artist, song_album, song_duration):
    params = {
        "track_name": song_name,
        "artist_name": song_artist,
    }

    if song_album:
        params["album_name"] = song_album

    try:
        attempts = 0
        max_attempts = 3
        while True:
            r = requests.get(
                "https://lrclib.net/api/search",
                params=params,
                timeout=10,
            )
            if r.ok or attempts >= max_attempts:
                results = r.json()
                break

            attempts += 1
            time.sleep(1 * attempts/2)

    except requests.RequestException as e:
        print(f"LRCLIB search error: {e}")
        return None

    if not results:
        print("<-- No LRCLIB results -->")
        return None
    
    best = None
    best_diff = float("inf")

    for result in results:
        duration = result.get("duration")

        if duration is None or song_duration is None:
            continue

        diff = abs(float(duration) - float(song_duration))

        if diff < best_diff:
            best = result
            best_diff = diff

    if best is None or best_diff > 2:
        print("<-- No matching LRCLIB track -->")
        return None

    print(
        f"FOUND: {best.get('trackName')} - "
        f"{best.get('artistName')} "
        f"({best.get('duration')}s)"
    )

    try:
        r = requests.get(
            f"https://lrclib.net/api/get/{best['id']}",
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

    except requests.RequestException as e:
        print(f"LRCLIB track error: {e}")
        return None

    if not data.get("syncedLyrics"):
        print("<-- No synced lyrics -->")
        return None

    return {
        "lyrics": (data["syncedLyrics"].split("\n") or None), 
        "artists": (data.get("artistName") or song_artist)
    }

STATUS_MAX_LEN = 128

class Discord:
    def __init__(self, token):
        self.session = requests.Session()

        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

    def change_token(self, token):
        self.headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }

    def change_status(self, text, emoji_icon=None):
        try:
            r = self.session.patch(
                "https://discord.com/api/v9/users/@me/settings",
                headers=self.headers,
                json={
                    "custom_status": {
                        "text": text[:STATUS_MAX_LEN],
                        "emoji_name": emoji_icon
                    }
                },
                timeout=10,
            )

            return r.status_code

        except Exception as e:
            print(f"[discord] error: {e}")
            return None