import React from 'react';
import {Composition} from 'remotion';
import {F} from './lib/time';
import {Episode as Demo} from './demo/Episode';
import {meta as demo} from './demo/data';

/** Une <Composition> par épisode : ajouter ici chaque nouveau dossier src/<episode>/. */
export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id={demo.id}
      component={Demo}
      width={demo.width}
      height={demo.height}
      fps={demo.fps}
      durationInFrames={F(demo.durationSec)}
    />
  </>
);
