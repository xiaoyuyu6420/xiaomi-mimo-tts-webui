"""
小米 MiMo-V2.5-TTS 调用示例
API 文档: https://platform.xiaomimimo.com/docs/usage-guide/speech-synthesis-v2.5
目前限时免费，需要先在 https://platform.xiaomimimo.com 注册获取 API Key
"""

import base64
import os
from openai import OpenAI

# ============ 配置 ============
# 设置环境变量 MIMO_API_KEY，或在此处直接填写
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "your-api-key-here")

client = OpenAI(
    api_key=MIMO_API_KEY,
    base_url="https://api.xiaomimimo.com/v1",
)

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def example_builtin_voice():
    """
    示例1: 使用内置音色合成语音
    - 模型: mimo-v2.5-tts
    - user message: 风格指令（自然语言描述想要的语气、情绪等）
    - assistant message: 要合成的文本
    - audio.voice: 内置音色 ID
    """
    print("=== 示例1: 内置音色 ===")

    completion = client.chat.completions.create(
        model="mimo-v2.5-tts",
        messages=[
            {
                "role": "user",
                "content": "用温柔慈祥的语气，像个老奶奶在给孙子讲故事，语速稍慢，声音温暖。"
            },
            {
                "role": "assistant",
                "content": "从前啊，有座山，山里有座庙，庙里住着一个老和尚和一个小和尚。"
                "老和尚对小和尚说：从前啊，有座山……"
            }
        ],
        audio={
            "format": "wav",
            "voice": "冰糖"  # 内置音色: 冰糖/茉莉/苏打/白桦/Mia/Chloe/Milo/Dean
        }
    )

    message = completion.choices[0].message
    audio_bytes = base64.b64decode(message.audio.data)
    output_path = os.path.join(OUTPUT_DIR, "builtin_voice.wav")
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f"音频已保存到: {output_path}")


def example_audio_tag():
    """
    示例2: 使用音频标签精细控制
    - 在 assistant message 中用 (标签) 控制情绪和节奏
    - 标签支持中英文，可用 ()、（）或 []
    """
    print("=== 示例2: 音频标签控制 ===")

    completion = client.chat.completions.create(
        model="mimo-v2.5-tts",
        messages=[
            {
                "role": "user",
                "content": ""  # 使用标签控制时，user 可以为空
            },
            {
                "role": "assistant",
                # 音频标签放在 assistant content 里
                "content": "(调侃) 老张你当时不是说这条航线稳得很吗……"
                          "(模仿自信，提高音量) \"系统全绿，放心走。\""
                          "(突然停顿) ……现在呢？"
                          "(爆发，愤怒压不住) 现在整艘船都在报警！你管这叫\"放心\"？！"
                          "(声音变轻) 不过……你看那外面，裂开的星云像在呼吸一样。"
                          "(低声｜情绪塌陷般平静) ……算了。"
                          "(轻笑｜带点释然) 也挺好，至少是一起看的。"
            }
        ],
        audio={
            "format": "wav",
            "voice": "白桦"
        }
    )

    message = completion.choices[0].message
    audio_bytes = base64.b64decode(message.audio.data)
    output_path = os.path.join(OUTPUT_DIR, "audio_tag.wav")
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f"音频已保存到: {output_path}")


def example_voice_design():
    """
    示例3: 音色设计 - 通过文字描述生成全新音色
    - 模型: mimo-v2.5-tts-voicedesign
    - user message: 音色描述（必须提供）
    - assistant message: 要合成的文本
    - 无需 audio.voice 参数
    """
    print("=== 示例3: 音色设计 ===")

    completion = client.chat.completions.create(
        model="mimo-v2.5-tts-voicedesign",
        messages=[
            {
                "role": "user",
                "content": "一位年迈的老先生，说带北方口音的普通话，语速缓慢而沉稳，"
                          "嗓音略带沙哑和沧桑感，仿佛一位饱经风霜的老爷爷在讲故事，充满岁月的智慧。"
            },
            {
                "role": "assistant",
                "content": "我这辈子啊，走南闯北六十多年。见过最热闹的集市，也见过最安静的戈壁。"
                          "到头来才明白一个道理——这人哪，不在走了多远的路，在于记住了多少风景。"
                          "年轻人，别光顾着赶路，偶尔也停下来看看天。"
            }
        ],
        audio={
            "format": "wav"
            # 音色设计不需要指定 voice
        }
    )

    message = completion.choices[0].message
    audio_bytes = base64.b64decode(message.audio.data)
    output_path = os.path.join(OUTPUT_DIR, "voice_design.wav")
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f"音频已保存到: {output_path}")


