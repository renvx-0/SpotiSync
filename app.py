import webview

HTML = """
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');
    :root { color-scheme: dark; }
    * { box-sizing: border-box; font-family: Inter, system-ui, sans-serif; margin: 0; padding: 0; }
    html, body { margin: 0; height: 100%; background: #0d0d0d; color: #fff; overflow: hidden; }
    .bar { height: 30px; position: relative; display: flex; align-items: center; justify-content: flex-end; padding: 0 12px; gap: 8px; background-color: #101010; border-bottom: solid 1px #1A1A1A; }
    .drag { position: absolute; inset: 0; }
    .dot { width: 14px; height: 14px; border-radius: 50%; border: 0; cursor: pointer; position: relative; z-index: 1; }
    .min { background: #febc2e } .close { background: #ff5f57 }
    .bar-title {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0;
      pointer-events: none;
      color: #B9B9B9;
      font-weight: 500;
      font-size: 14px;
    }

    .track { display: flex; align-items: center; justify-content: center; gap: 15px; }
    .track-thumbnail { height: 130px; border-radius: 5px; border: solid 2px #202020; }
    #track-title { font-size: 24px; font-weight: bold; }
    #track-artists { font-size: 14px; color: #B7B7B7; }

    .track-info-flex {
      margin-top: 15px;
      gap: 15px;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding-left: 20px;
      padding-right: 20px;
    }

    .lyrics {
      height: 130px;
      width: 100%;
      background-color: #070707;
      border-radius: 10px;
      border: solid 1px #191919;
      overflow: hidden;
    }

    .lyrics-viewport {
      height: 100%;
      overflow: hidden;
      -webkit-mask-image: linear-gradient(to bottom, transparent 0%, #000 30%, #000 70%, transparent 100%);
              mask-image: linear-gradient(to bottom, transparent 0%, #000 30%, #000 70%, transparent 100%);
    }

    .lyrics-track {
      transition: transform .55s cubic-bezier(.2, .8, .2, 1);
      will-change: transform;
    }

    .lyric-line {
      height: 40px;
      line-height: 40px;
      text-align: center;
      white-space: nowrap;
      padding: 0 10px;
      font-size: 20px;
      color: #949494;
      opacity: .55;
      transform: scale(1);
      transition: transform .45s cubic-bezier(.2, .8, .2, 1), color .35s, opacity .35s;
    }

    .lyric-line.active {
      color: #fff;
      opacity: 1;
      font-weight: 500;
      transform: scale(1.2);
    }

    @media (prefers-reduced-motion: reduce) {
      .lyrics-track, .lyric-line { transition: none; }
    }

    .settings {
      background: #101010;
      margin-left: 20px;
      margin-right: 20px;
      margin-top: 15px;
      display: flex;
      align-items: center;
      gap: 20px;
      padding: 15px;
      border-radius: 10px;
    }

    .option {
      background: transparent;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }

    .option-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 30px;
      width: 100%;
    }

    .option-title {
      display: flex;
      gap: 7px;
      align-items: center;
      color: #B5B5B5;
      transition: color .3s;
    }

    .option-title .lucide-info { color: #575757; }

    .option-dropdown {
      width: 100%;
      height: 24px;
      background: #191919;
      border-radius: 5px;
      border: solid 1px #2B2B2B;
      box-shadow: 0 1px 4px 0 rgba(0, 0, 0, 0.205);
      position: relative;
    }

    .option-dropdown svg {
      stroke: #616161;
      position: absolute;
      right: 5px;
    }

    .option-textbox {
      width: 100%;
      height: 24px;
      background: #191919;
      border-radius: 5px;
      border: solid 1px #2B2B2B;
      box-shadow: 0 1px 4px 0 rgba(0, 0, 0, 0.205);
      position: relative;
    }

    .option.discord { flex-grow: 1; }

    .switch {
      position: relative;
      display: inline-block;
      width: 45px;
      height: 20px;
      border-radius: 5px;
    }

    .switch input { opacity: 0; width: 0; height: 0; }

    .slider {
      position: absolute;
      cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      border-radius: 5px;
      background-color: #070707;
      border: solid 1px #191919;
      -webkit-transition: .4s;
      transition: .4s;
    }

    .slider:before {
      position: absolute;
      content: "";
      height: 22px;
      width: 22px;
      left: -2px;
      bottom: -2px;
      border-radius: 5px;
      background-color: #2F2F2F;
      -webkit-transition: .4s;
      transition: .4s;
    }

    input:checked + .slider::before { background-color: white; }

    input:checked + .slider:before {
      -webkit-transform: translateX(26px);
      -ms-transform: translateX(26px);
      transform: translateX(26px);
    }

    .slider.round { border-radius: 34px; }
    .slider.round:before { border-radius: 50%; }

    .option:has(input:checked) .option-title { color: #fff; }

    .divider {
      height: 55px;
      width: 2px;
      background: linear-gradient(0deg, rgba(91, 91, 91, 0) 0%, rgba(91, 91, 91, 1) 34%, rgba(91, 91, 91, 1) 63%, rgba(91, 91, 91, 0) 100%);
    }

    .option-dropdown { cursor: pointer; user-select: none; transition: border-color .2s; }
    .option-dropdown.open { border-color: #3d3d3d; }
    .option-dropdown svg { top: 0; pointer-events: none; transition: transform .2s; }
    .option-dropdown.open svg { transform: rotate(180deg); }
    .dd-field { display: flex; align-items: center; height: 100%; padding: 0 26px 0 8px; }
    .dd-value { font-size: 12px; color: #D0D0D0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .dd-value.placeholder { color: #6a6a6a; }

    .dd-menu {
      position: absolute; left: 0; bottom: calc(100% + 6px);
      min-width: 100%; max-height: 190px; overflow-y: auto;
      background: #141414; border: 1px solid #2B2B2B; border-radius: 8px;
      padding: 4px; box-shadow: 0 8px 24px rgba(0, 0, 0, .5);
      z-index: 50; white-space: nowrap; cursor: default;
      opacity: 0; visibility: hidden; transform: translateY(6px); pointer-events: none;
      transition: opacity .18s, transform .18s, visibility .18s;
    }
    .option-dropdown.open .dd-menu { opacity: 1; visibility: visible; transform: none; pointer-events: auto; }
    .dd-menu::-webkit-scrollbar { width: 6px; }
    .dd-menu::-webkit-scrollbar-thumb { background: #2B2B2B; border-radius: 3px; }

    .dd-item { display: flex; align-items: center; gap: 8px; height: 28px; padding: 0 8px;
               border-radius: 5px; font-size: 12px; color: #A8A8A8; cursor: pointer; }
    .dd-item:hover { background: #1f1f1f; color: #fff; }
    .dd-item.selected { color: #fff; }
    .dd-item small { margin-left: auto; padding-left: 14px; color: #5a5a5a; font-size: 11px; }
    .dd-item.all { font-weight: 600; margin-bottom: 4px; border-bottom: 1px solid #222; border-radius: 5px 5px 0 0; }

    .mark { width: 14px; height: 14px; border: 1px solid #3a3a3a; flex: none; position: relative;
            transition: background .15s, border-color .15s; }
    .dd-item.multi .mark { border-radius: 4px; }
    .dd-item.single .mark { border-radius: 50%; }
    .dd-item.selected .mark { background: #fff; border-color: #fff; }
    .dd-item.multi.selected .mark::after { content: ""; position: absolute; left: 4px; top: 1px; width: 4px; height: 8px;
                                           border: solid #0d0d0d; border-width: 0 2px 2px 0; transform: rotate(45deg); }
    .dd-item.single.selected .mark::after { content: ""; position: absolute; inset: 3px; border-radius: 50%; background: #0d0d0d; }

    .option-textbox input {
      width: 100%;
      height: 100%;
      background: transparent;
      outline: none;
      border: none;
      padding-left: 8px;
      padding-right: 8px;
      font-size: 12px;
      color: #D0D0D0;
    }
  </style>
</head>
<body>
  <div class="bar">
    <div class="drag pywebview-drag-region"></div>
    <button class="dot min"   onclick="pywebview.api.minimize()"></button>
    <button class="dot close" onclick="pywebview.api.close()"></button>
    <p class="bar-title">SpotiSync</p>
  </div>

  <div class="track-info-flex">
    <div class="track">
      <img class="track-thumbnail" src="https://i.pinimg.com/564x/55/81/f4/5581f43ab5768a3cd855466c40757a99.jpg"/>
      <div class="track-details">
        <h1 id="track-title">Loading Song Title</h1>
        <p id="track-artists">Artists will appear here...</p>
      </div>
    </div>

    <div class="lyrics">
      <div class="lyrics-viewport" id="lyrics-viewport">
        <div class="lyrics-track" id="lyrics-track"></div>
      </div>
    </div>
  </div>

  <div class="settings">
    <div class="option decorators">
      <div class="option-header">
        <div class="option-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkles preview-icon"><path d="M11.017 2.814a1 1 0 0 1 1.966 0l1.051 5.558a2 2 0 0 0 1.594 1.594l5.558 1.051a1 1 0 0 1 0 1.966l-5.558 1.051a2 2 0 0 0-1.594 1.594l-1.051 5.558a1 1 0 0 1-1.966 0l-1.051-5.558a2 2 0 0 0-1.594-1.594l-5.558-1.051a1 1 0 0 1 0-1.966l5.558-1.051a2 2 0 0 0 1.594-1.594z"/><path d="M20 2v4"/><path d="M22 4h-4"/><circle cx="4" cy="20" r="2"/></svg>
          <p>Decorators</p>
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info preview-icon"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
        </div>
        <label class="switch">
          <input class="decorators-input" type="checkbox">
          <span class="slider"></span>
        </label>
      </div>
      <div class="option-dropdown" id="dd-decorators">
        <div class="dd-field"><span class="dd-value placeholder">Choose one…</span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-down preview-icon"><path d="m6 9 6 6 6-6"/></svg></div>
        <div class="dd-menu"></div>
      </div>
    </div>

    <div class="option censor">
      <div class="option-header">
        <div class="option-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-ban preview-icon"><circle cx="12" cy="12" r="10"/><path d="M4.929 4.929 19.07 19.071"/></svg>
          <p>Censor words</p>
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info preview-icon"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
        </div>
        <label class="switch">
          <input class="censor-input" type="checkbox">
          <span class="slider"></span>
        </label>
      </div>
      <div class="option-dropdown" id="dd-censor">
        <div class="dd-field"><span class="dd-value placeholder">Choose languages…</span><svg xmlns="http://www.w3.org/2000/svg" width="16" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-chevron-down preview-icon"><path d="m6 9 6 6 6-6"/></svg></div>
        <div class="dd-menu"></div>
      </div>
    </div>

    <div class="divider"></div>

    <div class="option discord">
      <div class="option-header">
        <div class="option-title">
          <svg xmlns="http://www.w3.org/2000/svg" width="25" height="20" viewBox="0 3 24 16" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"> <path d="M18.8943 4.34399C17.5183 3.71467 16.057 3.256 14.5317 3C14.3396 3.33067 14.1263 3.77866 13.977 4.13067C12.3546 3.89599 10.7439 3.89599 9.14391 4.13067C8.99457 3.77866 8.77056 3.33067 8.58922 3C7.05325 3.256 5.59191 3.71467 4.22552 4.34399C1.46286 8.41865 0.716188 12.3973 1.08952 16.3226C2.92418 17.6559 4.69486 18.4666 6.4346 19C6.86126 18.424 7.24527 17.8053 7.57594 17.1546C6.9466 16.92 6.34927 16.632 5.77327 16.2906C5.9226 16.184 6.07194 16.0667 6.21061 15.9493C9.68793 17.5387 13.4543 17.5387 16.889 15.9493C17.0383 16.0667 17.177 16.184 17.3263 16.2906C16.7503 16.632 16.153 16.92 15.5236 17.1546C15.8543 17.8053 16.2383 18.424 16.665 19C18.4036 18.4666 20.185 17.6559 22.01 16.3226C22.4687 11.7787 21.2836 7.83202 18.8943 4.34399ZM8.05593 13.9013C7.01058 13.9013 6.15725 12.952 6.15725 11.7893C6.15725 10.6267 6.98925 9.67731 8.05593 9.67731C9.11191 9.67731 9.97588 10.6267 9.95454 11.7893C9.95454 12.952 9.11191 13.9013 8.05593 13.9013ZM15.065 13.9013C14.0196 13.9013 13.1652 12.952 13.1652 11.7893C13.1652 10.6267 13.9983 9.67731 15.065 9.67731C16.121 9.67731 16.985 10.6267 16.9636 11.7893C16.9636 12.952 16.1317 13.9013 15.065 13.9013Z" /> </svg>
          <p>Discord sync</p>
          <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info preview-icon"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
        </div>
        <label class="switch">
          <input class="discord-input" type="checkbox">
          <span class="slider"></span>
        </label>
      </div>
      <div class="option-textbox token">
        <input type="password" id="discord-token" placeholder="Discord token..." autocomplete="off">
      </div>
    </div>
  </div>

  <script>
    const LINE_H = 40;
    const viewport = document.getElementById('lyrics-viewport');
    const track = document.getElementById('lyrics-track');

    let lines = [];
    let current = -1;

    function setLyrics(input) {
      lines = input.map(l => typeof l === 'string' ? { time: null, text: l } : l);
      track.innerHTML = '';
      lines.forEach(l => {
        const el = document.createElement('div');
        el.className = 'lyric-line';
        el.textContent = l.text;
        track.appendChild(el);
      });
      current = -1;
      setActive(0);
    }

    function setActive(i) {
      if (!lines.length) return;
      i = Math.max(0, Math.min(lines.length - 1, i));
      if (i === current) return;
      current = i;

      [...track.children].forEach((el, n) => el.classList.toggle('active', n === i));

      const center = viewport.clientHeight / 2;
      const offset = center - (i * LINE_H + LINE_H / 2);
      track.style.transform = `translateY(${offset}px)`;
    }

    function setPosition(ms) {
      let idx = 0;
      for (let n = 0; n < lines.length; n++) {
        if (lines[n].time !== null && lines[n].time <= ms) idx = n;
      }
      setActive(idx);
    }

    function setTrack(title, artists, cover) {
      document.getElementById('track-title').textContent = title;
      document.getElementById('track-artists').textContent = artists;
      if (cover) document.querySelector('.track-thumbnail').src = cover;
    }

    setLyrics([
      "Loading 1...",
      "Loading 2...",
      "Loading 3...",
      "Loading 4...",
      "Loading 5...",
      "Loading 6..."
    ]);

    setTimeout(() => {
      if (window.pywebview) return;
      let n = 0;
      setInterval(() => setActive(++n % lines.length), 2000);
    }, 300);

    window.addEventListener('resize', () => { const c = current; current = -1; setActive(c); });
  </script>
  <script>
    const DECORATORS = ["First letter", "Face emojis", "Music emojis", "Cycling arrows", "Loading symbols", "Cronologic cycling clocks"];

    const LANGS = [
      ["ar", "Arabic"], ["zh", "Chinese"], ["cs", "Czech"], ["da", "Danish"], ["nl", "Dutch"],
      ["en", "English"], ["eo", "Esperanto"], ["fil", "Filipino"], ["fi", "Finnish"], ["fr", "French"],
      ["fr-CA-u-sd-caqc", "French (CA)"], ["de", "German"], ["hi", "Hindi"], ["hu", "Hungarian"],
      ["it", "Italian"], ["ja", "Japanese"], ["kab", "Kabyle"], ["tlh", "Klingon"], ["ko", "Korean"],
      ["no", "Norwegian"], ["fa", "Persian"], ["pl", "Polish"], ["pt", "Portuguese"], ["ru", "Russian"],
      ["es", "Spanish"], ["sv", "Swedish"], ["th", "Thai"], ["tr", "Turkish"]
    ];
    const LANG_NAME = Object.fromEntries(LANGS);

    const state = {
      decorators: { enabled: false, value: null },
      censor:     { enabled: false, all: false, languages: [] },
      discord:    { enabled: false }
    };

    const $ = (sel, root = document) => root.querySelector(sel);

    function emit() {
      const api = window.pywebview && window.pywebview.api;
      if (api && api.update_settings) api.update_settings(JSON.parse(JSON.stringify(state)));
    }

    function closeAll(except) {
      document.querySelectorAll('.option-dropdown.open').forEach(d => { if (d !== except) d.classList.remove('open'); });
    }
    document.addEventListener('click', e => { if (!e.target.closest('.option-dropdown')) closeAll(); });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeAll(); });

    function bindOpen(box) {
      box.addEventListener('click', e => {
        if (e.target.closest('.dd-menu')) return;      
        const open = !box.classList.contains('open');
        closeAll(box);
        box.classList.toggle('open', open);
      });
    }

    const decBox = $('#dd-decorators'), decMenu = $('.dd-menu', decBox), decLabel = $('.dd-value', decBox);
    decMenu.innerHTML = DECORATORS.map(v => `<div class="dd-item single" data-v="${v}"><span class="mark"></span>${v}</div>`).join('');
    bindOpen(decBox);

    function pickDecorator(v) {
      state.decorators.value = v;
      decMenu.querySelectorAll('.dd-item').forEach(i => i.classList.toggle('selected', i.dataset.v === v));
      decLabel.textContent = v;
      decLabel.classList.remove('placeholder');
    }
    decMenu.addEventListener('click', e => {
      const it = e.target.closest('.dd-item');
      if (!it) return;
      pickDecorator(it.dataset.v);
      decBox.classList.remove('open');
      emit();
    });

    const cenBox = $('#dd-censor'), cenMenu = $('.dd-menu', cenBox), cenLabel = $('.dd-value', cenBox);
    cenMenu.innerHTML =
      `<div class="dd-item multi all" data-v="__all"><span class="mark"></span>ALL</div>` +
      LANGS.map(([c, n]) => `<div class="dd-item multi" data-v="${c}"><span class="mark"></span>${n}<small>${c}</small></div>`).join('');
    bindOpen(cenBox);

    const selected = new Set();

    function refreshCensor() {
      const all = selected.size === LANGS.length;
      cenMenu.querySelectorAll('.dd-item:not(.all)').forEach(i => i.classList.toggle('selected', selected.has(i.dataset.v)));
      $('.all', cenMenu).classList.toggle('selected', all);

      state.censor.all = all;
      state.censor.languages = LANGS.map(l => l[0]).filter(c => selected.has(c));

      let text;
      if (all) text = 'All languages';
      else if (selected.size === 0) text = 'Choose languages…';
      else if (selected.size <= 2) text = state.censor.languages.map(c => LANG_NAME[c]).join(', ');
      else text = selected.size + ' languages';
      cenLabel.textContent = text;
      cenLabel.classList.toggle('placeholder', selected.size === 0);
    }

    cenMenu.addEventListener('click', e => {
      const it = e.target.closest('.dd-item');
      if (!it) return;
      if (it.dataset.v === '__all') {
        if (selected.size === LANGS.length) selected.clear();
        else LANGS.forEach(l => selected.add(l[0]));
      } else if (selected.has(it.dataset.v)) selected.delete(it.dataset.v);
      else selected.add(it.dataset.v);
      refreshCensor();
      emit();
    });

    $('.decorators-input').addEventListener('change', e => { state.decorators.enabled = e.target.checked; emit(); });
    $('.censor-input').addEventListener('change',     e => { state.censor.enabled = e.target.checked; emit(); });
    $('.discord-input').addEventListener('change',    e => { state.discord.enabled = e.target.checked; emit(); });

    function applySettings(s) {
      if (s.decorators) {
        state.decorators.enabled = !!s.decorators.enabled;
        $('.decorators-input').checked = state.decorators.enabled;
        if (s.decorators.value) pickDecorator(s.decorators.value);
      }
      if (s.censor) {
        state.censor.enabled = !!s.censor.enabled;
        $('.censor-input').checked = state.censor.enabled;
        selected.clear();
        (s.censor.all ? LANGS.map(l => l[0]) : (s.censor.languages || [])).forEach(c => selected.add(c));
        refreshCensor();
      }
      if (s.discord) {
        state.discord.enabled = !!s.discord.enabled;
        $('.discord-input').checked = state.discord.enabled;
      }
    }

    const tokenInput = $('#discord-token');

    async function refreshTokenState() {
    const has = await pywebview.api.has_token();
    tokenInput.placeholder = has ? 'Token saved ••••••••' : 'Discord token...';
    }

    tokenInput.addEventListener('change', async () => {
    if (!tokenInput.value.trim()) return;
    await pywebview.api.save_token(tokenInput.value);
    tokenInput.value = '';
    refreshTokenState();
    });

    window.addEventListener('pywebviewready', refreshTokenState);
  </script>
"""

