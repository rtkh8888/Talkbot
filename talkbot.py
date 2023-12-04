import os
import azure.cognitiveservices.speech as speechsdk
import openai
from langchain.llms import AzureOpenAI
from langchain.chains import RetrievalQA, ConversationalRetrievalChain, ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
import threading


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
speech_config.speech_recognition_language="en-US"
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# The language of the voice that responds on behalf of Azure OpenAI.
speech_config.speech_synthesis_voice_name='en-US-JennyMultilingualNeural'
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)

## Initalise LLM through Langchain, with a template to print the conversation.
#deployment_id= 
model_name="text-davinci-003"
llm = AzureOpenAI(deployment_name=deployment_id,model_name=model_name)

template = """Conversation between Me and AI.

Current Conversation:
{history}
Me: {input}
AI:
"""
prompt_msg = PromptTemplate(input_variables=['history','input'],template=template)
convo = ConversationChain(prompt=prompt_msg,llm=llm,verbose=True,memory=ConversationBufferMemory(human_prefix="Me"))




    

# Prompts Azure OpenAI with a request and synthesizes the response.
def ask_openai(prompt):
    # Ask Azure OpenAI
    
    text = convo.run(input=prompt)
    print('Azure OpenAI response:' + text)

    # Azure text to speech output
    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()


    # Check result
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesized to speaker for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

def speech_input_thread():
    while True:
        try:
            speech_recognition_result = speech_recognizer.recognize_once_async().get()

            if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
                if speech_recognition_result.text == "Stop.": 
                    print("Conversation ended.")
                    break
                print("Recognized speech: {}".format(speech_recognition_result.text))
                ask_openai(speech_recognition_result.text)
            elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
                continue
                # print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))

        except EOFError:
            break

def text_input_thread():
    while True:
        text_input = input("Type your message or type 'Stop' to end the conversation: ")
        if text_input.lower() == "stop":
            print("Conversation ended.")
            break
        ask_openai(text_input)

try:
    speech_thread = threading.Thread(target=speech_input_thread)
    text_thread = threading.Thread(target=text_input_thread)

    speech_thread.start()
    text_thread.start()

    speech_thread.join()
    text_thread.join()

except Exception as err:
    print("Encountered exception. {}".format(err))

