# 小米 MiMo 语音克隆 WebUI

基于小米 MiMo-V2.5-TTS API 的语音克隆 Web 应用。上传参考音频，输入文本，生成模仿参考音色的语音。

## 功能特性

- **语音克隆** - 通过 MiMo-V2.5-TTS-voiceclone 模型克隆任意音色
- **多参考音频** - 上传多个音频文件，自动拼接合并
- **精细参数控制** - 调节 temperature、top_p、seed 和批量次数
- **预设模式** - 稳定 / 均衡 / 创意 一键切换
- **情绪标签** - 在文本中插入 (开心)、(悲伤)、(愤怒) 等情绪标记
- **供应商端点** - 支持小米官方、Token Plan 端点，或自定义端点
- **记住设置** - API Key 和端点保存在浏览器本地
- **跨平台** - 支持 Windows、Linux、macOS

## 快速开始

### 方式一：Docker（推荐）

只需安装 [Docker](https://www.docker.com/get-started)，一行命令启动：

```bash
docker run -p 7860:7860 ghcr.io/tangyucheng6420/xiaomi-mimo-tts-webui:latest
```

或者使用 docker-compose：

```bash
git clone https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui.git
cd xiaomi-mimo-tts-webui
docker-compose up -d
```

浏览器打开 http://localhost:7860 即可使用。

### 方式二：Python 运行

**Windows：**
```
双击 start.bat
```

**Linux / macOS：**
```bash
chmod +x start.sh
./start.sh
```

**手动运行：**
```bash
git clone https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui.git
cd xiaomi-mimo-tts-webui
pip install -r requirements.txt
python app.py
```

### 前置条件

- Docker（方式一）或 Python 3.9+（方式二）
- [ffmpeg](https://ffmpeg.org/download.html)（Python 方式需要，Docker 已内置）
- MiMo API Key，从 [platform.xiaomimimo.com](https://platform.xiaomimimo.com) 获取

## 使用方法

1. **输入 API Key** - 从 [platform.xiaomimimo.com](https://platform.xiaomimimo.com) 获取
2. **选择端点** - 选择小米官方或 Token Plan
3. **上传参考音频** - 拖拽或点击上传（支持 mp3/wav，可多选）
4. **调节参数** - 使用预设或手动调节 temperature/top_p/seed
5. **输入文本** - 输入要合成的文本，可添加情绪标签
6. **生成** - 点击"生成语音"并下载结果

## 参数说明

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| temperature | 0 - 1.5 | 0.6 | 越低越稳定一致 |
| top_p | 0.01 - 1.0 | 0.95 | 越低越确定 |
| seed | 整数 | 随机 | 固定种子可复现相同结果 |

### 预设模式

| 模式 | Temperature | Top P | 适用场景 |
|------|-------------|-------|----------|
| 稳定模式 | 0.2 | 0.7 | 一致、可预测的输出 |
| 均衡模式 | 0.5 | 0.85 | 通用场景 |
| 创意模式 | 0.8 | 0.95 | 更有表现力、变化丰富 |

## 情绪标签

在文本中插入以下标签控制情绪和节奏：

`(开心)` `(悲伤)` `(愤怒)` `(温柔)` `(低沉)` `(叹气)` `(笑声)` `(低声)` `(哭泣)` `(语速加快)` `(突然停顿)` `(深呼吸)`

示例：`你好啊！(开心) 最近怎么样？(突然停顿) 我好想你。`

## API 供应商

| 供应商 | Base URL | 说明 |
|--------|----------|------|
| 小米官方 | `https://api.xiaomimimo.com/v1` | 小米平台直接访问 |
| Token Plan | `https://token-plan-cn.xiaomimimo.com/v1` | Token Plan 端点 |
| 自定义 | 用户输入 | 任意 OpenAI 兼容端点 |

## 项目结构

```
xiaomi-mimo-tts-webui/
├── app.py              # 主应用（Flask + 内嵌前端）
├── mimo_tts_example.py # API 调用示例
├── requirements.txt    # Python 依赖
├── Dockerfile          # Docker 镜像构建
├── docker-compose.yml  # Docker Compose 一键启动
├── start.bat           # Windows 一键启动（Python）
├── start.sh            # Linux/macOS 一键启动（Python）
├── build.py            # 打包脚本
├── LICENSE             # MIT 开源协议
└── README.md           # 本文件
```

## 技术栈

- **后端**: Python, Flask, OpenAI SDK
- **前端**: 原生 HTML/CSS/JS（单文件 SPA）
- **音频处理**: pydub（多文件拼接）
- **API**: MiMo-V2.5-TTS（OpenAI 兼容格式）

## 已知限制

- 参考音频合并后不能超过 10MB
- 仅支持 mp3 和 wav 格式
- 克隆效果取决于参考音频的质量和时长
- API 目前限时免费（截至 2026 年）

## 开源协议

[MIT License](LICENSE)

## 相关链接

- [小米 MiMo API 平台](https://platform.xiaomimimo.com)
- [MiMo TTS 文档](https://platform.xiaomimimo.com/docs/usage-guide/speech-synthesis-v2.5)
- [反馈问题](https://github.com/tangyucheng6420/xiaomi-mimo-tts-webui/issues)
