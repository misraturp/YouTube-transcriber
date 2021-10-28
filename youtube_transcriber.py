import streamlit as st
import youtube_dl
import requests
import pprint
from configure import auth_key
from time import sleep

ydl_opts = {
   'format': 'bestaudio/best',
   'postprocessors': [{
       'key': 'FFmpegExtractAudio',
       'preferredcodec': 'mp3',
       'preferredquality': '192',
   }],
   'ffmpeg-location': './',
   'outtmpl': "./%(id)s.%(ext)s",
}

transcript_endpoint = "https://api.assemblyai.com/v2/transcript"
upload_endpoint = 'https://api.assemblyai.com/v2/upload'

headers_auth_only = {'authorization': auth_key}
headers = {
   "authorization": auth_key,
   "content-type": "application/json"
}
CHUNK_SIZE = 5242880
 

def transcribe_from_link(link, categories: bool):
   _id = link.strip()

   def get_vid(_id):
       with youtube_dl.YoutubeDL(ydl_opts) as ydl:
           return ydl.extract_info(_id)

   meta = get_vid(_id)
   save_location = meta['id'] + ".mp3"

   duration = meta['duration']

   print('Saved mp3 to', save_location)

   def read_file(filename):
       with open(filename, 'rb') as _file:
           while True:
               data = _file.read(CHUNK_SIZE)
               if not data:
                   break
               yield data
  
   upload_response = requests.post(
       upload_endpoint,
       headers=headers_auth_only, data=read_file(save_location)
   )
   audio_url = upload_response.json()['upload_url']
   print('Uploaded to', audio_url)
   transcript_request = {
       'audio_url': audio_url,
       'iab_categories': 'True' if categories else 'False',
   }
 
   transcript_response = requests.post(transcript_endpoint, json=transcript_request, headers=headers)
   transcript_id = transcript_response.json()['id']
   polling_endpoint = transcript_endpoint + "/" + transcript_id

   print("Transcribing at", polling_endpoint)

   polling_response = requests.get(polling_endpoint, headers=headers)

   while polling_response.json()['status'] != 'completed':
       sleep(30)
       try:
           polling_response = requests.get(polling_endpoint, headers=headers)
       except:
           print("Expected wait time:", duration*2/5, "seconds")
           print("After wait time is up, call poll with id", transcript_id)
           return transcript_id

   _filename = transcript_id + '.txt'
   
   # with open(_filename, 'w') as f:
   #     f.write(polling_response.json()['text'])
   # print('Transcript saved to', _filename)
   return polling_response.json()['text']


st.title('Easily transcribe YouTube videos')


link = st.text_input('Enter your YouTube video link')
st.video(link)
transcript = transcribe_from_link(link, False)

# with open('we0pvtvkm-645c-408b-ac03-c8c25acc6a8b.txt') as f:
#     transcript = f.readlines()

st.markdown(transcript)




 