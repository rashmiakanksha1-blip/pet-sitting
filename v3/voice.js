// ElevenLabs voice demo (v3) — API key stays on Netlify, never in the browser.
(function () {
  const voiceCfg = (typeof SITE_CONFIG !== 'undefined' && SITE_CONFIG.voice) || {};
  if (!voiceCfg.enabled) return;

  const speakUrl = voiceCfg.speakUrl || '';
  let activeAudio = null;
  let busy = false;

  function stop(resetBusy) {
    if (activeAudio) {
      activeAudio.pause();
      if (activeAudio.dataset.objectUrl) {
        URL.revokeObjectURL(activeAudio.dataset.objectUrl);
      }
      activeAudio = null;
    }
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (resetBusy !== false) busy = false;
  }

  function speakBrowser(text) {
    return new Promise((resolve, reject) => {
      if (!window.speechSynthesis) {
        reject(new Error('No speech support'));
        return;
      }
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.94;
      utterance.pitch = 1;
      const voices = window.speechSynthesis.getVoices();
      const british = voices.find((v) => /en-GB/i.test(v.lang));
      if (british) utterance.voice = british;
      utterance.onend = () => resolve('browser');
      utterance.onerror = () => reject(new Error('Browser speech failed'));
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utterance);
    });
  }

  async function speakElevenLabs(text) {
    const res = await fetch(speakUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error('ElevenLabs unavailable');
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    const audio = new Audio(objectUrl);
    audio.dataset.objectUrl = objectUrl;
    return new Promise((resolve, reject) => {
      audio.onended = () => resolve('elevenlabs');
      audio.onerror = () => reject(new Error('Playback failed'));
      audio.play().catch(reject);
      activeAudio = audio;
    });
  }

  async function speak(text) {
    if (!text || busy) return null;
    busy = true;
    stop(false);
    try {
      if (speakUrl) {
        const source = await speakElevenLabs(text);
        setStatus(source);
        return source;
      }
      throw new Error('No speak URL');
    } catch {
      try {
        const source = await speakBrowser(text);
        setStatus(source);
        return source;
      } catch {
        setStatus('error');
        return null;
      }
    } finally {
      busy = false;
    }
  }

  function setStatus(source) {
    document.querySelectorAll('[data-voice-status]').forEach((el) => {
      if (source === 'elevenlabs') {
        el.textContent = 'Powered by ElevenLabs';
        el.dataset.state = 'elevenlabs';
      } else if (source === 'browser') {
        el.textContent = 'Demo voice (add ElevenLabs key on Netlify for studio quality)';
        el.dataset.state = 'browser';
      } else {
        el.textContent = '';
        el.dataset.state = '';
      }
    });
  }

  window.PSC_VOICE = { speak, stop };
})();
