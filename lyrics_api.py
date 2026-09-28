import requests

def search_song_lyrics(song_name, song_artist, song_album, song_duration):
    r = requests.get(f"https://lrclib.net/api/get?artist_name={song_artist}&track_name={song_name}&album={song_album}&duration={song_duration}")
    data = r.json()

    if data.get("syncedLyrics"):
        return data.get("syncedLyrics").split("\n")

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