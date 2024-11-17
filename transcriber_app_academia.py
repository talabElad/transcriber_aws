import asyncio  
import pyaudio  
import streamlit as st  
from amazon_transcribe.client import TranscribeStreamingClient  
from amazon_transcribe.handlers import TranscriptResultStreamHandler  
from amazon_transcribe.model import TranscriptEvent  
import uuid  
import boto3  
from _agent_ai_academia import ai_agent_clean, ai_agent_summary  
  
# Initialize the S3 client and session state setup remains the same...  
# [Previous initialization code remains unchanged]  
  
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
            --primary-blue: #E3F2FD;    /* Light blue background */  
            --secondary-blue: #90CAF9;   /* Accent blue */  
            --dark-blue: #1976D2;        /* Text and button blue */  
            --white: #FFFFFF;            /* Pure white */  
            --gray: #F5F5F5;             /* Light gray for sections */  
        }  
        /* Global styles */  
        .stApp {  
            background-color: var(--primary-blue);  
        }  
        .main {  
            background-color: var(--white);  
            border-radius: 15px;  
            padding: 2rem;  
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);  
        }  
        /* Header styling */  
        h1 {  
            color: var(--dark-blue);  
            font-family: 'Heebo', sans-serif;  
            text-align: right;  
            padding: 1rem 0;  
            border-bottom: 3px solid var(--secondary-blue);  
        }  
        /* Text areas */  
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
        /* Buttons */  
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
        /* Control panel */  
        .control-panel {  
            background-color: var(--gray);  
            padding: 1rem;  
            border-radius: 10px;  
            margin: 1rem 0;  
            direction: rtl;  
        }  
        /* Success messages */  
        .stSuccess {  
            background-color: #E8F5E9;  
            border: none;  
            border-radius: 10px;  
            padding: 1rem;  
            text-align: right;  
            direction: rtl;  
        }  
        /* Error messages */  
        .stError {  
            background-color: #FFEBEE;  
            border: none;  
            border-radius: 10px;  
            padding: 1rem;  
            text-align: right;  
            direction: rtl;  
        }  
        /* RTL support for all text */  
        .element-container, .stMarkdown, p {  
            direction: rtl;  
            text-align: right;  
        }  
        /* Button icons */  
        .button-icon {  
            font-size: 1.5rem;  
            margin-left: 0.5rem;  
        }  
    </style>  
""", unsafe_allow_html=True)  
  
# Display area for transcriptions  
transcription_placeholder = st.empty()  
  
# Initialize the S3 client  
s3_client = boto3.client('s3')  
  
# Ensure `sessionid` is set in session state  
if "sessionid" not in st.session_state:  
    # Generate a unique session ID if it does not exist  
    st.session_state.sessionid = str(uuid.uuid4())  
  
# Use the session ID from session state  
sessionid = st.session_state.sessionid  
  
# Define the S3 bucket, folder, and file name  
bucket_name = 'testtranscriberapp'  
folder_name = 'test'  # f"{sessionid}"  
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
                # Check if this is a partial result or a final result  
                if not result.is_partial:  
                    # For final results, append the full transcript  
                    self.transcription_accum += full_transcript + "\n"  
                    self.transcription_display.text_area("תמלול:", self.transcription_accum, height=300,  
                                                         key=f"live_{self.event_count}")  
                    # Store the accumulated transcription in session state  
                    st.session_state.transcription_text = self.transcription_accum  
                else:  
                    # For partial results, update the last line  
                    lines = self.transcription_accum.split('\n')  
                    if lines[-1].strip():  # If the last line is not empty  
                        lines[-1] = full_transcript  
                    else:  
                        lines.append(full_transcript)  
                    self.transcription_show = '\n'.join(lines)  
                    # Update transcription display in Streamlit  
                    self.transcription_display.text_area("תמלול:", self.transcription_show, height=300,  
                                                         key=f"live_{self.event_count}")  
  
    def update_transcription(self, new_text):  
        self.transcription_accum += new_text + "\n"  
        self.transcription_display.text_area("תמלול:", self.transcription_accum, height=300,  
                                             key=f"live_{self.event_count}")  
        st.session_state.transcription_text = self.transcription_accum  
  
    def stop(self):  
        self.stop_transcription = True  
  
  
# Function to stream microphone input  
async def mic_stream():  
    loop = asyncio.get_event_loop()  
    input_queue = asyncio.Queue()  
  
    def callback(in_data, frame_count, time_info, status):  
        loop.call_soon_threadsafe(input_queue.put_nowait, (in_data, status))  
  
    # Initialize PyAudio  
    p = pyaudio.PyAudio()  
    stream = p.open(  
        format=pyaudio.paInt16,  
        channels=1,  
        rate=16000,  
        input=True,  
        frames_per_buffer=1024,  
        stream_callback=callback  
    )  
  
    with stream:  
        while True:  
            in_data, status = await input_queue.get()  
            yield in_data, status  
  
  
# Function to write audio chunks to the transcription stream  
async def write_chunks(stream, handler):  
    async for chunk, status in mic_stream():  
        if handler.stop_transcription:  
            break  
        await stream.input_stream.send_audio_event(audio_chunk=chunk)  
    await stream.input_stream.end_stream()  
  
  
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
    # Create a task for handling events  
    event_task = asyncio.create_task(handler.handle_events())  
    # Create a task for writing chunks  
    chunk_task = asyncio.create_task(write_chunks(stream, handler))  
    # Wait for both tasks to complete  
    await asyncio.gather(event_task, chunk_task)  
    return handler  
  
  
# App Header  
st.markdown("<h1>🧑‍🎓️ תמלילן</h1>", unsafe_allow_html=True)  
st.markdown("<p class='subtitle'>מערכת תמלול באמצעות בינה מלאכותית   </p>", unsafe_allow_html=True)  
  
# Create a clean control panel layout  
st.markdown("<div class='control-panel'>", unsafe_allow_html=True)  
col1, col2, col3 = st.columns(3)  
with col3:  
    play_button = st.button("התחל הקלטה ▶️")  
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
  
# Rest of your existing logic remains the same, but wrapped in RTL containers  
if play_button:  
    st.markdown("<div class='status-message'>מתחיל הקלטה...</div>", unsafe_allow_html=True)  
    st.markdown("<p style='direction: rtl; text-align: right;'>מתחיל תמלול...</p>", unsafe_allow_html=True)  
    loop = asyncio.new_event_loop()  
    asyncio.set_event_loop(loop)  
    handler = loop.run_until_complete(basic_transcribe(transcription_placeholder))  
  
    # Stop transcription when the stop button is clicked  
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
    # Upload the raw text to S3  
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
# Your existing transcription display logic...  
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
