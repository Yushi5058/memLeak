from src.chamber import Chamber
from src.hazards import FallingHazard, next_interval, next_speed, spawn_x
from src.player import Player
from src.settings import (
    JUMP_COST,
    MAX_DT,
    STEP_COST,
)

INVULN_DURATION = 1.0  # Seconds of invulnerability after taking damage


class Session:
    def __init__(self, chamber: Chamber) -> None:
        self.chamber = chamber
        self.player = Player(*chamber.spawn_point)
        self.falling: list[FallingHazard] = []
        self.events: list[str] = []
        self.earth_alloc = self.chamber.start_years
        self.hearts = 3.0
        self.invuln_timer = 0.0
        self.elapsed = 0.0
        self.best_time = 0.0
        self.best_saved = 0.0
        self.game_over = False
        self.won = False
        self.hits = 0
        self.spawn_timer = self.chamber.spawn_profile.interval_max

    def reset(self) -> None:
        self.chamber.reset()
        self.player = Player(*self.chamber.spawn_point)
        self.falling.clear()
        self.events.clear()
        self.earth_alloc = self.chamber.start_years
        self.hearts = 3.0
        self.invuln_timer = 0.0
        self.elapsed = 0.0
        self.game_over = False
        self.won = False
        self.hits = 0
        self.spawn_timer = self.chamber.spawn_profile.interval_max

    def press_jump(self) -> bool:
        if not self.player.on_ground:
            return False
        self.player.jump()
        self.earth_alloc -= JUMP_COST
        self.events.append("jump")
        if self.earth_alloc <= 0:
            self.earth_alloc = 0.0
            self.game_over = True
        return True

    def drain_events(self) -> list[str]:
        drained = self.events
        self.events = []
        return drained

    def press_step(self) -> None:
        self.earth_alloc -= STEP_COST
        if self.earth_alloc <= 0:
            self.earth_alloc = 0.0
            self.game_over = True

    def _pop_struck_hazard(self) -> float:
        for i, hz in enumerate(self.falling):
            if self.player.rect.colliderect(hz.rect):
                damage = hz.damage
                del self.falling[i]
                return damage
        return 0.0

    def take_damage(self, damage: float) -> None:
        if self.invuln_timer > 0.0:
            return
        self.hearts = max(0.0, self.hearts - damage)
        self.hits += 1
        self.invuln_timer = INVULN_DURATION
        self.events.append("hazard")
        self.player = Player(*self.chamber.spawn_point)
        if self.hearts <= 0.0:
            self.game_over = True

    def step(self, dt: float, keys) -> None:
        dt = min(dt, MAX_DT)
        if self.game_over or self.won:
            return

        self.elapsed += dt
        if self.invuln_timer > 0.0:
            self.invuln_timer = max(0.0, self.invuln_timer - dt)

        self.earth_alloc = max(0.0, self.earth_alloc - self.chamber.drain_rate * dt)
        if self.earth_alloc <= 0.0:
            self.game_over = True

        self.player.handle_input(keys)
        was_airborne = not self.player.on_ground
        self.player.update(dt, self.chamber.platforms)
        if was_airborne and self.player.on_ground:
            self.events.append("land")

        self.chamber.update(dt)
        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            profile = self.chamber.spawn_profile
            self.spawn_timer = next_interval(self.elapsed, profile)
            self.falling.append(
                FallingHazard(spawn_x(self.player.rect.x), next_speed(self.elapsed, profile))
            )
        for hz in self.falling:
            hz.update(dt)
        self.falling = [hz for hz in self.falling if not hz.is_spent()]

        # Check collisions and deal heart damage
        struck_damage = self._pop_struck_hazard()
        chamber_damage = self.chamber.hazard_damage(self.player.rect)
        total_damage = max(struck_damage, chamber_damage)

        if total_damage > 0.0:
            self.take_damage(total_damage)

        if self.chamber.reached_target(self.player.rect):
            self.won = True
            self.events.append("portal")
            self.best_saved = max(self.best_saved, self.earth_alloc)
            if self.best_time == 0.0 or self.elapsed < self.best_time:
                self.best_time = self.elapsed
