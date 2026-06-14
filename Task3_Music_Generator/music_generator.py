import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import random
import os
import subprocess
import sys

try:
    from midiutil import MIDIFile
except ImportError:
    print("midiutil not found. Install it with: pip install midiutil")
    sys.exit(1)

# =========================
# Constants
# =========================

GENRE_CONFIG = {
    "Classical": {
        "notes": [
            60, 62, 64, 65, 67, 69, 71, 72,   # C major scale (oct 4-5)
            48, 50, 52, 53, 55, 57, 59,         # C major scale (oct 3)
            72, 74, 76, 77, 79,                  # C major scale (oct 5+)
        ],
        "chords": [
            [48, 52, 55],  # C major
            [45, 48, 52],  # A minor
            [53, 57, 60],  # F major
            [55, 59, 62],  # G major
        ],
        "tempos": [80, 100, 120],
        "durations": [0.5, 1.0, 1.5, 2.0],
    },
    "Jazz": {
        "notes": [
            60, 63, 65, 67, 70, 72,             # C minor pentatonic + b7
            58, 60, 63, 65, 67,                  # lower range
            72, 75, 77, 79,                      # upper range
        ],
        "chords": [
            [48, 52, 55, 58],  # Cmaj7
            [50, 53, 57, 60],  # Dm7
            [55, 58, 62, 65],  # G7
            [53, 57, 60, 64],  # Fmaj7
        ],
        "tempos": [100, 120, 140],
        "durations": [0.25, 0.5, 0.75, 1.0],
    },
    "Pop": {
        "notes": [
            60, 64, 67, 72,                     # C major triad + octave
            62, 65, 69,                          # fillers
            55, 57, 60, 62, 64,                  # lower
        ],
        "chords": [
            [48, 52, 55],  # C major
            [53, 57, 60],  # F major
            [57, 60, 64],  # A minor
            [55, 59, 62],  # G major
        ],
        "tempos": [100, 110, 120, 130],
        "durations": [0.5, 1.0, 1.0, 1.0, 2.0],  # weighted toward quarter notes
    },
    "Piano": {
        "notes": [
            60, 62, 64, 67, 69, 72,
            52, 55, 57, 60,
            72, 74, 76, 79,
        ],
        "chords": [
            [48, 52, 55, 60],  # C major (wide)
            [45, 48, 52, 57],  # A minor (wide)
            [50, 53, 57, 62],  # D minor (wide)
            [55, 59, 62, 67],  # G major (wide)
        ],
        "tempos": [70, 90, 100],
        "durations": [0.5, 1.0, 1.5, 2.0],
    },
    "Blues": {
        "notes": [
            60, 63, 65, 66, 67, 70, 72,          # C blues scale
            48, 51, 53, 54, 55, 58,               # lower oct
            72, 75, 77, 78, 79,                   # upper
        ],
        "chords": [
            [48, 52, 55, 58],  # C7
            [53, 57, 60, 63],  # F7
            [55, 59, 62, 65],  # G7
        ],
        "tempos": [80, 100, 120],
        "durations": [0.25, 0.5, 0.75, 1.0, 1.5],
    },
    "Lo-fi": {
        "notes": [
            60, 62, 63, 65, 67, 70, 72,          # C minor scale
            48, 50, 51, 53, 55,
            72, 74, 75, 77,
        ],
        "chords": [
            [48, 51, 55, 58],  # Cm7
            [53, 56, 60, 63],  # Fm7
            [43, 46, 50, 53],  # Gm7
            [46, 50, 53, 56],  # Bbmaj7
        ],
        "tempos": [70, 80, 85],
        "durations": [0.5, 1.0, 1.5, 2.0, 3.0],
    },
    "Rock": {
        "notes": [
            60, 63, 65, 67, 70, 72,              # pentatonic minor
            48, 51, 53, 55, 58, 60,
            72, 75, 77, 79,
        ],
        "chords": [
            [48, 55, 60],     # power chord C5
            [53, 60, 65],     # power chord F5
            [55, 62, 67],     # power chord G5
            [45, 52, 57],     # power chord Am
        ],
        "tempos": [120, 140, 160],
        "durations": [0.25, 0.5, 0.5, 1.0],
    },
}

