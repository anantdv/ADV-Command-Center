import { useMemo, useRef, useState } from 'react'

type SpeechRecognitionResultEvent = Event & {
  resultIndex: number
  results: {
    length: number
    [index: number]: {
      isFinal: boolean
      [index: number]: { transcript: string; confidence: number }
    }
  }
}

type SpeechRecognitionErrorEvent = Event & { error?: string; message?: string }

type SpeechRecognitionLike = {
  lang: string
  interimResults: boolean
  continuous: boolean
  start: () => void
  stop: () => void
  abort: () => void
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null
  onend: (() => void) | null
}

type SpeechRecognitionCtor = new () => SpeechRecognitionLike

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionCtor
    webkitSpeechRecognition?: SpeechRecognitionCtor
  }
}

export function useVoiceInput(options?: {
  language?: string
  onTranscript?: (text: string) => void
  onError?: (error: string) => void
}) {
  const [listening, setListening] = useState(false)
  const [supported] = useState(() => typeof window !== 'undefined' && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition))
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)

  const start = useMemo(() => () => {
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!Ctor) {
      options?.onError?.('Voice input is not supported in this browser.')
      return
    }
    recognitionRef.current?.abort()
    const recognition = new Ctor()
    recognition.lang = options?.language || 'en-IN'
    recognition.interimResults = true
    recognition.continuous = false
    recognition.onresult = event => {
      let transcript = ''
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        transcript += event.results[index][0]?.transcript || ''
      }
      if (transcript.trim()) options?.onTranscript?.(transcript.trim())
    }
    recognition.onerror = event => {
      setListening(false)
      options?.onError?.(event.message || event.error || 'Voice input failed.')
    }
    recognition.onend = () => setListening(false)
    recognitionRef.current = recognition
    setListening(true)
    recognition.start()
  }, [options])

  const stop = () => {
    recognitionRef.current?.stop()
    setListening(false)
  }

  const toggle = () => {
    if (listening) stop()
    else start()
  }

  return { listening, supported, start, stop, toggle }
}
