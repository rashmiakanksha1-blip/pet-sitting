// Voice demo (v3) — recorded welcome + ElevenLabs for dynamic lines.
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

  function playAudioSrc(src, sourceLabel) {
    return new Promise((resolve, reject) => {
      const audio = new Audio(src);
      const timer = setTimeout(() => {
        audio.pause();
        reject(new Error('Playback timed out'));
      }, 60000);
      audio.onended = () => {
        clearTimeout(timer);
        resolve(sourceLabel);
      };
      audio.onerror = () => {
        clearTimeout(timer);
        reject(new Error('Playback failed'));
      };
      audio.play().catch((err) => {
        clearTimeout(timer);
        reject(err);
      });
      activeAudio = audio;
    });
  }

  function warmVoices() {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  }
  warmVoices();

  function pickCalmFemaleVoice(voices) {
    const femaleName = /flo|shelley|sandy|samantha|kate|serena|fiona|martha|victoria|stephanie|karen|moira|tessa|laura|emily|susan|jenny|heather|alice|charlotte|lily|female|woman/i;
    const english = voices.filter((v) => /^en(-GB)?/i.test(v.lang));
    const britishFemale = english.find(
      (v) => /en-GB/i.test(v.lang) && femaleName.test(v.name),
    );
    if (britishFemale) return britishFemale;
    const anyFemale = english.find((v) => femaleName.test(v.name));
    if (anyFemale) return anyFemale;
    return english.find((v) => /en-GB/i.test(v.lang)) || english[0] || voices[0] || null;
  }

  function waitForVoices(ms) {
    return new Promise((resolve) => {
      if (!window.speechSynthesis) {
        resolve([]);
        return;
      }
      const deadline = Date.now() + ms;
      const tick = () => {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length || Date.now() >= deadline) {
          resolve(voices);
          return;
        }
        setTimeout(tick, 50);
      };
      tick();
    });
  }

  function speakBrowser(text) {
    return new Promise((resolve, reject) => {
      if (!window.speechSynthesis) {
        reject(new Error('No speech support'));
        return;
      }

      const maxMs = Math.min(60000, Math.max(12000, text.length * 90));
      let settled = false;

      function finish(ok, value) {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        if (ok) resolve(value);
        else reject(value);
      }

      const timer = setTimeout(() => {
        window.speechSynthesis.cancel();
        finish(false, new Error('Speech timed out'));
      }, maxMs);

      waitForVoices(800).then((voices) => {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.86;
        utterance.pitch = 0.94;
        const picked = pickCalmFemaleVoice(voices);
        if (picked) utterance.voice = picked;
        utterance.onend = () => finish(true, 'browser');
        utterance.onerror = () => finish(false, new Error('Browser speech failed'));
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
      });
    });
  }

  async function speakElevenLabs(text) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);
    let res;
    try {
      const payload = { text };
      if (voiceCfg.voiceId) payload.voiceId = voiceCfg.voiceId;
      res = await fetch(speakUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
    } finally {
      clearTimeout(timeout);
    }
    if (!res.ok) throw new Error('ElevenLabs unavailable');
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    return playAudioSrc(objectUrl, 'elevenlabs').finally(() => {
      URL.revokeObjectURL(objectUrl);
    });
  }

  async function speakWelcome() {
    if (busy) return null;
    busy = true;
    stop(false);
    setStatus('playing');
    try {
      if (voiceCfg.welcomeAudio) {
        const source = await playAudioSrc(voiceCfg.welcomeAudio, 'recorded');
        setStatus(source);
        return source;
      }
      const text = voiceCfg.welcomeText
        || `Welcome to ${SITE_CONFIG.businessName}. ${SITE_CONFIG.tagline || ''}`;
      busy = false;
      return speak(text.trim());
    } catch {
      setStatus('error');
      return null;
    } finally {
      busy = false;
    }
  }

  async function speak(text) {
    if (!text || busy) return null;
    busy = true;
    stop(false);
    setStatus('playing');
    try {
      if (speakUrl) {
        try {
          const source = await speakElevenLabs(text);
          setStatus(source);
          return source;
        } catch {
          // Fall through to browser voice.
        }
      }
      const source = await speakBrowser(text);
      setStatus(source);
      return source;
    } catch {
      setStatus('error');
      return null;
    } finally {
      busy = false;
    }
  }

  function setStatus(source) {
    document.querySelectorAll('[data-voice-status]').forEach((el) => {
      if (source === 'playing') {
        el.textContent = 'Playing…';
        el.dataset.state = 'playing';
      } else if (source === 'recorded') {
        el.textContent = 'Calm British voice';
        el.dataset.state = 'recorded';
      } else if (source === 'elevenlabs') {
        el.textContent = 'Calm British voice (ElevenLabs)';
        el.dataset.state = 'elevenlabs';
      } else if (source === 'browser') {
        el.textContent = 'Pet facts use device voice until ElevenLabs is connected';
        el.dataset.state = 'browser';
      } else if (source === 'error') {
        el.textContent = 'Voice unavailable — check sound is on';
        el.dataset.state = 'error';
      } else {
        el.textContent = '';
        el.dataset.state = '';
      }
    });
  }

  window.PSC_VOICE = { speak, speakWelcome, stop };
})();
