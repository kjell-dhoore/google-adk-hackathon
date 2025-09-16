/**
 * Copyright 2024 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  Dispatch,
  SetStateAction,
} from "react";
import { MultimodalLiveClient } from "../utils/multimodal-live-client";
import { AudioStreamer } from "../utils/audio-streamer";
import { audioContext } from "../utils/utils";
import VolMeterWorket from "../utils/worklets/vol-meter";

export type UseLiveAPIResults = {
  client: MultimodalLiveClient;
  connected: boolean;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  volume: number;
};

export type UseLiveAPIProps = {
  url?: string;
  userId?: string;
  onRunIdChange?: Dispatch<SetStateAction<string>>;
  onAgentTransition: (nextAgent: "vacancy_prompter" | "question_generator" | "interviewer", data?: any) => void;
  vacancyDescription: string;
  generatedQuestions: string;
  currentAgent: "vacancy_prompter" | "question_generator" | "interviewer";
};

export function useLiveAPI({
  url,
  userId,
  onAgentTransition,
  vacancyDescription,
  generatedQuestions,
  currentAgent,
}: UseLiveAPIProps): UseLiveAPIResults {
  const client = useMemo(
    () => new MultimodalLiveClient({ url, userId }),
    [url, userId],
  );
  const audioStreamerRef = useRef<AudioStreamer | null>(null);

  const [connected, setConnected] = useState(false);
  const [volume, setVolume] = useState(0);

  // register audio for streaming server -> speakers
  useEffect(() => {
    if (currentAgent === "interviewer" && !audioStreamerRef.current) {
      audioContext({ id: "audio-out", isVoiceEnabled: true }).then((audioCtx: AudioContext) => {
        audioStreamerRef.current = new AudioStreamer(audioCtx);
        audioStreamerRef.current
          .addWorklet<any>("vumeter-out", VolMeterWorket, (ev: any) => {
            setVolume(ev.data.volume);
          })
          .then(() => {
            // Successfully added worklet
          });
      });
    }
  }, [audioStreamerRef, currentAgent]);

  useEffect(() => {
    const onClose = () => {
      setConnected(false);
    };

    const stopAudioStreamer = () => audioStreamerRef.current?.stop();

    const onAudio = (data: ArrayBuffer) =>
      audioStreamerRef.current?.addPCM16(new Uint8Array(data));

    const onMessage = (message: any) => {
      if (client.url.includes("vacancy_prompter")) {
        onAgentTransition("question_generator", message.text);
      } else if (client.url.includes("question_generator")) {
        onAgentTransition("interviewer", message.text);
      }
    };

    client
      .on("close", onClose)
      .on("interrupted", stopAudioStreamer)
      .on("audio", onAudio)
      .on("message", onMessage);

    return () => {
      client
        .off("close", onClose)
        .off("interrupted", stopAudioStreamer)
        .off("audio", onAudio)
        .off("message", onMessage);
    };
  }, [client, onAgentTransition]);

  const connect = useCallback(async () => {
    client.disconnect();
    await client.connect();
    setConnected(true);

    // Send initial data if available
    if (client.url.includes("question_generator") && vacancyDescription) {
      client.send(vacancyDescription);
    } else if (client.url.includes("interviewer") && generatedQuestions) {
      client.send(generatedQuestions);
    }
  }, [client, setConnected, vacancyDescription, generatedQuestions]);

  const disconnect = useCallback(async () => {
    client.disconnect();
    setConnected(false);
  }, [setConnected, client]);

  return {
    client,
    connected,
    connect,
    disconnect,
    volume,
  };
}
