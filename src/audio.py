from pathlib import Path

import pygame

DEFAULT_SOUNDS_DIR = Path(__file__).resolve().parent.parent / "assets" / "sounds"
SOUND_NAMES = ("jump", "land", "hazard", "portal", "ui")
MIXER_FORMAT = {"frequency": 22050, "size": -16, "channels": 1, "buffer": 512}


class Audio:
    def __init__(self, sounds_dir: Path | None = None) -> None:
        self.sounds_dir = Path(sounds_dir) if sounds_dir else DEFAULT_SOUNDS_DIR
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._available = False
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

    @property
    def available(self) -> bool:
        return self._available

    def play(self, name: str) -> None:
        if not self._available:
            return
        sound = self._sounds.get(name)
        if sound is None:
            return
        try:
            sound.play()
        except pygame.error:
            pass