BG_COLOR = "#1e1e2f"
ACCENT = "#7c6ef5"
TEXT_COLOR = "white"
SUBTEXT = "#aaaaaa"
SUCCESS = "#9eff9e"
CARD_BG = "#2a2a3f"


# =========================
# Melody Generation Logic
# =========================

def build_motif(notes, length=4):
    """Generate a short repeating melodic motif."""
    return [random.choice(notes) for _ in range(length)]


def generate_melody_track(midi, track, channel, notes, durations, num_bars=8):
    """Generate a melody with motif repetition and variation."""
    time = 0.0
    motif = build_motif(notes, length=4)
    beats_per_bar = 4.0
    total_beats = num_bars * beats_per_bar

    while time < total_beats:
        # Occasionally vary the motif
        if random.random() < 0.3:
            motif = build_motif(notes, length=4)

        for pitch in motif:
            if time >= total_beats:
                break
            # Occasional octave shift for dynamics
            if random.random() < 0.15:
                pitch = pitch + 12 if pitch < 60 else pitch - 12

            duration = random.choice(durations)
            velocity = random.randint(70, 110)
            midi.addNote(track, channel, pitch, time, duration, velocity)
            time += duration

    return time


def generate_chord_track(midi, track, channel, chords, num_bars=8):
    """Generate a chord accompaniment track."""
    time = 0.0
    beats_per_bar = 4.0
    total_beats = num_bars * beats_per_bar

    while time < total_beats:
        chord = random.choice(chords)
        # Arpeggiate or block chord
        if random.random() < 0.4:
            # Arpeggiate
            for note in chord:
                if time >= total_beats:
                    break
                midi.addNote(track, channel, note, time, 0.25, 60)
                time += 0.25
        else:
            # Block chord for 1 or 2 beats
            dur = random.choice([1.0, 2.0])
            for note in chord:
                midi.addNote(track, channel, note, time, dur, 55)
            time += dur


def generate_music():
    genre = genre_var.get()
    if not genre:
        messagebox.showwarning("Select a genre", "Please choose a genre before generating.")
        return

    tempo = tempo_var.get()
    num_bars = bars_var.get()
    include_chords = chord_var.get()
    save_path = save_path_var.get()

    if not save_path:
        messagebox.showwarning("No save location", "Please choose where to save the file.")
        return

    config = GENRE_CONFIG[genre]
    notes = config["notes"]
    chords = config["chords"]
    durations = config["durations"]

    num_tracks = 2 if include_chords else 1
    midi = MIDIFile(num_tracks)

    # Melody track
    midi.addTrackName(0, 0, f"{genre} Melody")
    midi.addTempo(0, 0, tempo)
    generate_melody_track(midi, 0, 0, notes, durations, num_bars)

    # Chord track
    if include_chords:
        midi.addTrackName(1, 0, f"{genre} Chords")
        midi.addTempo(1, 0, tempo)
        generate_chord_track(midi, 1, 1, chords, num_bars)

    filename = os.path.join(save_path, f"{genre}_music.mid")
    with open(filename, "wb") as f:
        midi.writeFile(f)

    result_label.config(text=f"Saved: {filename}")
    status_var.set(f"✔ {genre} melody generated — {num_bars} bars @ {tempo} BPM")

    answer = messagebox.askyesno(
        "Done!",
        f"{os.path.basename(filename)} created.\n\nOpen it now?"
    )
    if answer:
        open_file(filename)


# =========================
# File Helpers
# =========================

