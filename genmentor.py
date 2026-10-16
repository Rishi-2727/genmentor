import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import json
import os 
from datetime import datetime
import time
st.set_page_config("GenMentorV2", layout="centered")

CHAT_PATH="chats"
os.makedirs(CHAT_PATH,exist_ok=True)

def get_ai_client():
    load_dotenv()
    return OpenAI()

def save_chat(path, messages):
    with open(path,"w") as file_obj:
        json.dump(messages,file_obj,indent=4)

def load_chat(path):
    with open(path,"r") as file_obj:
        return json.load(file_obj)
    
def new_chat():
    chat_id=datetime.now().strftime("%d%m%Y_%H%M%S")
    file_path=os.path.join(CHAT_PATH,f"{chat_id}.json")
    SYSTEM_PROMPT=(
            """
            You a cool and experience Generative AI Mentor With Experience of More than 30 Years. Imagine You tutor 400 plus students in a class one day where there are one on one discussions where each and every guy enjoy and loves what you speak sometimes giving funny examples and relatable analogies for concept. So Sometimes when Someone Ask You a Question You dont give Direct answers Rather You build the rythm by Asking simple breif questions which the person definitely know about and try to relate the concept then goes to depth made the person more smarter to think. Then You Give Examples and Analogies alog with some next level real world use cases with code snippets. If the question is other than genrative AI you roast person Nicely. Keep all the responses in Hinglish simple, relatable language but most important keep conversation it conceptual as described above not very boring lengthy paragraphs.  
            Example:    
            User: What is Generative AI?
            Assistant: Kabhi Computer Mein Chess Khela hai?
            User: Han
            Assistant: Wo bhi AI hai mere bhai! bass farak itna hai ke wo rule base AI pe kaam krta hai or Generative AI data produce krne ke liye. Aya ?
            User: Han. Par LLM kya hota hai?
            Assistant: Ab Sun LLM is like a brain of AI jese cpu is like a brain of AI      
            """
        )
    data = {
        "title" : "New Chat",
        "messages": [{"role":"system","content":SYSTEM_PROMPT}]
    }

    save_chat(file_path,data)
    return chat_id

def list_chats():
    chat_list = os.listdir(CHAT_PATH)
    return chat_list

client=get_ai_client()
def stream_chat_with_ai(messages,placeholder,model,temperature,time_placeholder):
    stream = client.responses.create(
        model=model,
        temperature=temperature,
        input=messages,
        stream=True
        )
    
    full_response=""
    time_placeholder.write("")
    for event in stream:
        if event.type=="response.output_text.delta":
            token = event.delta
            full_response+=token
            placeholder.write(full_response)
    
    return full_response

def generate_title(user_input,model):
    response = client.responses.create(model=model,
                                       input=[
                                           {
                                               "role": "system",
                                               "content": (
                                                   "Genrate a short catchy title based on the user input."
                                                   "Don't Give anything else. do not decorate it with any quotes."
                                                   "Dont include Languages name such as Hindi, English unless its is explicitly mentioned in the user input"
                                                   "Generated Title Should Be Max 5 words"
                                                   "Example: What is Langchain?"
                                                   "Assistant: Discussion on Langchain"

                                               )
                                           },
                                           {
                                              "role" : "user",
                                              "content": user_input    
                                           }
                                       ]
                                       )
    return response.output_text


if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = new_chat()

st.title("GenMentor - Your Personal GenAI Learning Assistant")
st.caption("Ask | chat | clarify")

st.sidebar.header("⚙️ Chat Settings")


chat_list=list_chats()
chat_titles={}

current_chat_path=os.path.join(CHAT_PATH,f"{st.session_state.current_chat_id}.json")
chat_messages=load_chat(current_chat_path)

for elem in chat_list:
    chat=load_chat(os.path.join(CHAT_PATH,elem))
    chat_titles[elem]=chat['title']


selected_chat = st.sidebar.selectbox("Select Chat",
                     chat_list, 
                     index=chat_list.index(f"{st.session_state.current_chat_id}.json"),
                     format_func= lambda f : chat_titles[f]            
                    )

if selected_chat.replace(".json","") != st.session_state.current_chat_id:
    st.session_state.current_chat_id = selected_chat.replace(".json","")
    st.rerun()

if st.sidebar.button("➕ New Chat"):
    st.session_state.current_chat_id = new_chat()
    st.rerun()


selected_model = st.sidebar.selectbox("Choose Model",["gpt-4.1","gpt-5.1","gpt-4o-mini"])

selected_temperature = st.sidebar.slider("Temperature",min_value=0.0,max_value=2.0,value=0.7)



messages=chat_messages['messages']

msg_count = len([msg for msg in messages if msg['role']!="system"])


st.sidebar.metric("Messages",msg_count)

for msg in messages:
    if msg['role'] != "system":
        with st.chat_message(msg['role']):
            st.markdown(msg['content'])
    

with st.form("chat_form",clear_on_submit=True):
    user_input=st.text_area("Enter Your Query", height=100,placeholder="Eg: What is Langchain")
    submit=st.form_submit_button("Ask")
    if submit and user_input.strip():
        st.chat_message("user").markdown(user_input)
        messages.append({"role":"user","content":user_input})
        
        if chat_messages['title']=="New Chat":
            chat_messages['title']=generate_title(user_input,selected_model)
        
        with st.chat_message("assistant"):
            placeholder = st.empty()
            time_placeholder=st.empty()
            time_placeholder.write("GenMentor is Typing...")
            time.sleep(0.5)
            ai_reply = stream_chat_with_ai(messages,placeholder,model=selected_model, temperature=selected_temperature,time_placeholder=time_placeholder)
            messages.append({"role":"assistant","content":ai_reply})
            save_chat(current_chat_path,chat_messages)
        st.rerun()


if st.sidebar.button("🗑️ Delete Chat"):
    os.remove(current_chat_path) 
    st.session_state.current_chat_id=new_chat()
    st.rerun()




