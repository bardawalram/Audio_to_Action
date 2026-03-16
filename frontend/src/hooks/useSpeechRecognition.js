import { useState, useRef, useEffect } from 'react'

/**
 * Custom hook for real-time speech recognition using Web Speech API
 */
const useSpeechRecognition = () => {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState(null)

  const recognitionRef = useRef(null)

  useEffect(() => {
    // Check if browser supports Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      setError('Speech Recognition not supported in this browser')
      return
    }

    // Initialize Speech Recognition
    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = true
    recognition.lang = 'en-US'

    recognition.onstart = () => {
      console.log('[SpeechRecognition] Started listening')
    }

    recognition.onaudiostart = () => {
      console.log('[SpeechRecognition] Audio capture started')
    }

    recognition.onresult = (event) => {
      console.log('[SpeechRecognition] Got result:', event.results)
      let interim = ''
      let final = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptText = event.results[i][0].transcript
        console.log('[SpeechRecognition] Transcript:', transcriptText, 'isFinal:', event.results[i].isFinal)

        if (event.results[i].isFinal) {
          final += transcriptText + ' '
        } else {
          interim += transcriptText
        }
      }

      if (final) {
        setTranscript(prev => prev + final)
      }
      setInterimTranscript(interim)
    }

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error)
      if (event.error !== 'no-speech') {
        setError(`Speech recognition error: ${event.error}`)
      }
    }

    recognition.onend = () => {
      setIsListening(false)
    }

    recognitionRef.current = recognition

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop()
      }
    }
  }, [])

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setTranscript('')
      setInterimTranscript('')
      setError(null)

      try {
        recognitionRef.current.start()
        setIsListening(true)
      } catch (err) {
        console.error('Error starting speech recognition:', err)
        setError('Failed to start speech recognition')
      }
    }
  }

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    }
  }

  const resetTranscript = () => {
    setTranscript('')
    setInterimTranscript('')
    setError(null)
  }

  const fullTranscript = transcript + (interimTranscript ? ' ' + interimTranscript : '')

  return {
    isListening,
    transcript: fullTranscript,
    finalTranscript: transcript,
    interimTranscript,
    error,
    startListening,
    stopListening,
    resetTranscript,
    isSupported: !!recognitionRef.current,
  }
}

export default useSpeechRecognition
