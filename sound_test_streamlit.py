import streamlit as st
from streamlit_webrtc import webrtc_streamer
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write

st.title("Voice Recording and Streaming App")

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    st.session_state["audio"].append(indata.copy())

def start_recording():
    if "audio" not in st.session_state:
        st.session_state["audio"] = []
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=44100):
        st.write("Recording... Press 'Stop' to save.")
        st.button("Stop Recording", on_click=stop_recording)

def stop_recording():
    if "audio" in st.session_state:
        audio_data = np.concatenate(st.session_state["audio"])
        write("recorded_audio.wav", 44100, (audio_data * 32767).astype(np.int16))
        st.success("Recording saved as 'recorded_audio.wav'")
        del st.session_state["audio"]

st.button("Start Recording", on_click=start_recording)
webrtc_streamer(key="example")