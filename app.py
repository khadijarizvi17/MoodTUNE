"""Mood Playlist Generator - tiny Python web app (standard library only).

Run:  python app.py        then open http://localhost:8000
"""
import json
import os
import random
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote_plus

from moods import DEFAULT_MOOD, MOODS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Look for index.html in static/ first, then next to app.py (in case the folder wasn't created)
INDEX_PATH = next(
    (p for p in (os.path.join(BASE_DIR, "static", "index.html"), os.path.join(BASE_DIR, "index.html"))
     if os.path.exists(p)),
    os.path.join(BASE_DIR, "static", "index.html"),
)


def detect_moods(text):
    """Score every mood by keyword hits. Returns [(mood_key, score), ...] best first."""
    text = " " + re.sub(r"[^\w\s']", " ", text.lower()) + " "
    scores = {}
    for key, mood in MOODS.items():
        score = 0
        for kw in mood["keywords"]:
            if " " + kw + " " in text:
                score += 2 if " " in kw else 1  # whole word / phrase
            elif len(kw) > 4 and kw in text:
                score += 1  # partial match (e.g. "relaxing" -> "relax")
        if score:
            scores[key] = score
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def song_payload(song):
    title, artist, lang = song
    q = quote_plus(f"{title} {artist}")
    return {
        "title": title,
        "artist": artist,
        "lang": lang,
        "youtube": f"https://www.youtube.com/results?search_query={q}",
        "spotify": f"https://open.spotify.com/search/{q}",
    }


def pick_songs(mood_key, language, count, exclude=()):
    pool = [s for s in MOODS[mood_key]["songs"] if language == "any" or s[2] == language]
    fresh = [s for s in pool if s[0] not in exclude]
    random.shuffle(fresh)
    return fresh[:count]


def generate(payload):
    text = (payload.get("text") or "").strip()
    forced = payload.get("mood")
    language = payload.get("language", "any")
    if language not in ("any", "en", "ur"):
        language = "any"
    try:
        count = max(4, min(int(payload.get("count", 8)), 15))
    except (TypeError, ValueError):
        count = 8

    detected = detect_moods(text) if text else []
    matched = True
    if forced in MOODS:
        primary = forced
    elif detected:
        primary = detected[0][0]
    else:
        primary, matched = DEFAULT_MOOD, False

    secondary = next((k for k, _ in detected if k != primary), None)

    # Mix: ~70% primary mood, ~30% secondary mood (if we found one)
    songs = []
    if secondary:
        n_secondary = max(1, round(count * 0.3))
        songs += pick_songs(secondary, language, n_secondary)
    songs = pick_songs(primary, language, count - len(songs), exclude={s[0] for s in songs}) + songs
    padded = False
    if len(songs) < count and language != "any":
        # Not enough songs in that language for this mood: fill from the same mood, any language
        taken = {s[0] for s in songs}
        extra = pick_songs(primary, "any", count - len(songs), exclude=taken)
        padded = bool(extra)
        songs += extra
    random.shuffle(songs)

    mood = MOODS[primary]
    total = sum(s for _, s in detected) or 1
    confidence = 100 if forced in MOODS else (
        round(100 * dict(detected).get(primary, 0) / total) if matched else 0)

    return {
        "mood": primary,
        "label": mood["label"],
        "emoji": mood["emoji"],
        "colors": mood["colors"],
        "vibe": random.choice(mood["vibes"]),
        "matched": matched,
        "padded": padded,
        "confidence": confidence,
        "secondary": (
            {"mood": secondary, "label": MOODS[secondary]["label"], "emoji": MOODS[secondary]["emoji"]}
            if secondary else None),
        "songs": [song_payload(s) for s in songs],
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{ctype}; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(INDEX_PATH, "rb") as f:
                self._send(200, f.read(), "text/html")
        elif self.path == "/api/moods":
            moods = [{"key": k, "label": m["label"], "emoji": m["emoji"], "colors": m["colors"]}
                     for k, m in MOODS.items()]
            self._send(200, json.dumps(moods))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/generate":
            return self._send(404, json.dumps({"error": "not found"}))
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send(200, json.dumps(generate(payload)))
        except (ValueError, json.JSONDecodeError):
            self._send(400, json.dumps({"error": "bad request"}))

    def log_message(self, fmt, *args):  # quieter console
        pass


def main():
    if not os.path.exists(INDEX_PATH):
        sys.exit("index.html not found. Put it in a 'static' folder next to app.py "
                 "(or directly next to app.py).")
    port = int(os.environ.get("PORT", 8000))
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://localhost:{port}"
    print(f"Mood Playlist Generator running at {url}  (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nBye!")


if __name__ == "__main__":
    main()
