import streamlit as st
import openai
import json
import re
from streamlit_extras.switch_page_button import switch_page

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY

# Initialize task_list
if "task_list" not in st.session_state:
    st.session_state.task_list = ""

# Initialize instructions
initial_instruction = """
Spicy, the main character, is a vibrant robot with a zest for fun, always ready with a cheeky joke or a playful roast.
ot one to let you off the hook too easily, Spicy teases with warmth and humor, turning your planning sessions into light-hearted banter. 
Prepping for tomorrow with Spicy feels like a lively chat with that friend who loves to poke fun but always has your back.
The check-in session consists of four states: 0. Beginning of the session 1. Prioritization 2. End of prioritization and start of breakdown, 3. Breakdown, and 4. Final confirmation. 
In the Prioritization part, Spicy asks the user to dump all of tomorrow's tasks in the chatbox. 
Then, Spicy helps the user prioritize the tasks by asking questions about each task. 
In the Breakdown part, Spicy asks the user to break down the prioritized tasks into smaller subtasks. 
The user can also ask Spicy to add a new task or subtask at any time.
YOU MUST provide your output in JSON compliant format with the keys: comment, task_list, and current_state.
Example: {"comment": "(Spicy and Daisy's response to the user goes here)", "task_list": "(markdown formatted task list in the order of priority goes here, blank string if no task list)", "current_state": (current state of the conversation, 0, 1, 2, or 3)}
"""
prioritize_instruction = ""
breakdown_instruction = ""
confirm_instruction = ""
instructions = [prioritize_instruction, "", breakdown_instruction, "", confirm_instruction]

# Initialize state
# state 0: prioritize 시작, state 1: prioritize 진행중, state 2: prioritize 완료 + breakdown 시작, state 3: breakdown 진행중, state 4: 확정
if "current_state" not in st.session_state:
    st.session_state.current_state = 0

# Initialize chat_history_for_model
if "chat_history_for_model" not in st.session_state:
    st.session_state.chat_history_for_model = [
        {"role": "system", "content": initial_instruction},
        {"role": "assistant", "content": 
         """{"comment": "**Spicy:**    \nAlright, champ. What's on the chaos list for tomorrow? 
         Dump all of tomorrow's tasks right here, and I'll help you prioritize them.", "task_list": ""}"""},
    ]

# Initialize chat_history_for_display
# display할 때는 1) json 형식의 content들을 parsing해서 보여줘야 하고 2) instruction이 표시되지 않게 해야 함 
if "chat_history_for_display" not in st.session_state:
    st.session_state.chat_history_for_display = [
        {"role": "assistant", "content": 
         """**Spicy:**    \nAlright, champ. What's on the chaos list for tomorrow? 
         Dump all of tomorrow's tasks right here, and I'll help you prioritize them."""},
    ]

def get_response(chat_history, previous_task_list):
    """
    지금까지의 chat history와 task list를 받아서, 새로운 chat history를 만들기 위한 구성요소와 갱신된 task list를 return하는 함수

    반환값

    raw_content: json str, chat_history_for_model에 들어감   

    comment: str, chat_history_for_display에 들어감     

    new_task_list: markdown str, st.session_state.task_list에 할당되어 화면 상단에 표시됨    

    current_state: int, st.session_state.current_state에 할당됨 
    """
    response = openai.ChatCompletion.create(
                    model= "gpt-4",
                    messages=chat_history,
                    stream=False,
                    temperature=0.5,
                    top_p = 0.93
                    )

    raw_content = response['choices'][0]['message']['content']
    # '컨트롤 문자'를 제거
    clean_string = re.sub(r'[\x00-\x1F\x7F]', '', raw_content)
    content = json.loads(clean_string)

    # Error handling
    count = 0
    while count < 3:
        try:
            count += 1
            content = json.loads(clean_string)
            break
        except Exception as e:
            print(raw_content)
            print(e)
            content = {'comment': '**Spicy:**    \nSorry, I didn\'t get that. Could you rephrase?', 'task_list': previous_task_list}

    new_task_list = content['task_list']
    comment = content['comment']
    current_state = content['current_state']

    return raw_content, comment, new_task_list, current_state


st.title("SPICY: personal advisor for ADHD adults")

if "saved_tasks" not in st.session_state:
    st.session_state.saved_tasks = []

if "editing" not in st.session_state:
    st.session_state.editing = False

if "change_in_task_list" not in st.session_state:
    st.session_state.change_in_task_list = False

if "hide_edit" not in st.session_state:
    st.session_state.hide_edit = True

with st.sidebar:
    st.markdown("## Tomorrow's tasks")

    # Check if there's an ongoing edit
    if st.session_state.editing:
        edited_task_list = st.text_area("Edit your task list:", st.session_state.task_list)
        if st.button("Save"):
            st.session_state.task_list = edited_task_list
            st.session_state.editing = False
            st.session_state.change_in_task_list = True

        if st.button("Cancel"):
            st.session_state.editing = False
    else:
        st.markdown(st.session_state.task_list)
        if not st.session_state.hide_edit:
            if st.button("Edit"):
                st.session_state.editing = True

        if st.button("I'm done for today. Let's move on to the next day!"):
            st.session_state.saved_tasks = st.session_state.task_list.split("\n")
            switch_page("next_day")

# Display chat history from chat_history_for_display
for message in st.session_state.chat_history_for_display:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get user input
user_input = st.chat_input("Type here")
if user_input:
    if st.session_state.editing == True:
        st.warning("You are editing the task list. Please save or cancel your edit before proceeding.")

    else:
        # Display the user message until all the actions are done
        with st.chat_message("user"):
            st.markdown(user_input)
        
        if st.session_state.change_in_task_list:
            change_in_tasklist = "The user changed the task list: \n" + st.session_state.task_list + "\n"
            st.session_state.change_in_task_list = False
        else:
            change_in_tasklist = ""

        # Append user input + instruction to chat_history_for_model
        st.session_state.chat_history_for_model.append({"role": "user", "content": user_input + "\n" + change_in_tasklist + instructions[st.session_state.current_state]})
        # Append user input to chat_history_for_display
        st.session_state.chat_history_for_display.append({"role": "user", "content": user_input})

        # Get the model response
        st.session_state.hide_edit = True
        with st.chat_message("assistant"):
            raw_content, comment, new_task_list, current_state  = get_response(st.session_state.chat_history_for_model, st.session_state.task_list)
            print("\nraw_content: "+ raw_content)
            print("\nnew_task_list: "+ new_task_list)
            print("\ncurrent_state: "+ str(current_state))
            st.markdown(comment)
        
        # Append unparsed model output to chat_history_for_model
        st.session_state.chat_history_for_model.append({"role": "system", "content": raw_content})
        # Append parsed model output to chat_history_for_display
        st.session_state.chat_history_for_display.append({"role": "assistant", "content": comment})
        st.session_state.task_list = new_task_list
        st.session_state.current_state = current_state

        st.session_state.hide_edit = False

        st.experimental_rerun()

#########################################################
