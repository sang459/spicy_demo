import streamlit as st
import openai

st.markdown("""
            <style>
            [data-testid="stSidebarNav"] {
                display: none
            }
            
            [data-testid="stSidebar"] {
                display: none
            }
            </style>
            """, unsafe_allow_html=True)

def get_response(chat_history_for_model_day2):
    response = openai.ChatCompletion.create(
                model= "gpt-4",
                messages=chat_history_for_model_day2,
                stream=False,
                temperature=0.5,
                top_p = 0.93
                )
    return response['choices'][0]['message']['content']
    # 대화 시작

for message in st.session_state.chat_history_for_display_day2:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type here")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history_for_model_day2.append({"role": "user", "content": user_input})
    st.session_state.chat_history_for_display_day2.append({"role": "user", "content": user_input})

    response = get_response(st.session_state.chat_history_for_model_day2)
    st.session_state.chat_history_for_model_day2.append({"role": "assistant", "content": response})
    st.session_state.chat_history_for_display_day2.append({"role": "assistant", "content": response})

    st.experimental_rerun()