def example_voice_clone():
    """
    示例4: 音色克隆 - 用参考音频复刻音色
    - 模型: mimo-v2.5-tts-voiceclone
    - 需要提供一段参考音频（mp3/wav），Base64 编码后放到 audio.voice
    - 格式: data:{MIME_TYPE};base64,{BASE64_AUDIO}
    - Base64 编码后大小不超过 10MB
    """
    print("=== 示例4: 音色克隆 ===")

    # 读取参考音频文件并编码
    ref_audio_path = "reference_voice.mp3"  # 替换为你的参考音频路径
    if not os.path.exists(ref_audio_path):
        print(f"参考音频文件不存在: {ref_audio_path}，跳过此示例")
        print("请准备一段 mp3 或 wav 格式的参考音频")
        return

    with open(ref_audio_path, "rb") as f:
        voice_bytes = f.read()
    voice_base64 = base64.b64encode(voice_bytes).decode("utf-8")

    # 根据文件格式选择 MIME type
    mime_type = "audio/wav" if ref_audio_path.endswith(".wav") else "audio/mpeg"

    completion = client.chat.completions.create(
        model="mimo-v2.5-tts-voiceclone",
        messages=[
            {
                "role": "user",
                "content": "用尖锐刻薄的嗓音，带着狐假虎威的得意感说话，"
                          "在提到大人物的身份时故意放慢语速并加重语气，营造压迫感。"
            },
            {
                "role": "assistant",
                "content": "你以为我是谁，也敢在这儿跟我耍横？我告诉你，站在我身后的那个人，"
                          "说出来吓死你——是当今的——万岁爷！你今天要是不给我个说法，"
                          "我让你这铺子明天就开不了门。"
            }
        ],
        audio={
            "format": "wav",
            "voice": f"data:{mime_type};base64,{voice_base64}"
        }
    )

    message = completion.choices[0].message
    audio_bytes = base64.b64decode(message.audio.data)
    output_path = os.path.join(OUTPUT_DIR, "voice_clone.wav")
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f"音频已保存到: {output_path}")


def example_director_mode():
    """
    示例5: 导演模式 - 结构化角色/场景/指导
    适合有声剧、游戏 NPC 等对声音表演要求高的场景
    """
    print("=== 示例5: 导演模式 ===")

    director_prompt = """CHARACTER
曾是守护九天的神祇，见证了凡人的无药可救后，决定以灭世来完成最终的净化。他的心中装满悲悯，但手段是绝对的屠戮。

SCENE
悬浮于崩塌的祭坛之上，俯视下方在火海中哀嚎、曾奉他为信仰的信徒。他在降下最后的毁灭前，发出神圣却残忍的叹息。

DIRECTION
发声机制与共鸣：充分打开胸腔共鸣，制造一种神圣的回音感。声音位置靠后，音色如古钟般低沉且带有金属质感的磁性。
声调与韵律：四声（去声）的下落要极其平缓，不要砸实，带有一种吟诵古籍般的从容与宏大。字句之间的停顿拉长，展现出视万物为刍狗的威压。
气声与实声的较量：在说前两句时，实声饱满，高高在上；但在说出"闭上眼吧"时，声音突然混入大量疲惫的气息，神性开始出现裂痕，流露出勉强的残忍。
咬字细节：古风词汇（如"垂怜"、"沉疴"、"剔骨刮毒"）咬字要深，声母起音圆润而不尖锐。结尾的最后半句，几乎全部转化为气声，像是在哄睡一个婴儿，将残酷包裹在极致的悲哀之中。"""

    completion = client.chat.completions.create(
        model="mimo-v2.5-tts",
        messages=[
            {
                "role": "user",
                "content": director_prompt
            },
            {
                "role": "assistant",
                "content": "你们求我垂怜，求我降下甘霖洗净这浊世。"
                          "可这世间的沉疴，唯有烈火能剔骨刮毒。"
                          "闭上眼吧。这业火烧起来的时候，一点也不疼。"
            }
        ],
        audio={
            "format": "wav",
            "voice": "白桦"
        }
    )

    message = completion.choices[0].message
    audio_bytes = base64.b64decode(message.audio.data)
    output_path = os.path.join(OUTPUT_DIR, "director_mode.wav")
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f"音频已保存到: {output_path}")


# ============ 运行 ============
if __name__ == "__main__":
    # 取消注释想运行的示例
    example_builtin_voice()
    # example_audio_tag()
    # example_voice_design()
    # example_voice_clone()    # 需要准备参考音频文件
    # example_director_mode()
