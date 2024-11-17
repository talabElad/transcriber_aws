import asyncio  
import streamlit as st  
from amazon_transcribe.client import TranscribeStreamingClient  
from amazon_transcribe.handlers import TranscriptResultStreamHandler  
from amazon_transcribe.model import TranscriptEvent  
import uuid  
import boto3  
from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings  
from _agent_ai_academia import ai_agent_clean, ai_agent_summary  
  
# Initialize the S3 client  
s3_client = boto3.client('s3')  
  
# Set up Streamlit page  
st.set_page_config(  
    page_title="Transcriber",  
    page_icon="🧑‍🎓️",  
    layout="wide",  
    initial_sidebar_state="expanded"  
)  
  
# Modern clinical theme CSS  
st.markdown("""  
    <style>  
        :root {  
            --primary-blue: #E3F2FD;  
            --secondary-blue: #90CAF9;  
            --dark-blue: #1976D2;  
            --white: #FFFFFF;  
            --gray: #F5F5F5;  
        }  
        .stApp {  
            background-color: var(--primary-blue);  
        }  
        .main {  
            background-color: var(--white);  
            border-radius: 15px;  
            padding: 2rem;  
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);  
        }  
        h1 {  
            color: var(--dark-blue);  
            font-family: 'Heebo', sans-serif;  
            text-align: right;  
            padding: 1rem 0;  
            border-bottom: 3px solid var(--secondary-blue);  
        }  
        .stTextArea>div>div>textarea {  
            background-color: var(--white);  
            border: 2px solid var(--secondary-blue);  
            border-radius: 10px;  
            padding: 1rem;  
            direction: rtl;  
            text-align: right;  
            font-family: 'Heebo', sans-serif;  
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);  
        }  
        .stButton>button {  
            background-color: var(--dark-blue);  
            color: var(--white);  
            border-radius: 25px;  
            padding: 0.5rem 2rem;  
            font-family: 'Heebo', sans-serif;  
            border: none;  
            transition: all 0.3s ease;  
            width: 100%;  
            margin: 0.5rem 0;  
        }  
        .stButton>button:hover {  
            background-color: var(--secondary-blue);  
            transform: translateY(-2px);  
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);  
        }  
        .control-panel {  
            background-color: var(--gray);  
            padding: 1rem;  
            border-radius: 10px;  
            margin: 1rem 0;  
            direction: rtl;  
        }  
        .stSuccess {  
            background-color: #E8F5E9;  
            border: none;  
            border-radius: 10px;  
            padding: 1rem;  
            text-align: right;  
            direction: rtl;  
        }  
        .stError {  
            background-color: #FFEBEE;  
            border: none;  
            border-radius: 10px;  
            padding: 1rem;  
            text-align: right;  
            direction: rtl;  
        }  
        .element-container, .stMarkdown, p {  
            direction: rtl;  
            text-align: right;  
        }  
    </style>  
""", unsafe_allow_html=True)  
  
# Display area for transcription  
transcription_placeholder = st.empty()  
  
# Ensure sessionid is set in session state  
if "sessionid" not in st.session_state:  
    # Generate a unique session ID if it does not exist  
    st.session_state.sessionid = str(uuid.uuid4())  
  
# Use the session ID from session state  
sessionid = st.session_state.sessionid  
  
# Define the S3 bucket, folder, and file name  
bucket_name = 'testtranscriberapp'  
folder_name = 'test'  
file_name = 'raw.txt'  
  
# Event handler to process transcription results  
class MyEventHandler(TranscriptResultStreamHandler):  
    def __init__(self, stream, transcription_display):  
        super().__init__(stream)  
        self.transcription_display = transcription_display  
        self.transcription_accum = ""  
        self.event_count = 0  
        self.stop_transcription = False  
  
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):  
        if self.stop_transcription:  
            return  
  
        results = transcript_event.transcript.results  
        self.event_count += 1  
        for result in results:  
            speaker = None  
            if result.alternatives[0].items[0].speaker is not None:  
                speaker = f"דובר {result.alternatives[0].items[0].speaker}: "  # Hebrew "Speaker"  
            if len(result.alternatives) > 0:  
                transcript = result.alternatives[0].transcript  
                full_transcript = f"{speaker}{transcript}" if speaker else transcript  
                if not result.is_partial:  
                    self.transcription_accum += full_transcript + "\n"  
                    self.transcription_display.text_area("תמלול:", self.transcription_accum, height=300,  
                                                       key=f"live_{self.event_count}")  
                    st.session_state.transcription_text = self.transcription_accum  
                else:  
                    lines = self.transcription_accum.split('\n')  
                    if lines[-1].strip():  
                        lines[-1] = full_transcript  
                    else:  
                        lines.append(full_transcript)  
                    self.transcription_show = '\n'.join(lines)  
                    self.transcription_display.text_area("תמלול:", self.transcription_show, height=300,  
                                                       key=f"live_{self.event_count}")  
  
    def update_transcription(self, new_text):  
        self.transcription_accum += new_text + "\n"  
        self.transcription_display.text_area("תמלול:", self.transcription_accum, height=300,  
                                           key=f"live_{self.event_count}")  
        st.session_state.transcription_text = self.transcription_accum  
  
    def stop(self):  
        self.stop_transcription = True  
  