import json
from pathlib import Path
import keyring
from keyring.errors import KeyringError, PasswordDeleteError
import asyncio
import threading
import traceback
import lyrics_main

loaded = threading.Event()
stop = threading.Event()

SETTINGS_FILE = Path.home() / ".spotisync" / "settings.json"

DEFAULTS = {
    "decorators": {"enabled": False, "value": None},
    "censor":     {"enabled": False, "all": False, "languages": []},
    "discord":    {"enabled": False},
}

def load_settings():
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return {k: {**DEFAULTS[k], **data.get(k, {})} for k in DEFAULTS}
    except (FileNotFoundError, json.JSONDecodeError, AttributeError, TypeError):
        return json.loads(json.dumps(DEFAULTS))

def save_settings(s):
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=2), encoding="utf-8")
    tmp.replace(SETTINGS_FILE)

KR_SERVICE = "SpotiSync"
KR_USER = "discord_token"

class Api:
    def __init__(self):
        self._settings = load_settings()
        self._maximized = False
        self._token = self._get_token()

    def close(self):
        window.destroy()

    def minimize(self):
        window.minimize()

    def update_settings(self, s):
        self._settings = s
        save_settings(s)

    def save_token(self, token):
        token = (token or "").strip()
        if not token:
            return False
        try:
            keyring.set_password(KR_SERVICE, KR_USER, token)
            self._token = token
            return True
        except KeyringError:
            return False

    def has_token(self):
        try:
            return bool(keyring.get_password(KR_SERVICE, KR_USER))
        except KeyringError:
            return False

    def clear_token(self):
        try:
            keyring.delete_password(KR_SERVICE, KR_USER)
        except (PasswordDeleteError, KeyringError):
            pass
        self._token = None

    def _get_token(self):
        try:
            return keyring.get_password(KR_SERVICE, KR_USER)
        except KeyringError:
            return None

