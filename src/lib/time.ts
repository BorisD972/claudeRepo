/** Cadence unique du studio : tout est pensé en 30 fps CFR (mezzanine). */
export const FPS = 30;

/** Secondes -> frames. C'est le seul endroit où l'on convertit. Ex : F(1.5) = 45. */
export const F = (sec: number): number => Math.round(sec * FPS);
