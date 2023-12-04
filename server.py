from flask import Flask, render_template, request, jsonify
import os
import azure.cognitiveservices.speech as speechsdk
import openai
from langchain.llms import AzureOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate

app = Flask(__name__, static_url_path='/static')

# This example requires environment variables named "OPEN_AI_KEY" and "OPEN_AI_ENDPOINT"
# Your endpoint should look like the following https://YOUR_OPEN_AI_RESOURCE_NAME.openai.azure.com/

openai.api_type = os.environ.get('OPENAI_API_TYPE')
openai.api_version = os.environ.get('OPENAI_API_VERSION')
openai.api_key = os.environ.get('OPENAI_API_KEY')
openai.api_base = os.environ.get('OPENAI_API_BASE')

# This will correspond to the custom name you chose for your deployment when you deployed a model.
speech_key = os.environ.get('SPEECH_KEY')
speech_region = os.environ.get('SPEECH_REGION')

# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
audio_output_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Should be the locale for the speaker's language.
speech_config.speech_recognition_language = "en-US"
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# The language of the voice that responds on behalf of Azure OpenAI.
speech_config.speech_synthesis_voice_name = 'en-US-JennyMultilingualNeural'
print('Voice Name', speech_config.speech_synthesis_voice_name)
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)

# Initalize LLM through Langchain, with a template to print the conversation.
#deployment_id = 
model_name = "text-davinci-003"
llm = AzureOpenAI(deployment_name=deployment_id, model_name=model_name)

template = """Conversation between Me and AI.

Current Conversation:
{history}
Me: {input}
AI:
"""
prompt_msg = PromptTemplate(input_variables=['history', 'input'], template=template)
convo = ConversationChain(prompt=prompt_msg, llm=llm, verbose=True, memory=ConversationBufferMemory(human_prefix="Me"))



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.json['user_message'] 
    response = convo.run(input=user_message)
    return jsonify({'bot_response': response})

if __name__ == '__main__':
    app.run()



