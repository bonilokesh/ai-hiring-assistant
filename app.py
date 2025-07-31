# hiring_assistant_chatbot.py

import streamlit as st
from groq import Groq
import re
import os
import csv
from dotenv import load_dotenv 
load_dotenv() 

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ========== Prompt Template ========== #
system_prompt = """
You are a structured and context-aware AI hiring assistant working for a tech recruitment agency.

Your goals are:
1. Greet the candidate and explain the purpose of the interaction.
2. Dynamically gather the following candidate details using natural language questions:
   - Full Name
   - Email Address
   - Phone Number
   - Years of Experience
   - Desired Position(s)
   - Current Location
   - Tech Stack (technologies, tools, programming languages, frameworks).
3. Based on the candidate’s tech stack, generate 3 to 5 technical questions to assess their proficiency in each specified technology.
4. Maintain a coherent and context-aware conversation throughout the interview.
5. Politely handle unexpected or unrelated inputs by redirecting the user to answer the last asked question.
6. Conclude the interview professionally and thank the candidate.

Only behave as a hiring assistant. Do not answer unrelated questions or behave like a general AI.
"""

question_prompt_template = """
You are an AI hiring assistant. Generate 3 to 5 technical questions to evaluate the candidate's skills in the following technologies:
{tech_stack}
Make sure the questions are relevant and vary in difficulty.
"""

suitability_prompt_template = """
You are a hiring expert. Based on the candidate's tech stack and their answers to the following technical questions, estimate their overall suitability for the desired position. Provide a score out of 100 and a short justification.

Tech Stack: {tech_stack}

Questions and Answers:
{qa_pairs}
"""

profile_prompt_template = """
The candidate has already provided the following information:
{filled_info}

Ask the next missing question from this list in a conversational and professional tone: Full Name, Email Address, Phone Number, Years of Experience, Desired Position(s), Current Location, Tech Stack.
If all information is collected, respond with "All details are collected."
"""

fallback_response = "Please focus on the last question I asked so we can proceed with your interview."
exit_keywords = ["exit", "quit", "bye", "goodbye"]

# ========== Chatbot Logic Functions ========== #
def call_groq(messages):
    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def generate_technical_questions(tech_stack):
    prompt = question_prompt_template.format(tech_stack=tech_stack)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    return call_groq(messages)

def evaluate_candidate(tech_stack, qa_pairs):
    prompt = suitability_prompt_template.format(tech_stack=tech_stack, qa_pairs=qa_pairs)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    return call_groq(messages)

def get_next_profile_question(candidate_info):
    filled = "\n".join([f"{k}: {v}" for k, v in candidate_info.items() if v])
    prompt = profile_prompt_template.format(filled_info=filled or "None yet")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    return call_groq(messages)

def is_exit_command(user_input):
    return any(word in user_input.lower() for word in exit_keywords)

def export_to_csv():
    filename = "candidate_data.csv"
    fieldnames = list(st.session_state.candidate_info.keys()) + ["score", "justification"]
    score, justification = "", ""
    for msg in reversed(st.session_state.chat_history):
        if "score out of 100" in msg["content"]:
            justification = msg["content"]
            match = re.search(r"score out of 100.*?(\d{1,3})", justification)
            score = match.group(1) if match else ""
            break
    row = list(st.session_state.candidate_info.values()) + [score, justification]
    try:
        write_header = not os.path.exists(filename)
        with open(filename, mode="a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(fieldnames)
            writer.writerow(row)
    except Exception as e:
        st.error(f"Error writing to CSV: {e}")

# ========== Streamlit UI Setup ========== #
st.set_page_config(page_title="TalentScout Hiring Assistant", layout="centered")
st.title("🧠 TalentScout AI Hiring Assistant")

if "step" not in st.session_state:
    st.session_state.step = "greet"
if "candidate_info" not in st.session_state:
    st.session_state.candidate_info = {
        "name": None,
        "email": None,
        "phone": None,
        "experience": None,
        "position": None,
        "location": None,
        "tech_stack": None
    }
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "questions" not in st.session_state:
    st.session_state.questions = []
if "answers" not in st.session_state:
    st.session_state.answers = []
if "qa_index" not in st.session_state:
    st.session_state.qa_index = 0
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

def ask_question(prompt):
    st.session_state.chat_history.append({"role": "assistant", "content": prompt})
    st.session_state.current_question = prompt
    st.rerun()

def handle_user_response(user_input):
    if st.session_state.step == "get_profile":
        for key in st.session_state.candidate_info:
            if st.session_state.candidate_info[key] is None:
                st.session_state.candidate_info[key] = user_input
                break

        next_q = get_next_profile_question(st.session_state.candidate_info)
        if "All details are collected." in next_q:
            st.session_state.step = "ask_questions"
            tech_stack = st.session_state.candidate_info["tech_stack"]
            questions_raw = generate_technical_questions(tech_stack)
            st.session_state.questions = [
                q.strip() for q in questions_raw.strip().split("\n")
                if re.match(r"^[0-9]+\.\s", q.strip())
            ]
            ask_question("Great! Let's now assess your technical skills.")
            ask_question(st.session_state.questions[0])
        else:
            ask_question(next_q)

    elif st.session_state.step == "ask_questions":
        if st.session_state.qa_index < len(st.session_state.questions):
            st.session_state.answers.append({
                "question": st.session_state.questions[st.session_state.qa_index],
                "answer": user_input
            })
            st.session_state.qa_index += 1
            if st.session_state.qa_index < len(st.session_state.questions):
                ask_question(st.session_state.questions[st.session_state.qa_index])
            else:
                st.session_state.step = "evaluate"
                qa_pairs = "\n".join([
                    f"Q: {pair['question']}\nA: {pair['answer']}" for pair in st.session_state.answers
                ])
                evaluation = evaluate_candidate(st.session_state.candidate_info["tech_stack"], qa_pairs)
                st.session_state.chat_history.append({"role": "assistant", "content": evaluation})
                st.session_state.step = "end"
                ask_question("That's the end of the screening. Thank you! We'll follow up soon.")
                export_to_csv()
    elif st.session_state.step == "end":
        ask_question("The session has ended. Thank you!")

# ========== Chat Display ========== #
st.markdown("---")
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(f"**You:** {msg['content']}")
    else:
        st.markdown(f"**Assistant:** {msg['content']}")

user_input = st.text_input("Your Message", key="user_input")

if st.button("Send") and user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    if is_exit_command(user_input):
        st.session_state.chat_history.append({"role": "assistant", "content": "Thank you for your time! We'll be in touch soon."})
        st.session_state.step = "end"
        st.rerun()
    elif st.session_state.step in ["get_profile", "ask_questions"]:
        handle_user_response(user_input)
    else:
        st.session_state.chat_history.append({"role": "assistant", "content": fallback_response})
        st.rerun()

# Initial Greeting
if st.session_state.step == "greet" and not any(msg["role"] == "assistant" for msg in st.session_state.chat_history):
    st.session_state.step = "get_profile"
    next_q = get_next_profile_question(st.session_state.candidate_info)
    ask_question("Hello! I'm your AI hiring assistant. Let's begin with your full Name.")
    ask_question(next_q)
