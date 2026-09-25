import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {F} from '../lib/time';
import {Subtitles} from '../lib/Subtitles';
import {background, subStyle, title} from './data';
import {subs} from './subs';

/** Rendu de l'épisode : lit tout dans data.ts et subs.ts, aucune valeur en dur. */
export const Episode: React.FC = () => {
  const frame = useCurrentFrame();
  const {width} = useVideoConfig();
  const k = width / 1080;

  const opacity = interpolate(
    frame,
    [F(title.inSec), F(title.inSec + title.inDurSec), F(title.outSec), F(title.outSec + title.outDurSec)],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );
  const rise = interpolate(frame, [F(title.inSec), F(title.inSec + title.inDurSec)], [40, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{background: `linear-gradient(${background.top}, ${background.bottom})`}}>
      <AbsoluteFill style={{alignItems: 'center'}}>
        <div
          style={{
            marginTop: title.top * k,
            opacity,
            transform: `translateY(${rise * k}px)`,
            textAlign: 'center',
            color: '#ffffff',
            fontFamily: title.fontFamily,
          }}
        >
          <div style={{fontSize: title.fontSize * k, fontWeight: title.fontWeight}}>{title.text}</div>
          <div style={{fontSize: title.subFontSize * k, fontWeight: 400, fontStyle: 'italic', marginTop: 12 * k}}>
            {title.sub}
          </div>
        </div>
      </AbsoluteFill>
      <Subtitles subs={subs} style={subStyle} />
    </AbsoluteFill>
  );
};
