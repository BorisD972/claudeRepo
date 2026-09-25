import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {F} from './time';
import type {Sub, SubStyle} from './types';

/**
 * Affiche le bloc de sous-titre courant. L'apparition part `leadSec` avant l'attaque
 * du mot et dure `enterFrames` (<= 5-6 frames) : plus long, c'est perçu désynchronisé.
 * Pas de couleur : blanc, le contraste vient du poids, de la taille et de l'italique.
 */
export const Subtitles: React.FC<{subs: Sub[]; style: SubStyle}> = ({subs, style}) => {
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();
  const k = width / 1080;

  const current = subs.find((s) => frame >= F(s.start - style.leadSec) && frame < F(s.end));
  if (!current) return null;

  const enterStart = F(current.start - style.leadSec);
  const progress = interpolate(frame, [enterStart, enterStart + style.enterFrames], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scale = interpolate(progress, [0, 1], [style.enterScaleFrom, 1]);

  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', pointerEvents: 'none'}}>
      <div
        style={{
          marginBottom: style.bottom * k,
          fontFamily: style.fontFamily,
          fontWeight: style.fontWeight,
          fontStyle: style.italic ? 'italic' : 'normal',
          fontSize: style.fontSize * k,
          letterSpacing: `${style.letterSpacing}em`,
          textTransform: style.uppercase ? 'uppercase' : 'none',
          color: '#ffffff',
          textShadow: `0 ${4 * k}px ${18 * k}px rgba(0,0,0,0.55)`,
          opacity: progress,
          transform: `scale(${scale})`,
          whiteSpace: 'nowrap',
        }}
      >
        {current.text}
      </div>
    </AbsoluteFill>
  );
};