# Function to handle the transcription process  
async def basic_transcribe(transcription_display):  
    client = TranscribeStreamingClient()  
    stream = await client.start_stream_transcription(  
        language_code="he-IL",  
        media_sample_rate_hz=16000,  
        media_encoding="pcm",  
        show_speaker_label="true"  
    )  
    handler = MyEventHandler(stream.output_stream, transcription_display)  
    event_task = asyncio.create_task(handler.handle_events())  
    await asyncio.gather(event_task)  
    return handler  
  
# App Header  
st.markdown("<h1>🧑‍🎓️ תמלילן</h1>", unsafe_allow_html=True)  
st.markdown("<p class='subtitle'>מערכת תמלול באמצעות בינה מלאכותית</p>", unsafe_allow_html=True)  
  
# Create a clean control panel layout  
st.markdown("<div class='control-panel'>", unsafe_allow_html=True)  
col1, col2, col3 = st.columns(3)  
with col3:  
    webrtc_ctx = webrtc_streamer(  
        key="transcription",  
        mode=WebRtcMode.SENDRECV,  
        client_settings=ClientSettings(  
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},  
            media_stream_constraints={"audio": True, "video": False},  
        ),  
    )  
with col2:  
    stop_button = st.button("עצור הקלטה ⏹️")  
with col1:  
    clear_button = st.button("תמלול חדש 🗑️")  
st.markdown("</div>", unsafe_allow_html=True)  
  
# Action buttons in a separate section  
st.markdown("<div class='action-panel'>", unsafe_allow_html=True)  
col4, col5, col6 = st.columns(3)  
with col6:  
    clean_button = st.button("נקה שיחה 🧹")  
with col5:  
    summary_button = st.button("סיכום שיחה 📝")  
with col4:  
    email_button = st.button("שלח מייל 📧")  
st.markdown("</div>", unsafe_allow_html=True)  
  
# Handle the transcription logic  
if webrtc_ctx.state.playing:  
    st.markdown("<div class='status-message'>מתחיל הקלטה...</div>", unsafe_allow_html=True)  
    st.markdown("<p style='direction: rtl; text-align: right;'>מתחיל תמלול...</p>", unsafe_allow_html=True)  
    loop = asyncio.new_event_loop()  
    asyncio.set_event_loop(loop)  
    handler = loop.run_until_complete(basic_transcribe(transcription_placeholder))  
  
    if stop_button:  
        handler.stop()  
        st.markdown("<p style='direction: rtl; text-align: right;'>התמלול הופסק.</p>", unsafe_allow_html=True)  
  
if stop_button:  
    raw_text = st.text_area(  
        "",  
        value=st.session_state.transcription_text,  
        height=150,  
        key="raw_text_area"  
    )  
    s3_path = f"{folder_name}/{file_name}"  
    s3_clean = f"{folder_name}/clean.txt"  
    s3_summary = f"{folder_name}/summary.txt"  
    s3_client.put_object(Bucket=bucket_name, Key=s3_path, Body=raw_text)  
    clean_text = ai_agent_clean(raw_text)  
    summary_text = ai_agent_summary(clean_text)  
    s3_client.put_object(Bucket=bucket_name, Key=s3_clean, Body=clean_text)  
    s3_client.put_object(Bucket=bucket_name, Key=s3_summary, Body=summary_text)  
    st.success(f"התמלול מוכן...")  
    st.markdown("<div class='status-message'>ההקלטה הסתיימה</div>", unsafe_allow_html=True)  
  
# Display areas should be wrapped in RTL containers  
st.markdown("<div class='transcription-area'>", unsafe_allow_html=True)  
st.markdown("</div>", unsafe_allow_html=True)  
  
# Then handle the button actions and display text areas outside columns  
if clean_button:  
    s3_path = f"{folder_name}/clean.txt"  
    try:  
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_path)  
        file_content = response['Body'].read().decode('utf-8')  
        st.text_area("Cleaned Text", value=file_content, height=150, key="clean_text_area")  
    except Exception as e:  
        st.error(f"Could not retrieve file: {e}")  
  
if summary_button:  
    s3_summary = f"{folder_name}/summary.txt"  
    try:  
        response = s3_client.get_object(Bucket=bucket_name, Key=s3_summary)  
        file_content = response['Body'].read().decode('utf-8')  
        st.text_area("Summary", value=file_content, height=150, key="summary_text_area")  
    except Exception as e:  
        st.error(f"Could not retrieve file: {e}")  