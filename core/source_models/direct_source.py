from dataclasses import dataclass

@dataclass
class DirectSource:
    release_rate_g_s: float
    duration_s: float
    height_m: float = 0.0

    def total_mass_g(self) -> float:
        return self.release_rate_g_s * self.duration_s

    def as_puff(self):
        return {'Q': self.release_rate_g_s, 't_r': self.duration_s, 'h_s': self.height_m}
