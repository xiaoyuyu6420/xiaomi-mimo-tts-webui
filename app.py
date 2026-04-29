"""
小米 MiMo-V2.5-TTS 语音克隆 WebUI (Flask)
支持多参考音频上传、精细参数控制、批量生成、多供应商端点
生产环境：SEO / 限流 / 分析 / 安全头 / 管理员认证
"""

import base64
import io
import os
import time
import tempfile
import atexit
import threading
import json as _json
from collections import defaultdict
from functools import wraps

from flask import Flask, render_template_string, request, send_file, jsonify, Response
from openai import OpenAI
from pydub import AudioSegment

# 环境变量
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())

# ============ 配置 ============
ADMIN_USER = os.environ.get("ADMIN_USER", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "")
GA_ID = os.environ.get("GA_ID", "")
MAX_FILES = int(os.environ.get("MAX_FILES", "5"))
MAX_FILE_SIZE_MB = int(os.environ.get("MAX_FILE_SIZE_MB", "5"))
MAX_TOTAL_SIZE_MB = int(os.environ.get("MAX_TOTAL_SIZE_MB", "10"))
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", "10"))  # 每分钟请求数

# ============ 安全头 ============
@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# ============ 简易限流 ============
_rate_lock = threading.Lock()
_rate_data = defaultdict(list)

def _check_rate_limit(ip):
    now = time.time()
    with _rate_lock:
        _rate_data[ip] = [t for t in _rate_data[ip] if now - t < 60]
        if len(_rate_data[ip]) >= RATE_LIMIT:
            return False
        _rate_data[ip].append(now)
    return True

@app.before_request
def rate_limit_check():
    if request.path.startswith("/api/"):
        if not _check_rate_limit(request.remote_addr):
            return jsonify({"error": "请求过于频繁，请稍后再试"}), 429

# ============ 管理员认证 ============
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not ADMIN_USER:
            return jsonify({"error": "管理员未配置"}), 403
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
            return Response("需要管理员认证", 401, {"WWW-Authenticate": 'Basic realm="Admin"'})
        return f(*args, **kwargs)
    return decorated

# ============ 临时文件清理 ============
_temp_files = []

def _cleanup_temps():
    for f in _temp_files:
        try:
            os.unlink(f)
        except OSError:
            pass
    _temp_files.clear()

atexit.register(_cleanup_temps)

# ============ 统计 ============
_stats = {"total_requests": 0, "total_errors": 0, "start_time": time.time()}

# ============ 供应商端点 ============
PROVIDERS = [
    {"name": "小米官方", "url": "https://api.xiaomimimo.com/v1"},
    {"name": "Token Plan", "url": "https://token-plan-cn.xiaomimimo.com/v1"},
]

# ============ HTML ============
GA_SCRIPT = """
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID_PLACEHOLDER"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_ID_PLACEHOLDER');
</script>
""" if GA_ID else ""

