/* Vanilla JS: language toggle, chat box and voice assistant (Web Speech API, no libraries). */
(function () {
  'use strict';
  var root = document.documentElement;
  var rec = null, listening = false;
  function $(id) { return document.getElementById(id); }
  function lang() { return root.dataset.lang === 'en' ? 'en' : 'te'; }
  function speechLang() { return lang() === 'te' ? 'te-IN' : 'en-IN'; }

  function setLang(l) {
    root.dataset.lang = l; root.lang = l;
    try { localStorage.setItem('lang', l); } catch (e) {}
    document.querySelectorAll('option[data-te]').forEach(function (o) { o.textContent = o.dataset[l]; });
    document.querySelectorAll('[data-ph-te]').forEach(function (i) { i.placeholder = i.dataset['ph' + (l === 'te' ? 'Te' : 'En')]; });
    var b = $('lang-btn'); if (b) b.textContent = l === 'te' ? 'English' : 'తెలుగు';
    if (listening && rec) rec.stop();
  }
  var langBtn = $('lang-btn');
  if (langBtn) langBtn.addEventListener('click', function () { setLang(lang() === 'te' ? 'en' : 'te'); });
  setLang(lang());

  /* ---- Chat ---- */
  var box = $('chat'); if (!box) return;
  var fab = $('chat-fab'), panel = $('chat-panel'), log = $('chat-log'), form = $('chat-form');
  var input = $('chat-input'), mic = $('chat-mic'), voice = $('chat-voice');

  function show(id) { var h = $(id); if (h) h.hidden = false; }
  function hide(id) { var h = $(id); if (h) h.hidden = true; }

  function addUser(text) {
    var d = document.createElement('div'); d.className = 'msg user'; d.textContent = text;
    log.appendChild(d); log.scrollTop = log.scrollHeight;
  }
  function addBot(r) {
    var d = document.createElement('div'); d.className = 'msg bot';
    ['te', 'en'].forEach(function (l) {
      var s = document.createElement('span'); s.dataset.l = l; s.lang = l; s.textContent = r[l]; d.appendChild(s);
    });
    if (r.link) {
      var a = document.createElement('a'); a.href = r.link.href;
      ['te', 'en'].forEach(function (l) { var s = document.createElement('span'); s.dataset.l = l; s.textContent = r.link[l]; a.appendChild(s); });
      d.appendChild(a);
    }
    if (r.source) { var m = document.createElement('small'); m.textContent = r.source; d.appendChild(m); }
    log.appendChild(d); log.scrollTop = log.scrollHeight;
    return d;
  }

  function speak(text) {
    if (!('speechSynthesis' in window) || !text) return;
    speechSynthesis.cancel();
    var u = new SpeechSynthesisUtterance(text), l = speechLang();
    u.lang = l;
    var v = speechSynthesis.getVoices().filter(function (x) { return x.lang.replace('_', '-').toLowerCase().indexOf(l.slice(0, 2)) === 0; })[0];
    if (v) u.voice = v; else if (l === 'te-IN') show('hint-novoice');
    speechSynthesis.speak(u);
  }
  function stopSpeak() { if ('speechSynthesis' in window) speechSynthesis.cancel(); }

  function send(text, viaVoice) {
    text = (text || '').trim(); if (!text) return;
    addUser(text); input.value = '';
    var wait = document.createElement('div'); wait.className = 'msg bot'; wait.textContent = '…'; log.appendChild(wait);
    var farmer = box.dataset.farmer ? parseInt(box.dataset.farmer, 10) : null;
    fetch('/api/chat', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, farmer_id: farmer, scenario: box.dataset.scenario || null })
    }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (r) { wait.remove(); addBot(r); if (viaVoice || voice.checked) speak(r[lang()]); })
      .catch(function () { wait.remove(); addBot({ te: box.dataset.errTe, en: box.dataset.errEn }); });
  }

  fab.addEventListener('click', function () {
    panel.hidden = !panel.hidden;
    if (!panel.hidden) {
      if (!log.children.length) addBot({ te: box.dataset.helloTe, en: box.dataset.helloEn });
      input.focus();
    } else { stopSpeak(); }
  });
  $('chat-close').addEventListener('click', function () { panel.hidden = true; stopSpeak(); });
  form.addEventListener('submit', function (e) { e.preventDefault(); send(input.value, false); });

  /* ---- Voice input: needs Chrome-like browser, secure context (HTTPS or localhost), and internet ---- */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR || !window.isSecureContext) {
    mic.hidden = true; show('hint-nomic');
  } else {
    mic.addEventListener('click', function () {
      if (listening) { rec.stop(); return; }
      stopSpeak(); hide('hint-denied');
      rec = new SR(); rec.lang = speechLang(); rec.interimResults = false; rec.maxAlternatives = 1;
      rec.onstart = function () { listening = true; mic.classList.add('listening'); input.placeholder = box.dataset['listening' + (lang() === 'te' ? 'Te' : 'En')]; };
      rec.onresult = function (e) { send(e.results[0][0].transcript, true); };
      rec.onerror = function () { show('hint-denied'); };
      rec.onend = function () { listening = false; mic.classList.remove('listening'); setLang(lang()); };
      rec.start();
    });
  }
})();
