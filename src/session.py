from src.chamber import Chamber
from src.hazards import FallingHazard, next_interval, next_speed, spawn_x
from src.player import Player
from src.settings import (
    DRAIN_RATE,
    HAZARD_PENALTY,
    JUMP_COST,
    MAX_DT,
    SPAWN_INTERVAL_MAX,
    START_EARTH_YEARS,
    STEP_COST,
)


class Session:
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
        self.player = Player(*chamber.spawn_point)
        self.falling: list[FallingHazard] = []
        self.earth_alloc = START_EARTH_YEARS
        self.elapsed = 0.0
        self.best_time = 0.0
        self.best_saved = 0.0
        self.game_over = False
        self.won = False
        self.spawn_timer = SPAWN_INTERVAL_MAX

    def reset(self) -> None:
        self.player = Player(*self.chamber.spawn_point)
        self.falling.clear()
        self.earth_alloc = START_EARTH_YEARS
        self.elapsed = 0.0
        self.game_over = False
        self.won = False
        self.spawn_timer = SPAWN_INTERVAL_MAX

    def press_jump(self) -> bool:
        if not self.player.on_ground:
            return False
        self.player.jump()
        self.earth_alloc -= JUMP_COST
        if self.earth_alloc <= 0:
            self.earth_alloc = 0
            self.game_over = True
        return True

    def press_step(self) -> None:
        self.earth_alloc -= STEP_COST

    def _pop_struck_hazard(self) -> bool:
        for i, hz in enumerate(self.falling):
            if self.player.rect.colliderect(hz.rect):
                del self.falling[i]
                return True
        return False

    def step(self, dt: float, keys) -> None:
        dt = min(dt, MAX_DT)
        if self.game_over or self.won:
            return

        self.elapsed += dt
        self.earth_alloc = max(0.0, self.earth_alloc - DRAIN_RATE * dt)
        if self.earth_alloc <= 0.0:
            self.game_over = True

        self.player.handle_input(keys)
        self.player.update(dt, self.chamber.platforms)

        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            self.spawn_timer = next_interval(self.elapsed)
            self.falling.append(
                FallingHazard(spawn_x(self.player.rect.x), next_speed(self.elapsed))
            )
        for hz in self.falling:
            hz.update(dt)
        self.falling = [hz for hz in self.falling if not hz.is_spent()]

        if self.chamber.hits_hazard(self.player.rect) or self._pop_struck_hazard():
            self.earth_alloc -= HAZARD_PENALTY
            self.player = Player(*self.chamber.spawn_point)
            if self.earth_alloc <= 0:
                self.earth_alloc = 0
                self.game_over = True

        if self.chamber.reached_target(self.player.rect):
            self.won = True
            self.best_saved = max(self.best_saved, self.earth_alloc)
            if self.best_time == 0.0 or self.elapsed < self.best_time:
                self.best_time = self.elapsed
