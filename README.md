# 🤖 AI Hiring Assistant Chatbot

A conversational, AI-powered hiring assistant built with **Streamlit** and **Groq LLMs**. This chatbot collects candidate details, asks technical questions based on their tech stack, evaluates their responses, and exports the results to CSV — all within a dynamic chat interface.

---

## 🚀 Features

- Collects candidate profile: name, email, phone, experience, etc.
- Generates 3–5 technical questions based on provided tech stack
- Uses Groq’s fast LLaMA-3 model for conversational flow
- Evaluates technical answers and gives a suitability score out of 100
- Exports all data to `candidate_data.csv`
- Built using Streamlit for a clean and interactive web UI

---

## 🧑‍💻 Tech Stack

- [Python 3.9+](https://www.python.org/)
- [Streamlit](https://streamlit.io)
- [Groq LLMs](https://console.groq.com)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ai-hiring-assistant.git
cd ai-hiring-assistant

### 2. Install Dependencies
pip install -r requirements.txt

### 3. Install Dependencies
Create a .env file in the project root:
GROQ_API_KEY=your-groq-api-key-here

### 4. Running the App
streamlit run app.py

