import gradio as gr
import numpy as np
import scipy.io.wavfile as wavfile
import soundfile as sf
import time
import uuid
import os
import csv
from supabase import create_client

# Supabase
url = "https://eecucubpmvpjkhqletul.supabase.co"
key = "eyJhbGciOi..."  # Cẩn thận không chia sẻ publicly!
# DB = create_client(supabase_url=url, supabase_key=key)


def local_storage_set(key, value):
    value = json.dumps(value, ensure_ascii=False)  # Convert to JSON string
    st_javascript(f"localStorage.setItem('{key}', {value});")


# Function to get a value from localStorage
def local_storage_get(key):
    return st_javascript(f"localStorage.getItem('{key}');")


def get_transcripts(path: str):
    samples = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            samples.append(f"{row[0]} - {row[1]}")
    return samples


def get_provinces(path):
    provinces = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)
        for row in reader:
            provinces.append(f"{row[0]}")
    return provinces


def save_data(audio, transcript, age, gender, region):
    if age < 1:
        return "⚠️ Bạn cần nhập đúng số tuổi."

    if not transcript or not gender or not region.strip():
        return "⚠️ Bạn cần nhập đầy đủ các thông tin: Câu thoại, Giới tính và Tỉnh/TP."

    if audio is None:
        return "⚠️ Vui lòng ghi âm trước khi lưu."

    session_id = str(uuid.uuid4())
    audio_array = np.frombuffer(audio[-1], dtype=np.int16)
    filename = f"upload/recorded_audio_{int(time.time())}.wav"
    wavfile.write(filename, 44100, audio_array)

    DB.storage.from_("cs-bucket").upload(file=filename, path=f"{filename}", file_options={"content-type": "audio/wav"})
    url = DB.storage.from_("cs-bucket").get_public_url(path=f"{filename}")

    word = transcript.split("-")[0]
    transcript_text = transcript.split("-")[1]

    DB.table("cs-data").insert({
        "user_id": session_id,
        "audio_url": url,
        "word": word,
        "transcript_text": transcript_text,
        "age": age,
        "gender": gender,
        "region": region.strip()
    }).execute()

    if os.path.exists(filename):
        os.remove(filename)

    return "✅ Dữ liệu đã được lưu thành công. Cảm ơn bạn!"


transcripts = get_transcripts("scripts.csv")
provinces = get_provinces("vietnam_provinces.csv")

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    <h1 style="
        font-size: 32px;
        text-align: center;
    ">
    🎤 Ứng dụng ghi âm và thu thập dữ liệu
    </h1>
    """)

    with gr.Row():
        with gr.Column(scale=3):
            transcript = gr.Dropdown(label="Chọn câu thoại", choices=transcripts)
            age = gr.Number(label="Tuổi")
            gender = gr.Dropdown(label="Giới tính", choices=["Nam", "Nữ"])
            region = gr.Dropdown(label="Tỉnh/TP", choices=provinces)
            audio = gr.Audio(sources="microphone", type="numpy", label="Ghi âm tại đây")
            submit_btn = gr.Button("Lưu dữ liệu")
            output = gr.Textbox(label="Thông báo")
            submit_btn.click(save_data, inputs=[audio, transcript, age, gender, region], outputs=output)

        with gr.Column(scale=2):
            gr.Markdown("<h3 style='font-size: 22px'>📌 Hướng dẫn sử dụng</h3>")
            gr.Markdown("""
            <div style="font-size: 18px">
            <b>Bước 1:</b> Chọn đoạn thoại bạn muốn ghi âm trong hộp gợi ý.<br>
            <b>Bước 2:</b> Điền đầy đủ thông tin (<i>tuổi, giới tính, tỉnh/thành</i>).<br>
            <b>Bước 3:</b> Bấm <b>Start Recording</b> để ghi âm, sau đó bấm <b>Stop</b> và nghe lại.<br>
            <b>Bước 4:</b> Nếu ghi âm bị lỗi hoặc thiếu, bấm <b>Reset</b> để ghi lại.<br>
            <b>Bước 5:</b> Bấm <b>“Lưu dữ liệu”</b> để gửi ghi âm về cho nhóm phát triển.<br><br>

            <span style="color: red">🔊 Lưu ý:</span> Bạn có thể phát âm từ tiếng Anh theo kiểu Việt hóa.<br>
            Ví dụ: <code>ability</code> → <i>ờ bi li ti</i><br><br>
            👉 Hãy cố gắng giúp ghi âm <b>5 câu</b> nếu có thể nhé! Cảm ơn sự giúp đỡ của bạn 
            </div>
            """)

demo.launch()
