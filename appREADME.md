# 🎧 Moodtune: Mood-based Playlist Generator

Type how you feel (English, Urdu or Hinglish) and get a vibe description plus a playlist of songs to search on YouTube / Spotify.

Pure Python standard library. **No pip install needed.**

## Run

```bash
python app.py
```

Then open http://localhost:8000 (it opens automatically). Use `PORT=9000 python app.py` to change the port, or `--no-browser` to skip auto-open.

## Features

- Mood detection from free text (English + Roman Urdu/Hindi keywords like *udaas*, *khush*, *ghussa*, *pyaar*)
- 10 moods: happy, sad, calm, energetic, romantic, angry, focused, nostalgic, lonely/anxious, motivated
- Blends a secondary mood when your text mixes feelings
- Language filter: All / English / Urdu-Hindi
- Adjustable playlist size, one-click shuffle for new songs
- UI theme and glow change with each mood
- YouTube and Spotify search buttons per song
- Favorites (♥), recent-mood history, copy list, download as .txt
- Responsive, keyboard friendly (Ctrl/Cmd + Enter to generate)

## Project structure

```
app.py            # Python web server + mood detection API
moods.py          # moods, keywords, vibe texts, song lists
static/index.html # the whole UI
```

## Add your own songs

Open `moods.py` and append a tuple to any mood's `songs` list:

```python
("Song Title", "Artist", "en")   # or "ur" for Urdu/Hindi
```
