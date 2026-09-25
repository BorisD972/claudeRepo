/** Un bloc de sous-titre (1 à 2 mots), temps en secondes, généré par scripts/gen-subs.py. */
export type Sub = {
  text: string;
  start: number;
  end: number;
};

/** Style typographique d'un sous-titre : le contraste est typographique, jamais chromatique. */
export type SubStyle = {
  fontFamily: string;
  fontWeight: number;
  fontSize: number; // en px pour une largeur de 1080 (mis à l'échelle ensuite)
  italic: boolean;
  uppercase: boolean;
  letterSpacing: number; // em
  bottom: number; // distance au bas de l'image, px pour 1080 de large
  enterFrames: number; // durée de l'apparition (<= 5-6 frames)
  leadSec: number; // l'apparition démarre ce temps AVANT l'attaque du mot
  enterScaleFrom: number; // échelle de départ de l'apparition
};