HTML = """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>小米 MiMo 语音克隆 - AI 语音克隆在线工具</title>
    <meta name="description" content="基于小米 MiMo-V2.5-TTS 的在线语音克隆工具。上传参考音频，输入文本，一键生成克隆语音。支持多参考音频、精细参数控制、批量生成。">
    <meta name="keywords" content="语音克隆, AI 语音, MiMo TTS, 小米语音合成, 声音克隆, text to speech, voice clone">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="https://mimo-tts.example.com/">

    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="小米 MiMo 语音克隆">
    <meta property="og:description" content="基于小米 MiMo-V2.5-TTS 的在线语音克隆工具。上传音频，输入文本，一键克隆。">
    <meta property="og:url" content="https://mimo-tts.example.com/">
    <meta property="og:site_name" content="MiMo Voice Clone">
    <meta property="og:locale" content="zh_CN">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="小米 MiMo 语音克隆">
    <meta name="twitter:description" content="基于小米 MiMo-V2.5-TTS 的在线语音克隆工具">

    GA_SCRIPT_PLACEHOLDER

    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif; background: #f0f2f5; min-height: 100vh; padding: 16px; }
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
        .audio-upload.dragover { border-color: #4a90d9; background: #e8f0fe; }
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
        .file-item .ferror { color: #e74c3c; font-size: 11px; }
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

    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "WebApplication",
      "name": "小米 MiMo 语音克隆",
      "description": "基于小米 MiMo-V2.5-TTS 的在线语音克隆工具",
      "applicationCategory": "MultimediaApplication",
      "operatingSystem": "Any",
      "offers": { "@type": "Offer", "price": "0", "priceCurrency": "CNY" }
    }
    </script>
</head>
<body>
    <div class="container">
        <h1>小米 MiMo 语音克隆</h1>
        <p class="subtitle">
            多段参考音频合并克隆 | 精细参数控制 | 批量生成
            &nbsp;|&nbsp;
            <a href="https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui" target="_blank" rel="noopener">GitHub</a>
        </p>

        <form id="form" novalidate>
            <div class="row">
                <div class="col">
                    <div class="card">
                        <h3>API 配置</h3>
                        <label>API 供应商</label>
                        <div class="endpoint-row">
                            <div class="endpoint-select">
                                <select id="endpointSelect" onchange="onEndpointChange()">
                                    <option value="0">小米官方</option>
                                    <option value="1">Token Plan</option>
                                    <option value="custom">自定义端点</option>
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
                                <input type="password" id="apiKey" placeholder="输入你的 MiMo API Key" autocomplete="off">
                                <button type="button" class="btn-sm" onclick="toggleKeyVisibility()" id="eyeBtn">显示</button>
                                <button type="button" class="btn-sm" onclick="clearSavedKey()">清除</button>
                            </div>
                            <div class="hint">Key 保存在浏览器本地，不会上传到服务器</div>
                        </div>

                        <div style="margin-top: 14px;">
                            <label>参考音频（最多 MAX_FILES_PLACEHOLDER 个）</label>
                            <div class="audio-upload" id="dropZone">
                                <div class="icon">&#127908;</div>
                                <div style="font-size:13px;">点击选择或拖拽音频文件到此处</div>
                                <div class="hint">支持 mp3 / wav，可多选，自动拼接 | 单文件最大 MAX_FILE_SIZE_PLACEHOLDER MB</div>
                                <input type="file" id="audioFile" accept=".mp3,.wav,.wave" multiple>
                            </div>
                            <div class="file-list" id="fileList"></div>
                            <div class="merge-hint" id="mergeHint" style="display:none;">
                                多个文件将按顺序拼接为一段完整音频后发送
                            </div>
                        </div>

                        <div style="margin-top: 14px;">
                            <label>输出格式</label>
                            <select id="format">
                                <option value="wav">WAV (推荐)</option>
                                <option value="pcm16">PCM16</option>
                            </select>
                        </div>
                    </div>

                    <div class="card">
                        <h3>参数调节</h3>
                        <div class="preset-btns">
                            <span class="preset-btn active" onclick="applyPreset('stable')">稳定模式</span>
                            <span class="preset-btn" onclick="applyPreset('balanced')">均衡模式</span>
                            <span class="preset-btn" onclick="applyPreset('creative')">创意模式</span>
                        </div>

                        <div class="param-row">
                            <div class="param-col">
                                <label>temperature <span class="slider-val" id="tempVal">0.3</span></label>
                                <input type="range" id="temperature" min="0" max="1.5" step="0.05" value="0.3"
                                       oninput="document.getElementById('tempVal').textContent=this.value">
                                <div class="hint">越低越稳定一致 (TTS 默认 0.6)</div>
                            </div>
                        </div>
                        <div class="param-row">
                            <div class="param-col">
                                <label>top_p <span class="slider-val" id="toppVal">0.8</span></label>
                                <input type="range" id="topP" min="0.01" max="1.0" step="0.01" value="0.8"
                                       oninput="document.getElementById('toppVal').textContent=this.value">
                                <div class="hint">越低越确定 (默认 0.95)</div>
                            </div>
                        </div>
                        <div class="param-row">
                            <div class="param-col">
                                <label>seed (随机种子)</label>
                                <input type="number" id="seed" placeholder="留空=随机，填数字=可复现" min="0">
                                <div class="hint">固定种子可复现相同结果</div>
                            </div>
                        </div>
                        <div class="param-row">
                            <div class="param-col">
                                <label>批量生成次数</label>
                                <select id="batchCount">
                                    <option value="1">1 次</option>
                                    <option value="2">2 次</option>
                                    <option value="3" selected>3 次</option>
                                    <option value="5">5 次</option>
                                </select>
                                <div class="hint">多生成几次挑最好的</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="col">
                    <div class="card">
                        <h3>语音内容</h3>
                        <label>风格指令（可选）</label>
                        <textarea id="instruction" rows="3" placeholder="描述想要的语气风格，如：&#10;用温柔的语气说话，语速稍慢&#10;模仿参考音频中说话人的语气"></textarea>

                        <div style="margin-top: 14px;">
                            <label>要合成的文本</label>
                            <textarea id="text" rows="6" placeholder="输入要合成的文本...&#10;可以用 (标签) 控制情绪"></textarea>
                            <div class="tags">
                                <span class="tag" onclick="insertTag(this)">(开心)</span>
                                <span class="tag" onclick="insertTag(this)">(悲伤)</span>
                                <span class="tag" onclick="insertTag(this)">(愤怒)</span>
                                <span class="tag" onclick="insertTag(this)">(温柔)</span>
                                <span class="tag" onclick="insertTag(this)">(低沉)</span>
                                <span class="tag" onclick="insertTag(this)">(叹气)</span>
                                <span class="tag" onclick="insertTag(this)">(笑声)</span>
                                <span class="tag" onclick="insertTag(this)">(低声)</span>
                                <span class="tag" onclick="insertTag(this)">(哭泣)</span>
                                <span class="tag" onclick="insertTag(this)">(语速加快)</span>
                                <span class="tag" onclick="insertTag(this)">(突然停顿)</span>
                                <span class="tag" onclick="insertTag(this)">(深呼吸)</span>
                            </div>
                        </div>

                        <div style="margin-top: 16px;">
                            <button type="submit" class="btn" id="submitBtn">生成语音</button>
                        </div>
                    </div>

                    <div class="card" id="resultCard" style="display:none;">
                        <h3>生成结果</h3>
                        <div class="results-grid" id="resultsGrid"></div>
                    </div>
                </div>
            </div>
        </form>

        <div class="loading" id="loading">
            <div class="spinner"></div>
            <div id="loadingText">正在生成语音 (1/1)...</div>
        </div>
        <div class="error" id="errorMsg"></div>

        <div class="footer">
            <a href="https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui" target="_blank" rel="noopener">Xiaomi MiMo TTS Voice Clone</a>
            &nbsp;&middot;&nbsp; 基于 MiMo-V2.5-TTS
            &nbsp;&middot;&nbsp; <a href="https://platform.xiaomimimo.com" target="_blank" rel="noopener">获取 API Key</a>
        </div>
    </div>

    <script>
        const providers = PROVIDERS_JSON;
        const MAX_FILES = MAX_FILES_JS;
        const MAX_FILE_SIZE = MAX_FILE_SIZE_JS * 1024 * 1024;

        // === localStorage 持久化 ===
        const LS = {
            APIKEY: 'mimo_tts_apikey',
            ENDPOINT: 'mimo_tts_endpoint',
            CUSTOM_URL: 'mimo_tts_custom_url',
            TEMPERATURE: 'mimo_tts_temperature',
            TOPP: 'mimo_tts_topp',
            BATCH: 'mimo_tts_batch',
            FORMAT: 'mimo_tts_format',
        };

        function loadSaved() {
            const k = localStorage.getItem(LS.APIKEY);
            if (k) document.getElementById('apiKey').value = k;

            const ep = localStorage.getItem(LS.ENDPOINT);
            if (ep !== null) { document.getElementById('endpointSelect').value = ep; onEndpointChange(); }

            const cu = localStorage.getItem(LS.CUSTOM_URL);
            if (cu) document.getElementById('customUrl').value = cu;

            const t = localStorage.getItem(LS.TEMPERATURE);
            if (t) { document.getElementById('temperature').value = t; document.getElementById('tempVal').textContent = t; }

            const tp = localStorage.getItem(LS.TOPP);
            if (tp) { document.getElementById('topP').value = tp; document.getElementById('toppVal').textContent = tp; }

            const b = localStorage.getItem(LS.BATCH);
            if (b) document.getElementById('batchCount').value = b;

            const f = localStorage.getItem(LS.FORMAT);
            if (f) document.getElementById('format').value = f;
        }

        function saveSettings() {
            const pairs = [
                [LS.APIKEY, document.getElementById('apiKey').value],
                [LS.ENDPOINT, document.getElementById('endpointSelect').value],
                [LS.CUSTOM_URL, document.getElementById('customUrl').value],
                [LS.TEMPERATURE, document.getElementById('temperature').value],
                [LS.TOPP, document.getElementById('topP').value],
                [LS.BATCH, document.getElementById('batchCount').value],
                [LS.FORMAT, document.getElementById('format').value],
            ];
            for (const [k, v] of pairs) {
                if (v) localStorage.setItem(k, v);
                else localStorage.removeItem(k);
            }
        }

        function clearSavedKey() {
            localStorage.removeItem(LS.APIKEY);
            document.getElementById('apiKey').value = '';
        }

        function toggleKeyVisibility() {
            const inp = document.getElementById('apiKey');
            const btn = document.getElementById('eyeBtn');
            if (inp.type === 'password') { inp.type = 'text'; btn.textContent = '隐藏'; }
            else { inp.type = 'password'; btn.textContent = '显示'; }
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
                hint.textContent = '请输入自定义 base URL';
            } else {
                wrap.style.display = 'none';
                hint.textContent = providers[parseInt(sel)].url;
            }
            saveSettings();
        }

        // === 音频文件管理 ===
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
            saveSettings();
        }

        audioInput.addEventListener('change', function() { addFiles(this.files); this.value = ''; });
        dropZone.addEventListener('click', () => audioInput.click());
        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault(); dropZone.classList.remove('dragover');
            addFiles(e.dataTransfer.files);
        });

        function addFiles(files) {
            for (const f of files) {
                if (uploadedFiles.length >= MAX_FILES) {
                    showError('最多上传 ' + MAX_FILES + ' 个文件'); break;
                }
                const ext = f.name.split('.').pop().toLowerCase();
                if (!['mp3','wav','wave'].includes(ext)) continue;
                if (f.size > MAX_FILE_SIZE) {
                    showError(f.name + ' 超过 ' + MAX_FILE_SIZE_JS + ' MB 限制'); continue;
                }
                if (uploadedFiles.some(u => u.name === f.name && u.size === f.size)) continue;
                uploadedFiles.push(f);
            }
            renderFileList();
        }

        function removeFile(idx) { uploadedFiles.splice(idx, 1); renderFileList(); }

        function renderFileList() {
            fileList.innerHTML = '';
            mergeHint.style.display = uploadedFiles.length > 1 ? 'block' : 'none';
            let totalSize = 0;
            uploadedFiles.forEach((f, i) => {
                totalSize += f.size;
                const mb = (f.size / 1024 / 1024).toFixed(2);
                const div = document.createElement('div');
                div.className = 'file-item';
                div.innerHTML = `
                    <span style="color:#4a90d9;font-weight:600;">${i+1}</span>
                    <span class="fname">${f.name}</span>
                    <span class="fsize">${mb} MB</span>
                    <button class="fdel" onclick="removeFile(${i})" title="移除">&times;</button>
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

        // === 表单提交 ===
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

            if (!apiKey) { showError('请填写 API Key'); return; }
            if (!baseUrl) { showError('请选择或输入 API 端点'); return; }
            if (uploadedFiles.length === 0) { showError('请上传至少一个参考音频'); return; }
            if (!text.trim()) { showError('请输入要合成的文本'); return; }

            saveSettings();
            showLoading(true); hideError();
            document.getElementById('resultCard').style.display = 'none';
            document.getElementById('resultsGrid').innerHTML = '';

            const results = [];
            for (let i = 0; i < batch; i++) {
                document.getElementById('loadingText').textContent = `正在生成语音 (${i+1}/${batch})...`;
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
                    showError(`第 ${i+1} 次失败: ${err.message}`); break;
                }
            }

            if (results.length > 0) {
                const grid = document.getElementById('resultsGrid');
                results.forEach((url, idx) => {
                    const d = document.createElement('div');
                    d.className = 'result-item';
                    d.innerHTML = `<span class="idx">#${idx+1}</span><audio controls src="${url}"></audio><a href="${url}" download="clone_${idx+1}.wav" class="download-btn">下载</a>`;
                    grid.appendChild(d);
                });
                document.getElementById('resultCard').style.display = 'block';
            }
            showLoading(false);
        });

        function showLoading(v) { document.getElementById('loading').classList.toggle('show', v); document.getElementById('submitBtn').disabled = v; }
        function showError(m) { const el = document.getElementById('errorMsg'); el.textContent = m; el.classList.add('show'); }
        function hideError() { document.getElementById('errorMsg').classList.remove('show'); }

        document.addEventListener('DOMContentLoaded', loadSaved);
    </script>
</body>
</html>
"""

