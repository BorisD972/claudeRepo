/**
 * TÉLÉCOMMANDE de l'épisode « demo ». Tous les réglages sont ici : on itère dans ce fichier.
 * Temps en secondes (convertis en frames par F() au rendu), tailles en px pour 1080 de large.
 */
import type {SubStyle} from '../lib/types';

export const meta = {
  id: 'demo',
  width: 1080,
  height: 1920,
  fps: 30,
  durationSec: 6,
};

// Pas de média dans la démo : un fond uni. Pour un vrai épisode : src/<episode>/ + public/<episode>/.
export const background = {
  top: '#1b1f2a',
  bottom: '#0b0d12',
};

export const title = {
  text: 'MON STUDIO',
  sub: 'Remotion · piloté par Claude',
  fontFamily: 'Helvetica, Arial, sans-serif',
  fontWeight: 900,
  fontSize: 120,
  subFontSize: 44,
  top: 640, // px depuis le haut
  inSec: 0.2, // apparition
  inDurSec: 0.35,
  outSec: 2.6, // disparition
  outDurSec: 0.3,
};

// Style des sous-titres : à valider avec toi pour chaque épisode (pas de couleur).
export const subStyle: SubStyle = {
  fontFamily: 'Helvetica, Arial, sans-serif',
  fontWeight: 800,
  fontSize: 92,
  italic: false,
  uppercase: true,
  letterSpacing: -0.01,
  bottom: 520,
  enterFrames: 5,
  leadSec: 0.1,
  enterScaleFrom: 0.86,
};
