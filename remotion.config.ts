import {Config} from '@remotion/cli/config';

// Rendus en JPEG pour la vitesse ; les épisodes alpha (webm) se rendent en PNG via l'interface.
Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
