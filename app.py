"""
Xiaomi MiMo-V2.5-TTS Voice Clone WebUI (Flask)
Production-ready voice cloning web application with multi-provider support.
GitHub: https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui
"""

import base64
import io
import os
import tempfile
import atexit
from flask import Flask, render_template_string, request, send_file, jsonify
from openai import OpenAI
from pydub import AudioSegment

app = Flask(__name__)

# Track temp output files for cleanup
_temp_files = []

def _cleanup_temps():
    for f in _temp_files:
        try:
            os.unlink(f)
        except OSError:
            pass
    _temp_files.clear()

atexit.register(_cleanup_temps)

# Provider endpoints
PROVIDERS = [
    {"name": "MiMo Official", "url": "https://api.xiaomimimo.com/v1", "model": "mimo-v2.5-tts-voiceclone"},
    {"name": "Token Plan CN", "url": "https://token-plan-cn.xiaomimimo.com/v1", "model": "mimo-v2.5-tts-voiceclone"},
]

HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xiaomi MiMo TTS Voice Clone</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f0f2f5; min-height: 100vh; padding: 16px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { text-align: center; color: #1a1a1a; margin-bottom: 4px; font-size: 26px; }
        .subtitle { text-align: center; color: #888; margin-bottom: 24px; font-size: 13px; }
        .subtitle a { color: #4a90d9; text-decoration: none; }
        .subtitle a:hover { text-decoration: underline; }
        .card { background: #fff; border-radius: 12px; padding: 24px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); margin-bottom: 16px; }
        .card h3 { font-size: 15px; color: #333; margin-bottom: 16px; border-bottom: 1px solid #f0f0f0; padding-bottom: 8px; }
        .row { display: flex; gap: 16px; }
        .col { flex: 1; }
        label { display: block; font-weight: 600; margin-bottom: 5px; color: #333; font-size: 13px; }
        .hint { font-size: 11px; color: #aaa; margin-bottom: 10px; }
        input[type="text"], input[type="password"], input[type="number"], textarea, select {
            width: 100%; padding: 8px 10px; border: 1px solid #e0e0e0;
            border-radius: 6px; font-size: 13px; background: #fafafa;
        }
        input:focus, textarea:focus, select:focus { outline: none; border-color: #4a90d9; background: #fff; }
        textarea { resize: vertical; font-family: inherit; }
        .audio-upload {
            border: 2px dashed #e0e0e0; border-radius: 8px; padding: 16px;
            text-align: center; cursor: pointer; transition: all 0.2s; background: #fafafa;
        }
        .audio-upload:hover { border-color: #4a90d9; background: #f5f8fc; }
        .audio-upload input { display: none; }
        .audio-upload .icon { font-size: 28px; margin-bottom: 4px; }
        .btn {
            display: inline-block; padding: 10px 24px; background: #4a90d9;
            color: #fff; border: none; border-radius: 6px; font-size: 14px;
            font-weight: 600; cursor: pointer; width: 100%;
        }
        .btn:hover { background: #357abd; }
        .btn:disabled { background: #ccc; cursor: not-allowed; }
        .btn-sm {
            padding: 4px 10px; font-size: 11px; border-radius: 4px;
            background: #f5f5f5; color: #666; border: 1px solid #e0e0e0; cursor: pointer;
        }
        .btn-sm:hover { background: #e0e7f1; color: #4a90d9; border-color: #4a90d9; }
        .tags { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 6px; }
        .tag {
            background: #f5f5f5; padding: 3px 8px; border-radius: 10px;
            font-size: 11px; color: #666; cursor: pointer;
        }
        .tag:hover { background: #e0e7f1; color: #4a90d9; }
        .loading { display: none; text-align: center; padding: 24px; }
        .loading.show { display: block; }
        .spinner {
            border: 3px solid #f3f3f3; border-top: 3px solid #4a90d9;
            border-radius: 50%; width: 28px; height: 28px;
            animation: spin 0.8s linear infinite; margin: 0 auto 8px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .error { color: #e74c3c; text-align: center; padding: 8px; display: none; font-size: 13px; }
        .error.show { display: block; }
        .param-row { display: flex; gap: 12px; align-items: flex-end; margin-bottom: 10px; }
        .param-row .param-col { flex: 1; }
        .param-row label { margin-bottom: 3px; }
        .slider-val { font-size: 11px; color: #4a90d9; font-weight: 600; }
        input[type="range"] { width: 100%; accent-color: #4a90d9; }
        .results-grid { display: flex; flex-direction: column; gap: 10px; }
        .result-item {
            display: flex; align-items: center; gap: 12px;
            background: #f8f9fa; border-radius: 8px; padding: 12px;
        }
        .result-item audio { flex: 1; height: 36px; }
        .result-item .idx { font-weight: 700; color: #4a90d9; font-size: 14px; min-width: 24px; }
        .result-item .download-btn {
            background: none; border: 1px solid #ddd; border-radius: 4px;
            padding: 4px 10px; cursor: pointer; font-size: 12px; color: #666;
        }
        .result-item .download-btn:hover { border-color: #4a90d9; color: #4a90d9; }
        .preset-btns { display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }
        .preset-btn {
            padding: 4px 10px; border: 1px solid #e0e0e0; border-radius: 4px;
            background: #fff; cursor: pointer; font-size: 11px; color: #666;
        }
        .preset-btn:hover { border-color: #4a90d9; color: #4a90d9; }
        .preset-btn.active { border-color: #4a90d9; background: #f0f6ff; color: #4a90d9; }
        .file-list { margin-top: 8px; }
        .file-item {
            display: flex; align-items: center; gap: 8px;
            background: #f8f9fa; border-radius: 6px; padding: 8px 10px; margin-bottom: 4px;
            font-size: 12px;
        }
        .file-item .fname { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .file-item .fsize { color: #999; min-width: 60px; text-align: right; }
        .file-item .fdel {
            background: none; border: none; color: #ccc; cursor: pointer;
            font-size: 16px; padding: 0 4px;
        }
        .file-item .fdel:hover { color: #e74c3c; }
        .merge-hint { background: #fff8e1; border-radius: 6px; padding: 8px 10px; font-size: 11px; color: #b8860b; margin-top: 8px; }
        .endpoint-row { display: flex; gap: 8px; align-items: flex-end; }
        .endpoint-row .endpoint-select { flex: 2; }
        .endpoint-row .endpoint-custom { flex: 3; }
        .api-key-row { display: flex; gap: 8px; align-items: flex-end; }
        .api-key-row input { flex: 1; }
        .api-key-row .btn-sm { white-space: nowrap; height: 34px; }
        .footer { text-align: center; color: #bbb; font-size: 11px; padding: 16px 0; }
        .footer a { color: #999; text-decoration: none; }
        .footer a:hover { color: #4a90d9; }
        @media (max-width: 768px) { .row { flex-direction: column; } }
    </style>
</head>
<body>
    <div class="container">
        <h1>Xiaomi MiMo TTS Voice Clone</h1>
        <p class="subtitle">
            Multi-reference audio merge clone | Fine-grained parameter control | Batch generation
            &nbsp;|&nbsp;
            <a href="https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui" target="_blank">GitHub</a>
        </p>

        <form id="form">
            <div class="row">
                <div class="col">
                    <div class="card">
                        <h3>API Configuration</h3>
                        <label>API Provider</label>
                        <div class="endpoint-row">
                            <div class="endpoint-select">
                                <select id="endpointSelect" onchange="onEndpointChange()">
                                    <option value="0">MiMo Official</option>
                                    <option value="1">Token Plan CN</option>
                                    <option value="custom">Custom Endpoint</option>
                                </select>
                            </div>
                            <div class="endpoint-custom" id="customUrlWrap" style="display:none;">
                                <input type="text" id="customUrl" placeholder="https://your-endpoint.com/v1">
                            </div>
                        </div>
                        <div class="hint" id="endpointHint">api.xiaomimimo.com/v1</div>

                        <div style="margin-top: 14px;">
                            <label>API Key</label>
                            <div class="api-key-row">
                                <input type="password" id="apiKey" placeholder="Enter your MiMo API Key" required>
                                <button type="button" class="btn-sm" onclick="toggleKeyVisibility()" id="eyeBtn">Show</button>
                                <button type="button" class="btn-sm" onclick="clearSavedKey()">Clear</button>
                            </div>
                            <div class="hint">Key is saved locally in your browser (localStorage)</div>
                        </div>

                        <div style="margin-top: 14px;">
                            <label>Reference Audio (multiple allowed)</label>
                            <div class="audio-upload" id="dropZone">
                                <div class="icon">&#127908;</div>
                                <div style="font-size:13px;">Click or drag audio files here</div>
                                <div class="hint">Supports mp3 / wav, multiple files auto-merged</div>
                                <input type="file" id="audioFile" accept=".mp3,.wav,.wave" multiple>
                            </div>
                            <div class="file-list" id="fileList"></div>
                            <div class="merge-hint" id="mergeHint" style="display:none;">
                                Multiple files will be concatenated in order before sending
                            </div>
                        </div>

                        <div style="margin-top: 14px;">
                            <label>Output Format</label>
                            <select id="format">
                                <option value="wav">WAV (Recommended)</option>
                                <option value="pcm16">PCM16</option>
                            </select>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Parameters</h3>
                        <div class="preset-btns">
                            <span class="preset-btn active" onclick="applyPreset('stable')">Stable</span>
                            <span class="preset-btn" onclick="applyPreset('balanced')">Balanced</span>
                            <span class="preset-btn" onclick="applyPreset('creative')">Creative</span>
                        </div>

                        <div class="param-row">
                            <div class="param-col">
                                <label>temperature <span class="slider-val" id="tempVal">0.3</span></label>
                                <input type="range" id="temperature" min="0" max="1.5" step="0.05" value="0.3"
                                       oninput="document.getElementById('tempVal').textContent=this.value">
                                <div class="hint">Lower = more consistent (TTS default 0.6)</div>
                            </div>
                        </div>
                        <div class="param-row">
                            <div class="param-col">
                                <label>top_p <span class="slider-val" id="toppVal">0.8</span></label>
                                <input type="range" id="topP" min="0.01" max="1.0" step="0.01" value="0.8"
                                       oninput="document.getElementById('toppVal').textContent=this.value">
                                <div class="hint">Lower = more deterministic (default 0.95)</div>
                            </div>
                        </div>
                        <div class="param-row">
                            <div class="param-col">
                                <label>seed</label>
                                <input type="number" id="seed" placeholder="Empty = random, number = reproducible" min="0">
                                <div class="hint">Fixed seed for reproducible results</div>
                            </div>
                        </div>
                        <div class="param-row">
                            <div class="param-col">
                                <label>Batch Count</label>
                                <select id="batchCount">
                                    <option value="1">1</option>
                                    <option value="2">2</option>
                                    <option value="3" selected>3</option>
                                    <option value="5">5</option>
                                </select>
                                <div class="hint">Generate multiple and pick the best</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col">
                    <div class="card">
                        <h3>Voice Content</h3>
                        <label>Style Instruction (optional)</label>
                        <textarea id="instruction" rows="3" placeholder="Describe desired tone/style, e.g.:&#10;Speak in a gentle voice, slightly slow&#10;Mimic the speaker's tone from the reference audio"></textarea>

                        <div style="margin-top: 14px;">
                            <label>Text to Synthesize</label>
                            <textarea id="text" rows="6" placeholder="Enter text to synthesize...&#10;Use (tags) to control emotion"></textarea>
                            <div class="tags">
                                <span class="tag" onclick="insertTag(this)">(Happy)</span>
                                <span class="tag" onclick="insertTag(this)">(Sad)</span>
                                <span class="tag" onclick="insertTag(this)">(Angry)</span>
                                <span class="tag" onclick="insertTag(this)">(Gentle)</span>
                                <span class="tag" onclick="insertTag(this)">(Low voice)</span>
                                <span class="tag" onclick="insertTag(this)">(Sigh)</span>
                                <span class="tag" onclick="insertTag(this)">(Laugh)</span>
                                <span class="tag" onclick="insertTag(this)">(Whisper)</span>
                                <span class="tag" onclick="insertTag(this)">(Crying)</span>
                                <span class="tag" onclick="insertTag(this)">(Faster)</span>
                                <span class="tag" onclick="insertTag(this)">(Pause)</span>
                                <span class="tag" onclick="insertTag(this)">(Deep breath)</span>
                            </div>
                        </div>

                        <div style="margin-top: 16px;">
                            <button type="submit" class="btn" id="submitBtn">Generate Voice</button>
                        </div>
                    </div>

                    <div class="card" id="resultCard" style="display:none;">
                        <h3>Results</h3>
                        <div class="results-grid" id="resultsGrid"></div>
                    </div>
                </div>
            </div>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div id="loadingText">Generating voice (1/1)...</div>
        </div>
        <div class="error" id="errorMsg"></div>

        <div class="footer">
            <a href="https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui" target="_blank">Xiaomi MiMo TTS Voice Clone</a>
            &nbsp;&middot;&nbsp; Powered by MiMo-V2.5-TTS
            &nbsp;&middot;&nbsp; <a href="https://platform.xiaomimimo.com" target="_blank">Get API Key</a>
        </div>
    </div>

    <script>
        // === Provider endpoints ===
        const providers = PROVIDERS_JSON;

        // === localStorage helpers ===
        const LS_KEY_APIKEY = 'mimo_tts_apikey';
        const LS_KEY_ENDPOINT = 'mimo_tts_endpoint';
        const LS_KEY_CUSTOM_URL = 'mimo_tts_custom_url';

        function loadSaved() {
            const savedKey = localStorage.getItem(LS_KEY_APIKEY);
            const savedEp = localStorage.getItem(LS_KEY_ENDPOINT);
            const savedUrl = localStorage.getItem(LS_KEY_CUSTOM_URL);
            if (savedKey) document.getElementById('apiKey').value = savedKey;
            if (savedEp !== null) {
                document.getElementById('endpointSelect').value = savedEp;
                onEndpointChange();
            }
            if (savedUrl) document.getElementById('customUrl').value = savedUrl;
        }

        function saveSettings() {
            const key = document.getElementById('apiKey').value;
            const ep = document.getElementById('endpointSelect').value;
            const url = document.getElementById('customUrl').value;
            if (key) localStorage.setItem(LS_KEY_APIKEY, key);
            localStorage.setItem(LS_KEY_ENDPOINT, ep);
            if (url) localStorage.setItem(LS_KEY_CUSTOM_URL, url);
        }

        function clearSavedKey() {
            localStorage.removeItem(LS_KEY_APIKEY);
            document.getElementById('apiKey').value = '';
        }

        function toggleKeyVisibility() {
            const inp = document.getElementById('apiKey');
            const btn = document.getElementById('eyeBtn');
            if (inp.type === 'password') { inp.type = 'text'; btn.textContent = 'Hide'; }
            else { inp.type = 'password'; btn.textContent = 'Show'; }
        }

        function getBaseUrl() {
            const sel = document.getElementById('endpointSelect').value;
            if (sel === 'custom') return document.getElementById('customUrl').value.trim();
            return providers[parseInt(sel)].url;
        }

        function onEndpointChange() {
            const sel = document.getElementById('endpointSelect').value;
            const hint = document.getElementById('endpointHint');
            const wrap = document.getElementById('customUrlWrap');
            if (sel === 'custom') {
                wrap.style.display = 'block';
                hint.textContent = 'Enter your custom base URL';
            } else {
                wrap.style.display = 'none';
                hint.textContent = providers[parseInt(sel)].url;
            }
            saveSettings();
        }

        // === Audio file management ===
        let uploadedFiles = [];
        const audioInput = document.getElementById('audioFile');
        const dropZone = document.getElementById('dropZone');
        const fileList = document.getElementById('fileList');
        const mergeHint = document.getElementById('mergeHint');

        const presets = {
            stable:   { temp: 0.2, topp: 0.7 },
            balanced: { temp: 0.5, topp: 0.85 },
            creative: { temp: 0.8, topp: 0.95 },
        };

        function applyPreset(name) {
            const p = presets[name];
            document.getElementById('temperature').value = p.temp;
            document.getElementById('topP').value = p.topp;
            document.getElementById('tempVal').textContent = p.temp;
            document.getElementById('toppVal').textContent = p.topp;
            document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
        }

        audioInput.addEventListener('change', function() {
            addFiles(this.files);
            this.value = '';
        });

        dropZone.addEventListener('click', () => audioInput.click());
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = '#4a90d9'; });
        dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = '#e0e0e0'; });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault(); dropZone.style.borderColor = '#e0e0e0';
            addFiles(e.dataTransfer.files);
        });

        function addFiles(files) {
            for (const f of files) {
                const ext = f.name.split('.').pop().toLowerCase();
                if (!['mp3','wav','wave'].includes(ext)) continue;
                if (uploadedFiles.some(u => u.name === f.name && u.size === f.size)) continue;
                uploadedFiles.push(f);
            }
            renderFileList();
        }

        function removeFile(idx) {
            uploadedFiles.splice(idx, 1);
            renderFileList();
        }

        function renderFileList() {
            fileList.innerHTML = '';
            mergeHint.style.display = uploadedFiles.length > 1 ? 'block' : 'none';
            uploadedFiles.forEach((f, i) => {
                const mb = (f.size / 1024 / 1024).toFixed(2);
                const div = document.createElement('div');
                div.className = 'file-item';
                div.innerHTML = `
                    <span style="color:#4a90d9;font-weight:600;">${i+1}</span>
                    <span class="fname">${f.name}</span>
                    <span class="fsize">${mb} MB</span>
                    <button class="fdel" onclick="removeFile(${i})" title="Remove">&times;</button>
                `;
                fileList.appendChild(div);
            });
        }

        function insertTag(el) {
            const textarea = document.getElementById('text');
            const tag = el.textContent;
            const s = textarea.selectionStart, e = textarea.selectionEnd;
            textarea.value = textarea.value.substring(0, s) + tag + ' ' + textarea.value.substring(e);
            textarea.focus();
            textarea.selectionStart = textarea.selectionEnd = s + tag.length + 1;
        }

        // === Form submit ===
        document.getElementById('form').addEventListener('submit', async function(e) {
            e.preventDefault();
            const apiKey = document.getElementById('apiKey').value;
            const instruction = document.getElementById('instruction').value;
            const text = document.getElementById('text').value;
            const fmt = document.getElementById('format').value;
            const temp = document.getElementById('temperature').value;
            const topP = document.getElementById('topP').value;
            const seed = document.getElementById('seed').value;
            const batch = parseInt(document.getElementById('batchCount').value);
            const baseUrl = getBaseUrl();

            if (!apiKey) { showError('Please enter your API Key'); return; }
            if (!baseUrl) { showError('Please select or enter an API endpoint'); return; }
            if (uploadedFiles.length === 0) { showError('Please upload at least one reference audio'); return; }
            if (!text.trim()) { showError('Please enter text to synthesize'); return; }

            saveSettings();
            showLoading(true); hideError();
            document.getElementById('resultCard').style.display = 'none';
            document.getElementById('resultsGrid').innerHTML = '';

            const results = [];
            for (let i = 0; i < batch; i++) {
                document.getElementById('loadingText').textContent = `Generating voice (${i+1}/${batch})...`;
                const fd = new FormData();
                fd.append('api_key', apiKey);
                fd.append('base_url', baseUrl);
                fd.append('instruction', instruction);
                fd.append('text', text);
                fd.append('format', fmt);
                fd.append('temperature', temp);
                fd.append('top_p', topP);
                if (seed) fd.append('seed', seed);
                uploadedFiles.forEach(f => fd.append('audio', f));

                try {
                    const resp = await fetch('/api/clone', { method: 'POST', body: fd });
                    if (!resp.ok) { const err = await resp.json(); throw new Error(err.error); }
                    results.push(URL.createObjectURL(await resp.blob()));
                } catch (err) {
                    showError(`Batch ${i+1} failed: ${err.message}`); break;
                }
            }

            if (results.length > 0) {
                const grid = document.getElementById('resultsGrid');
                results.forEach((url, idx) => {
                    const d = document.createElement('div');
                    d.className = 'result-item';
                    d.innerHTML = `<span class="idx">#${idx+1}</span><audio controls src="${url}"></audio><a href="${url}" download="clone_${idx+1}.wav" class="download-btn">Download</a>`;
                    grid.appendChild(d);
                });
                document.getElementById('resultCard').style.display = 'block';
            }
            showLoading(false);
        });

        function showLoading(v) { document.getElementById('loading').classList.toggle('show', v); document.getElementById('submitBtn').disabled = v; }
        function showError(m) { const el = document.getElementById('errorMsg'); el.textContent = m; el.classList.add('show'); }
        function hideError() { document.getElementById('errorMsg').classList.remove('show'); }

        // === Init ===
        document.addEventListener('DOMContentLoaded', loadSaved);
    </script>
</body>
</html>
"""

# Inject provider data into HTML
import json as _json
HTML = HTML.replace("PROVIDERS_JSON", _json.dumps(PROVIDERS, ensure_ascii=False))


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/clone", methods=["POST"])
def api_clone():
    api_key = request.form.get("api_key", "").strip()
    base_url = request.form.get("base_url", "").strip()
    instruction = request.form.get("instruction", "").strip()
    text = request.form.get("text", "").strip()
    output_format = request.form.get("format", "wav")
    temperature = float(request.form.get("temperature", 0.6))
    top_p = float(request.form.get("top_p", 0.95))
    seed = request.form.get("seed", "").strip()

    if not api_key:
        return jsonify({"error": "API Key is required"}), 400
    if not base_url:
        return jsonify({"error": "API endpoint is required"}), 400
    if not text:
        return jsonify({"error": "Text to synthesize is required"}), 400

    audio_files = request.files.getlist("audio")
    if not audio_files or not audio_files[0].filename:
        return jsonify({"error": "Please upload at least one reference audio"}), 400

    tmp_files = []
    tmp_out = None
    try:
        # Save uploaded audio files
        for af in audio_files:
            ext = os.path.splitext(af.filename)[1].lower()
            if ext not in (".mp3", ".wav", ".wave"):
                return jsonify({"error": f"Unsupported format: {af.filename}"}), 400
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            af.save(tmp.name)
            tmp.close()
            tmp_files.append(tmp.name)

        # Concatenate multiple audio files
        if len(tmp_files) == 1:
            with open(tmp_files[0], "rb") as f:
                voice_bytes = f.read()
            ext = os.path.splitext(tmp_files[0])[1].lower()
            mime_type = "audio/wav" if ext in (".wav", ".wave") else "audio/mpeg"
        else:
            combined = AudioSegment.empty()
            for path in tmp_files:
                seg = AudioSegment.from_file(path)
                combined += seg
            buf = io.BytesIO()
            combined.export(buf, format="wav")
            voice_bytes = buf.getvalue()
            mime_type = "audio/wav"

        size_mb = len(voice_bytes) / (1024 * 1024)
        if size_mb > 10:
            return jsonify({"error": f"Merged audio too large ({size_mb:.1f}MB), max 10MB. Reduce files or duration."}), 400

        voice_b64 = base64.b64encode(voice_bytes).decode("utf-8")

        client = OpenAI(api_key=api_key, base_url=base_url)

        messages = [
            {"role": "user", "content": instruction},
            {"role": "assistant", "content": text},
        ]

        kwargs = {
            "model": "mimo-v2.5-tts-voiceclone",
            "messages": messages,
            "audio": {"format": output_format, "voice": f"data:{mime_type};base64,{voice_b64}"},
            "temperature": temperature,
            "top_p": top_p,
        }
        if seed:
            kwargs["seed"] = int(seed)

        completion = client.chat.completions.create(**kwargs)
        audio_bytes = base64.b64decode(completion.choices[0].message.audio.data)

        out_ext = ".wav" if output_format == "wav" else ".pcm"
        tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=out_ext, prefix="mimo_clone_")
        tmp_out.write(audio_bytes)
        tmp_out.close()
        _temp_files.append(tmp_out.name)

        return send_file(tmp_out.name, mimetype="audio/wav", as_attachment=True, download_name=f"clone{out_ext}")

    except Exception as e:
        msg = str(e)
        if "401" in msg or "Unauthorized" in msg.lower():
            return jsonify({"error": "Invalid API Key. Please check your key at platform.xiaomimimo.com"}), 401
        if "429" in msg or "rate" in msg.lower():
            return jsonify({"error": "Rate limited. Please wait and try again."}), 429
        if "timeout" in msg.lower() or "connect" in msg.lower():
            return jsonify({"error": f"Network error: {msg}. Check your connection and endpoint URL."}), 502
        return jsonify({"error": msg}), 500
    finally:
        for f in tmp_files:
            try:
                os.unlink(f)
            except OSError:
                pass


if __name__ == "__main__":
    print("=" * 50)
    print("  Xiaomi MiMo TTS Voice Clone")
    print("  http://localhost:7860")
    print("=" * 50)
    app.run(host="0.0.0.0", port=7860, debug=False)
