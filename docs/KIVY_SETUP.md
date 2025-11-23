# Kivy Setup Guide for Dynevi

This document describes the Kivy GUI setup and architecture for Dynevi.

## Overview

Dynevi uses **Kivy** as the GUI framework for the theater-of-the-mind interface. Kivy provides:
- GPU-accelerated rendering
- Cross-platform support (Windows, macOS, Linux)
- Modern, touch-friendly interface
- Excellent animation support
- Open source (MIT license)

## Architecture

### Components

1. **MainWindow** (`src/gui/main_window.py`)
   - Main application entry point
   - Manages overall UI layout
   - Coordinates video, dialog icons, and audio

2. **VideoPlayer** (`src/gui/video_player.py`)
   - Background video playback using OpenCV
   - Seamless looping support
   - Threaded frame rendering for smooth playback

3. **DialogIconManager** (`src/gui/dialog_icons.py`)
   - Manages multiple dialog icons
   - Handles animations (fade in/out, pulse)
   - Position mapping for NPCs

4. **AudioPlayer** (`src/gui/audio_player.py`)
   - TTS audio playback using pygame
   - Volume control
   - Queue management

## Running the Application

### Basic Run

```bash
# Activate virtual environment (if using uv)
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Run the application
python main.py
```

### Using uv

```bash
# Run directly with uv
uv run python main.py
```

## Configuration

### Window Settings

Window configuration is set in `src/gui/main_window.py`:

```python
Config.set('graphics', 'fullscreen', 'auto')
Config.set('graphics', 'window_state', 'maximized')
Config.set('graphics', 'borderless', '1')
```

### Video Playback

- Video file: `background/loop.mp4`
- Format: MP4 (H.264 recommended)
- Looping: Enabled by default
- FPS: Auto-detected from video file

### Dialog Icons

- Default position: Center-bottom (0.5, 0.3)
- Custom positions can be set per NPC
- Animation duration: 0.3s fade in/out
- Display duration: 3.0s (configurable)

## Development

### Kivy KV Language

Kivy uses KV language for UI definitions. The main KV file is:
- `src/gui/kv/main.kv`

### Adding New Components

1. Create widget class in `src/gui/`
2. Add KV definition if needed
3. Import and use in `MainLayout`

### Testing

```bash
# Run with verbose logging
python main.py --log-level=DEBUG
```

## Troubleshooting

### Video Not Playing

- Check video file exists: `background/loop.mp4`
- Verify video codec (H.264 recommended)
- Check OpenCV installation: `python -c "import cv2; print(cv2.__version__)"`

### Audio Not Playing

- Check pygame installation: `python -c "import pygame; pygame.mixer.init()"`
- Verify audio file format (WAV recommended)
- Check system audio settings

### Window Issues

- If fullscreen doesn't work, try: `Config.set('graphics', 'fullscreen', '0')`
- For borderless window: `Config.set('graphics', 'borderless', '1')`

## Dependencies

- `kivy>=2.2.0` - Main GUI framework
- `kivymd>=1.1.1` - Material Design components (optional)
- `opencv-python>=4.8.0` - Video playback
- `pygame>=2.5.0` - Audio playback

## Next Steps

- Integrate with Story Orchestrator
- Add input handling for player messages
- Connect TTS service to AudioPlayer
- Implement dialog text overlay
- Add settings dialog

