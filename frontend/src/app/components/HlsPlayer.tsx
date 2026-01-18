"use client";

import { useEffect, useRef } from "react";
import Hls from "hls.js";

type Props = {
  src: string;      // URL do .m3u8
  autoPlay?: boolean;
  muted?: boolean;
};

export default function HlsPlayer({ src, autoPlay = false, muted = false }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Safari / iOS: HLS działa natywnie
    if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = src;
      return;
    }

    // Chrome/Firefox/Edge: używamy hls.js
    if (Hls.isSupported()) {
      const hls = new Hls({
        // opcjonalnie:
        // lowLatencyMode: true,
      });

      hls.loadSource(src);
      hls.attachMedia(video);

      hls.on(Hls.Events.ERROR, (_, data) => {
        console.error("HLS error:", data);
      });

      return () => {
        hls.destroy();
      };
    } else {
      console.error("HLS nie jest wspierany w tej przeglądarce.");
    }
  }, [src]);

  return (
    <video
      ref={videoRef}
      controls
      playsInline
      autoPlay={autoPlay}
      muted={muted}
      style={{
        width: "100%",
        maxWidth: 1000,
        borderRadius: 12,
        background: "#000",
      }}
    />
  );
}
