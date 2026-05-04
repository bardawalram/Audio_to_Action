import { useState, useRef, useCallback } from 'react'

/**
 * Custom hook for real-time speech recognition using Web Speech API
 */
const useSpeechRecognition = () => {
  const [isListening, setIsListening] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState(null)

  const recognitionRef = useRef(null)
  const shouldListenRef = useRef(false)

  const getRecognition = useCallback(() => {
    if (recognitionRef.current) return recognitionRef.current

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setError('Speech Recognition not supported in this browser')
      return null
    }

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
      let interim = ''
      let final = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcriptText = event.results[i][0].transcript
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
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        setError(`Speech recognition error: ${event.error}`)
      }
    }

    recognition.onend = () => {
      // Auto-restart if we're still supposed to be listening
      // (Web Speech API can stop after silence or network issues)
      if (shouldListenRef.current) {
        console.log('[SpeechRecognition] Ended unexpectedly, restarting...')
        try {
          recognition.start()
        } catch (err) {
          console.error('[SpeechRecognition] Failed to restart:', err)
          setIsListening(false)
          shouldListenRef.current = false
        }
      } else {
        setIsListening(false)
      }
    }

    recognitionRef.current = recognition
    return recognition
  }, [])

  const startListening = useCallback(() => {
    const recognition = getRecognition()
    if (!recognition) return

    setTranscript('')
    setInterimTranscript('')
    setError(null)
    shouldListenRef.current = true

    try {
      recognition.start()
      setIsListening(true)
    } catch (err) {
      // If already started, abort and retry
      if (err.name === 'InvalidStateError') {
        recognition.abort()
        setTimeout(() => {
          try {
            recognition.start()
            setIsListening(true)
          } catch (retryErr) {
            console.error('Error restarting speech recognition:', retryErr)
            setError('Failed to start speech recognition')
            shouldListenRef.current = false
          }
        }, 100)
      } else {
        console.error('Error starting speech recognition:', err)
        setError('Failed to start speech recognition')
        shouldListenRef.current = false
      }
    }
  }, [getRecognition])

  const stopListening = useCallback(() => {
    shouldListenRef.current = false
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      setIsListening(false)
    }
  }, [])

  const resetTranscript = useCallback(() => {
    setTranscript('')
    setInterimTranscript('')
    setError(null)
  }, [])

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
    isSupported: !!(window.SpeechRecognition || window.webkitSpeechRecognition),
  }
}

export default useSpeechRecognition