# 模板注入
HTML = HTML.replace("PROVIDERS_JSON", _json.dumps(PROVIDERS, ensure_ascii=False))
HTML = HTML.replace("MAX_FILES_PLACEHOLDER", str(MAX_FILES))
HTML = HTML.replace("MAX_FILE_SIZE_PLACEHOLDER", str(MAX_FILE_SIZE_MB))
HTML = HTML.replace("MAX_FILES_JS", str(MAX_FILES))
HTML = HTML.replace("MAX_FILE_SIZE_JS", str(MAX_FILE_SIZE_MB))
if GA_ID:
    HTML = HTML.replace("GA_SCRIPT_PLACEHOLDER", GA_SCRIPT.replace("GA_ID_PLACEHOLDER", GA_ID))
else:
    HTML = HTML.replace("GA_SCRIPT_PLACEHOLDER", "")


@app.route("/")
def index():
    return render_template_string(HTML)


# ============ 管理后台 ============
@app.route("/admin/stats")
@admin_required
def admin_stats():
    uptime = int(time.time() - _stats["start_time"])
    hours, rem = divmod(uptime, 3600)
    mins, secs = divmod(rem, 60)
    return jsonify({
        "uptime": f"{hours}h {mins}m {secs}s",
        "total_requests": _stats["total_requests"],
        "total_errors": _stats["total_errors"],
        "rate_limit": f"{RATE_LIMIT}/min",
        "max_files": MAX_FILES,
        "max_file_size": f"{MAX_FILE_SIZE_MB}MB",
        "ga_enabled": bool(GA_ID),
    })


