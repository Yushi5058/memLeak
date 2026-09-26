import pygame


class CrtOverlay:
    """Scanline and vignette overlay, built once and reused every frame.

    The result is an RGB surface meant to be blitted with BLEND_RGB_MULT, so
    white leaves the frame untouched and darker values subtract from it.
    """

    def __init__(
        self,
        width: int,
        height: int,
        scanline_stride: int = 3,
        scanline_alpha: int = 46,
        vignette_alpha: int = 96,
    ) -> None:
        self.width = int(width)
        self.height = int(height)
        self.scanline_stride = max(1, int(scanline_stride))
        self.surface = self._build(scanline_alpha, vignette_alpha)

    def _build(self, scanline_alpha: int, vignette_alpha: int) -> pygame.Surface:
        w, h = self.width, self.height
        if w < 1 or h < 1:
            return pygame.Surface((max(w, 1), max(h, 1)))

        cx, cy = (w - 1) / 2.0, (h - 1) / 2.0
        max_d2 = cx * cx + cy * cy or 1.0
        scan_gain = 1.0 - _clamp_byte(scanline_alpha) / 255.0
        vig_gain = _clamp_byte(vignette_alpha) / 255.0

        data = bytearray(w * h * 3)
        offset = 0
        for y in range(h):
            dy2 = (y - cy) * (y - cy)
            row_gain = scan_gain if y % self.scanline_stride == 0 else 1.0
            for x in range(w):
                dx = x - cx
                d2 = (dx * dx + dy2) / max_d2
                gain = (1.0 - vig_gain * d2) * row_gain
                level = max(0, min(255, int(gain * 255.0 + 0.5)))
                data[offset] = level
                data[offset + 1] = level
                data[offset + 2] = level
                offset += 3
        return pygame.image.frombuffer(bytes(data), (w, h), "RGB")

    def draw(self, target: pygame.Surface) -> None:
        target.blit(self.surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)


def _clamp_byte(value: int) -> int:
    return max(0, min(255, int(value)))
