from pathlib import Path

import pygame

DEFAULT_SOUNDS_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"
DEFAULT_MUSIC_DIR = Path(__file__).resolve().parent.parent / "assets" / "music"
SOUND_NAMES = ("jump", "land", "hazard", "portal", "ui")
MUSIC_NAMES = ("menu", "prologue", "game")
MIXER_FORMAT = {"frequency": 22050, "size": -16, "channels": 1, "buffer": 512}
VOLUME_STEPS = 5


class Audio:
    def __init__(
        self,
        sounds_dir: Path | None = None,
        music_dir: Path | None = None,
    ) -> None:
        self.sounds_dir = Path(sounds_dir) if sounds_dir else DEFAULT_SOUNDS_DIR
        self.music_dir = Path(music_dir) if music_dir else DEFAULT_MUSIC_DIR
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._music_name: str | None = None
        self._available = False
        self.sfx_volume = VOLUME_STEPS
        self.music_volume = VOLUME_STEPS
        self.muted = False
        self._start_mixer()
        self._load_sounds()

    def _start_mixer(self) -> None:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(**MIXER_FORMAT)
        except (pygame.error, OSError):
            return

    def _load_sounds(self) -> None:
        if pygame.mixer.get_init() is None:
            return
        for name in SOUND_NAMES:
            path = self.sounds_dir / f"{name}.wav"
            if not path.is_file():
                continue
            try:
                self._sounds[name] = pygame.mixer.Sound(str(path))
            except pygame.error:
                continue
        self._available = bool(self._sounds)
        self._apply_sfx_volume()

    def _apply_sfx_volume(self) -> None:
        level = 0.0 if self.muted else self.sfx_volume / VOLUME_STEPS
        for sound in self._sounds.values():
            try:
                sound.set_volume(level)
            except pygame.error:
                continue

    def _apply_music_volume(self) -> None:
        level = 0.0 if self.muted else self.music_volume / VOLUME_STEPS
        try:
            pygame.mixer.music.set_volume(level)
        except pygame.error:
            pass

    def play_music(self, name: str) -> None:
        if pygame.mixer.get_init() is None:
            return
        if name == self._music_name and pygame.mixer.music.get_busy():
            self._apply_music_volume()
            return
        path = self.music_dir / f"{name}.wav"
        if not path.is_file():
            return
        try:
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.play(-1)
        except pygame.error:
            return
        self._music_name = name
        self._apply_music_volume()

    def stop_music(self) -> None:
        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass
        self._music_name = None

    @property
    def current_music(self) -> str | None:
        return self._music_name

    @property
    def available(self) -> bool:
        return self._available

    @property
    def sfx_label(self) -> str:
        if self.muted:
            return "OFF"
        return f"{self.sfx_volume}/{VOLUME_STEPS}"

    @property
    def music_label(self) -> str:
        if self.muted:
            return "OFF"
        return f"{self.music_volume}/{VOLUME_STEPS}"

    @property
    def mute_label(self) -> str:
        return "ON" if self.muted else "OFF"

    def adjust_sfx(self, delta: int) -> None:
        self.sfx_volume = max(0, min(VOLUME_STEPS, self.sfx_volume + delta))
        self._apply_sfx_volume()

    def adjust_music(self, delta: int) -> None:
        self.music_volume = max(0, min(VOLUME_STEPS, self.music_volume + delta))
        self._apply_music_volume()

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        self._apply_sfx_volume()
        self._apply_music_volume()

    def play(self, name: str) -> None:
        if not self._available or self.muted or self.sfx_volume == 0:
            return
        sound = self._sounds.get(name)
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            pass
