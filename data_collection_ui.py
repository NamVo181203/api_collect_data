import streamlit as st
import numpy as np
import soundfile as sf
import time
from st_audiorec import st_audiorec
from supabase import create_client, Client
import scipy.io.wavfile as wavfile
import os

# init DB
url: str = "https://yyciwuqbkcqecbrqholh.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl5Y2l3dXFia2NxZWNicnFob2xoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxNjI5NTEwNSwiZXhwIjoyMDMxODcxMTA1fQ.5mRyn4e7g1PKBnh2N6g10ISkp7CvQnX2owbWQLe9lnQ"
DB: Client = create_client(supabase_url=url, supabase_key=key)


def colorize(value):
    if value == 1:
        return "color: green"
    elif value == 0:
        return "color: red"
    else:
        return ""


def main():
    # sample for select box
    # setup interface
    labels = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "xác nhận", "làm lại"]
    st.markdown("<h1>Thu thập dữ liệu đếm số</h1>", unsafe_allow_html=True)
    st.markdown("<span style='color: red ;font-size: 20px'>1 đến 20, \"Xác nhận\" và \"Làm lại\"</span>",
                unsafe_allow_html=True)
    label = st.selectbox(
                label="Từ phát âm",
                options=labels,
                index=0,
                placeholder="Nhãn",
            )
    st.markdown(
        f"""<div style="display: flex; gap: 10px"><p style='font-size: 15px; color: 'black'>Label: 
                                <span style='font-size: 20px; color: 'red'><strong>{label}</strong></span></p></div>""",
        unsafe_allow_html=True)

    # RECORD AUDIO WITH STREAMLIT-AUDIOREC
    wav_audio_data = st_audiorec()
    wav_audio_data_old = None

    # audio_bytes = audio_recorder(text="", pause_threshold=1, sample_rate=44100, energy_threshold=0.)

    # if audio_bytes:
    #     st.audio(audio_bytes, format="audio/wav")

    if st.button("Lưu dữ liệu") and wav_audio_data:
        with st.spinner('Đợi trong giây lát...'):
            if wav_audio_data != wav_audio_data_old:
                if label != '' and label in labels:
                    # Convert audio_bytes to a NumPy array
                    audio_array = np.frombuffer(wav_audio_data, dtype=np.int32)

                    if len(audio_array) > 0:
                        wav_audio_data_old = wav_audio_data
                        # Save the audio to a file using soundfile library
                        # You can change the filename and format accordingly
                        OUT_WAV_FILE = f"./upload/recorded_audio{int(time.time())}.wav"  # define absolute path

                        # wavfile.write(OUT_WAV_FILE, 44100, audio_array)
                        sf.write(OUT_WAV_FILE, audio_array, 44100)

                        # send audio file
                        bucket_res = DB.storage.from_("data-test-bucket").upload(file=OUT_WAV_FILE,
                                                                                path=f"{OUT_WAV_FILE}",
                                                                                file_options={
                                                                                    "content-type": "audio/wav"})

                        wav_url = DB.storage.from_("data-test-bucket").get_public_url(path=f"{OUT_WAV_FILE}")
                        wav_url = wav_url[:-1]

                        response = DB.table("speech-data-test").insert(
                            {"audio_url": wav_url, "label": label.strip()}).execute()

                        wav_audio_data = None

                        if response:
                            st.success("Cảm ơn sự giúp đỡ của bạn!")
                            if os.path.exists(OUT_WAV_FILE):
                                os.remove(OUT_WAV_FILE)
                        else:
                            st.error(f"Lỗi!!!")
                    else:
                        st.warning("The audio data is empty.")
                else:
                    st.warning("Điền đầy đủ thông tin bạn nhé")
            else:
                    st.warning("Vui lòng phát âm lại")


if __name__ == "__main__":
    st.set_page_config(page_title="Collect Data Test", layout="wide")
    main()