def open_file(path):
    """Open MIDI file with system default player."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Could not open file", str(e))


def choose_save_path():
    path = filedialog.askdirectory(title="Choose save folder")
    if path:
        save_path_var.set(path)
        path_label.config(text=path)


# =========================
# GUI
# =========================

root = tk.Tk()
root.title("AI Music Generator")
root.geometry("620x580")
root.configure(bg=BG_COLOR)
root.resizable(False, False)

# --- Title ---
tk.Label(
    root, text="🎵 AI Music Generator",
    font=("Segoe UI", 22, "bold"),
    bg=BG_COLOR, fg=ACCENT
).pack(pady=(24, 2))

tk.Label(
    root, text="CodeAlpha Artificial Intelligence Internship",
    bg=BG_COLOR, fg=SUBTEXT, font=("Segoe UI", 9)
).pack()

# --- Separator ---
ttk.Separator(root, orient="horizontal").pack(fill="x", padx=30, pady=18)

# --- Main Card Frame ---
card = tk.Frame(root, bg=CARD_BG, bd=0, relief="flat")
card.pack(padx=30, fill="x")

def card_row(parent, label_text, widget_fn):
    row = tk.Frame(parent, bg=CARD_BG)
    row.pack(fill="x", padx=20, pady=8)
    tk.Label(
        row, text=label_text,
        bg=CARD_BG, fg=TEXT_COLOR,
        font=("Segoe UI", 10, "bold"),
        width=18, anchor="w"
    ).pack(side="left")
    widget_fn(row)

# Genre
genre_var = tk.StringVar()
def make_genre(parent):
    cb = ttk.Combobox(
        parent, textvariable=genre_var, state="readonly",
        width=22, values=list(GENRE_CONFIG.keys())
    )
    cb.pack(side="left")
card_row(card, "Genre", make_genre)

# Tempo
tempo_var = tk.IntVar(value=120)
def make_tempo(parent):
    frm = tk.Frame(parent, bg=CARD_BG)
    frm.pack(side="left")
    slider = tk.Scale(
        frm, from_=60, to=200, orient="horizontal",
        variable=tempo_var, bg=CARD_BG, fg=TEXT_COLOR,
        troughcolor=ACCENT, highlightthickness=0,
        activebackground=ACCENT, length=180, showvalue=True
    )
    slider.pack()
card_row(card, "Tempo (BPM)", make_tempo)

# Bars
bars_var = tk.IntVar(value=8)
def make_bars(parent):
    frm = tk.Frame(parent, bg=CARD_BG)
    frm.pack(side="left")
    for val, lbl in [(4, "4"), (8, "8"), (16, "16"), (32, "32")]:
        tk.Radiobutton(
            frm, text=lbl, variable=bars_var, value=val,
            bg=CARD_BG, fg=TEXT_COLOR, selectcolor=ACCENT,
            activebackground=CARD_BG, font=("Segoe UI", 10)
        ).pack(side="left", padx=6)
card_row(card, "Bars", make_bars)

# Chords toggle
chord_var = tk.BooleanVar(value=True)
def make_chords(parent):
    tk.Checkbutton(
        parent, text="Include chord accompaniment",
        variable=chord_var,
        bg=CARD_BG, fg=TEXT_COLOR, selectcolor=ACCENT,
        activebackground=CARD_BG, font=("Segoe UI", 10)
    ).pack(side="left")
card_row(card, "Chords", make_chords)

# Save path
save_path_var = tk.StringVar(value=os.path.expanduser("~"))
def make_path(parent):
    global path_label
    btn = tk.Button(
        parent, text="Browse…",
        command=choose_save_path,
        bg=ACCENT, fg="white",
        font=("Segoe UI", 9),
        padx=8, pady=2, relief="flat"
    )
    btn.pack(side="left")
    path_label = tk.Label(
        parent, text=save_path_var.get(),
        bg=CARD_BG, fg=SUBTEXT,
        font=("Segoe UI", 9),
        wraplength=300, justify="left"
    )
    path_label.pack(side="left", padx=10)
card_row(card, "Save to", make_path)

# --- Generate Button ---
tk.Button(
    root, text="Generate Music ▶",
    command=generate_music,
    bg=ACCENT, fg="white",
    font=("Segoe UI", 13, "bold"),
    padx=30, pady=10, relief="flat",
    cursor="hand2"
).pack(pady=24)

# --- Result label ---
result_label = tk.Label(
    root, text="",
    bg=BG_COLOR, fg=SUCCESS,
    font=("Segoe UI", 10)
)
result_label.pack()

# --- Status bar ---
status_var = tk.StringVar(value="Ready — select a genre and hit Generate.")
tk.Label(
    root, textvariable=status_var,
    bg="#13131f", fg=SUBTEXT,
    font=("Segoe UI", 9),
    anchor="w", padx=12
).pack(side="bottom", fill="x", ipady=4)

root.mainloop()