api = Api()
window = webview.create_window("SpotiSync", html=HTML, js_api=api,
                               width=884, height=480, frameless=True,
                               easy_drag=False)

def on_loaded():
    try:
        window.evaluate_js(f"applySettings({json.dumps(api._settings)})")
    finally:
        loaded.set()

window.events.loaded += on_loaded
window.events.closed += stop.set

async def ui(js):
    if stop.is_set():
        return
    try:
        await asyncio.to_thread(window.evaluate_js, js)
    except Exception as e:
        if not stop.is_set():
            print("evaluate_js falló:", e, "| JS:", js[:120], flush=True)

async def sync_loop():
    prev_cfg = None
    last_lyrics = None
    last_sent_idx = None
    last_idx = None

    while not stop.is_set():
        try:
            cfg = api._settings
            if cfg != prev_cfg:
                prev_cfg = cfg

            track_data, synced_lyrics, current_line_idx = await lyrics_main.run_main(cfg, api._token)
            lyric_list = list((synced_lyrics or {}).values())

            if synced_lyrics != last_lyrics:
                await ui(f"setLyrics({json.dumps(lyric_list)})")
                last_lyrics = synced_lyrics
                last_sent_idx = None

            line_idx = current_line_idx if current_line_idx is not None else (last_idx or 0)
            if lyric_list:
                line_idx = max(0, min(line_idx, len(lyric_list) - 1))
                if line_idx != last_sent_idx:
                    await ui(f"setActive({line_idx})")
                    last_sent_idx = line_idx
            last_idx = line_idx

            if track_data["name"] and track_data["artist"] and track_data["thumbnail"]:
              await ui(f"setTrack({json.dumps(track_data["name"])}, {json.dumps(track_data["artist"])}, {json.dumps(track_data["thumbnail"])})")

        except Exception:
            traceback.print_exc()

        await asyncio.sleep(0.25)


async def main():
    await asyncio.to_thread(loaded.wait, 30)
    await asyncio.gather(
        sync_loop(),
    )


def background():
    try:
        asyncio.run(main())
    except Exception:
        traceback.print_exc()


webview.start(background)