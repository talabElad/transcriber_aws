import streamlit as st
from streamlit_webrtc import webrtc_streamer
import soundfile as sf
import numpy as np

def process_audio(audio_frames):
    # Example: Save the audio as a WAV file
    audio_data = b''.join(audio_frames)
    with open("output.wav", "wb") as f:
        f.write(audio_data)

st.title("Audio Recorder and Streamer")
result = webrtc_streamer(
    key="audio_stream", audio_receiver_size=256
)

if result.audio_receiver:
    audio_frames = []
    while True:
        audio_frame = result.audio_receiver.get_audio_frame()
        if audio_frame:
            audio_frames.append(audio_frame.to_ndarray().tobytes())
        else:
            break

    # Process received audio
    process_audio(audio_frames)
    st.success("Audio saved!")