# ============ API ============
@app.route("/api/clone", methods=["POST"])
def api_clone():
    _stats["total_requests"] += 1

    api_key = request.form.get("api_key", "").strip()
    base_url = request.form.get("base_url", "").strip()
    instruction = request.form.get("instruction", "").strip()
    text = request.form.get("text", "").strip()
    output_format = request.form.get("format", "wav")
    temperature = float(request.form.get("temperature", 0.6))
    top_p = float(request.form.get("top_p", 0.95))
    seed = request.form.get("seed", "").strip()

    # 参数校验
    if not api_key:
        return jsonify({"error": "请填写 API Key"}), 400
    if not base_url:
        return jsonify({"error": "请选择或输入 API 端点"}), 400
    if not text:
        return jsonify({"error": "请输入要合成的文本"}), 400
    if len(text) > 5000:
        return jsonify({"error": "文本过长，最多 5000 字"}), 400
    if not (0 <= temperature <= 1.5):
        return jsonify({"error": "temperature 范围 0-1.5"}), 400
    if not (0.01 <= top_p <= 1.0):
        return jsonify({"error": "top_p 范围 0.01-1.0"}), 400

    audio_files = request.files.getlist("audio")
    if not audio_files or not audio_files[0].filename:
        return jsonify({"error": "请上传参考音频"}), 400
    if len(audio_files) > MAX_FILES:
        return jsonify({"error": f"最多上传 {MAX_FILES} 个文件"}), 400

    tmp_files = []
    tmp_out = None
    try:
        for af in audio_files:
            ext = os.path.splitext(af.filename)[1].lower()
            if ext not in (".mp3", ".wav", ".wave"):
                return jsonify({"error": f"不支持的格式: {af.filename}"}), 400
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            af.save(tmp.name)
            tmp.close()
            size = os.path.getsize(tmp.name)
            if size > MAX_FILE_SIZE_MB * 1024 * 1024:
                os.unlink(tmp.name)
                return jsonify({"error": f"文件 {af.filename} 超过 {MAX_FILE_SIZE_MB}MB 限制"}), 400
            tmp_files.append(tmp.name)

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
        if size_mb > MAX_TOTAL_SIZE_MB:
            return jsonify({"error": f"拼接后音频过大 ({size_mb:.1f}MB)，最大 {MAX_TOTAL_SIZE_MB}MB"}), 400

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
        _stats["total_errors"] += 1
        msg = str(e)
        if "401" in msg or "Unauthorized" in msg.lower():
            return jsonify({"error": "API Key 无效，请检查你的 Key"}), 401
        if "429" in msg or "rate" in msg.lower():
            return jsonify({"error": "请求频率过高，请稍后再试"}), 429
        if "timeout" in msg.lower() or "connect" in msg.lower():
            return jsonify({"error": f"网络错误，请检查网络和端点地址"}), 502
        return jsonify({"error": msg}), 500
    finally:
        for f in tmp_files:
            try:
                os.unlink(f)
            except OSError:
                pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "7860"))
    print("=" * 50)
    print("  小米 MiMo 语音克隆")
    print(f"  http://localhost:{port}")
    if ADMIN_USER:
        print(f"  管理后台: http://localhost:{port}/admin/stats")
    if GA_ID:
        print(f"  Google Analytics: {GA_ID}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=port, debug=False)
