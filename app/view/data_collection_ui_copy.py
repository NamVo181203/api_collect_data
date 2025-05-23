import streamlit as st
import numpy as np
import soundfile as sf
import time
from st_audiorec import st_audiorec
from supabase import create_client, Client
import scipy.io.wavfile as wavfile
from random import shuffle
import uuid
import os
import requests
from streamlit_javascript import st_javascript
import json
import csv
import random

# init DB
url: str = "https://eecucubpmvpjkhqletul.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVlY3VjdWJwbXZwamtocWxldHVsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3MTc5MzUsImV4cCI6MjA2MDI5MzkzNX0.Av-ZEQ2xczudhm2c8p1JioXRXQCf4s0m4X_w5jrkf-8"
DB: Client = create_client(supabase_url=url, supabase_key=key)

st.set_page_config(layout="wide")


def local_storage_set(key, value):
    value = json.dumps(value, ensure_ascii=False)  # Convert to JSON string
    st_javascript(f"localStorage.setItem('{key}', {value});")


# Function to get a value from localStorage
def local_storage_get(key):
    return st_javascript(f"localStorage.getItem('{key}');")


def _get_phonemes(file_path):
    list_of_phonemes = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            list_of_phonemes.append(line)
    return list_of_phonemes


def get_transcripts(path):
    samples = []
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header if there is one
        for row in reader:
            samples.append(str(row[0] + " - " + row[1]))
    return samples


@st.cache_data
def get_user_id():
    return str(uuid.uuid4())


def internal_select(option):
    texts = option.split("-")
    text = texts[1]
    return text


def on_select_change():
    selection = st.session_state["transcript"].split("-")
    item = selection[0]
    st.session_state["word"] = item


def main():
    session_id = local_storage_get("userId")
    if not session_id:
        session_id = get_user_id()
        st.session_state["userId"] = session_id
        # local_storage_set("userId", session_id)

    # sample for select box
    transcripts = get_transcripts("scripts.csv")

    _, cl1, _, cl3, _ = st.columns([1, 10, 1, 6, 1])
    with cl1:
        # setup interface
        st.markdown("<h1>Thu thập dữ liệu</h1>", unsafe_allow_html=True)
        st.markdown("<span style='color: red ;font-size: 20px'>Bạn vui lòng đọc hướng dẫn sử dụng</span>",
                    unsafe_allow_html=True)

        scol1 = st.columns(1)

        suggestion = scol1[0].selectbox(
            "Gợi ý transcript cho người dùng",
            transcripts,
            index=0,
            format_func=internal_select,
            on_change=on_select_change,
            key="transcript",
        )
        c1, c2, c3 = st.columns([5, 5, 5])

        with c1:
            age = st.number_input("Tuổi", min_value=0)
        with c2:
            gender = st.selectbox(
                "Giới tính",
                ["Nam", "Nữ"],
                index=0,
            )
        with c3:
            region = st.text_input(label="Tỉnh/TP", placeholder="Đà Nẵng")

        # RECORD AUDIO WITH STREAMLIT-AUDIOREC
        wav_audio_data = st_audiorec()

        if st.button("Lưu dữ liệu") and wav_audio_data:
            if age != 0 and session_id is not None and gender is not None and suggestion is not None and region != "" and \
                    st.session_state["word"] is not None:
                # Convert audio_bytes to a NumPy array
                audio_array = np.frombuffer(wav_audio_data, dtype=np.int32)

                if len(audio_array) > 0:
                    # Save the audio to a file using soundfile library
                    # You can change the filename and format accordingly
                    wavfile.write(f"upload/recorded_audio{time.time()}.wav", 44100, audio_array)

                    OUT_WAV_FILE = f"upload/recorded_audio{time.time()}.wav"  # define absolute path
                    sf.write(OUT_WAV_FILE, audio_array, 44100)

                    # send an audio file
                    _ = DB.storage.from_("cs-bucket").upload(file=OUT_WAV_FILE, path=f"{OUT_WAV_FILE}",
                                                             file_options={"content-type": "audio/wav"})

                    if OUT_WAV_FILE:
                        # get audio_url
                        wav_url = DB.storage.from_("cs-bucket").get_public_url(path=f"{OUT_WAV_FILE}")
                        print(f"Wav url: {wav_url}")
                        st.write("Đang chờ xử lý")
                        response = DB.table("cs-data").insert(
                            {
                                "user_id": session_id,
                                "audio_url": wav_url,
                                "word": st.session_state["word"],
                                "transcript_text": suggestion.strip().split("-")[1],
                                "age": age,
                                "gender": gender,
                                "region": region.strip()
                            }).execute()
                        if response:
                            st.markdown(f"<div style='color: red; font-size: 25px'>Cảm ơn bạn đã giành thời gian giúp "
                                        f"chúng mình</div>",
                                        unsafe_allow_html=True)

                        else:
                            st.error(f"Failed to fetch data")
                else:
                    st.warning("The audio data is empty.")
            else:
                st.title("Điền đầy đủ thông tin bạn nhé")

    with cl3:
        st.markdown(f"<h2>Hướng dẫn sử dụng</h2>", unsafe_allow_html=True)

        st.markdown(f"<p><strong>Bước 1</strong> Chọn đoạn thoại bạn muốn ghi âm trong hộp gợi ý.</p>"
                    f"<p><strong>Bước 2</strong> <strong>Điền đầy đủ thông tin </strong> (tuổi, giới tính)."
                    f"<p><strong>Bước 3</strong> Bấm <strong>“Start Recording”</strong> để thu âm, sau khi thu âm "
                    f"xong bấm ”<strong>Stop</strong>” và nghe lại phần ghi âm ở bên dưới. Nếu phần ghi âm <strong>bị "
                    f"lỗi hoặc thiếu </strong>thì bấm <strong>“Reset”</strong> để ghi âm lại nha.</p>"
                    f"<p><strong>Bước 4</strong> Bấm <strong>“Lưu dữ liệu”</strong> để gửi ghi âm về cho chúng mình "
                    f"bạn nhé</p></br>"
                    f"<strong><span style='color: red'>Lưu ý: các bạn có thể phát âm các từ tiếng Anh theo hướng Việt hóa </br>"
                    f"<strong><span style='color: green'> Eg: ability - ờ bi li ti </br>"
                    f"Hy vọng bạn có thể giúp mình với 5 audio thui </br>"
                    f"<strong><span style='color: red'>Khi thanh ghi âm hiện lên/sáng lên bạn hẳn ghi âm "
                    f"nhé.</span></strong> </br>",
                    unsafe_allow_html=True)
        st.image("visualize.png", width=300)  # aaaa
        st.markdown(f"<strong><span style='font-size: 25px'>Cảm ơn sự giúp đỡ của bạn rất nhiều</span></strong>",
                    unsafe_allow_html=True)


if __name__ == "__main__":
    main()
