from flask import Flask, render_template, request
import os
import re
from langchain_community.chat_models import ChatOpenAI  # ✅ Updated import
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from datetime import datetime

app = Flask(__name__)

# ✅ Set your OpenRouter API Key
os.environ["OPENAI_API_KEY"] = "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"

# ✅ Initialize the model
llm = ChatOpenAI(
    temperature=0.7,
    model_name="openai/gpt-3.5-turbo",
    openai_api_base="https://openrouter.ai/api/v1",
)

# ✅ Flashcard Generator Prompt
flashcard_prompt = PromptTemplate(
    input_variables=["topic", "exam_type", "difficulty"],
    template="""
You are an expert {exam_type} tutor creating comprehensive study materials.

Topic: **{topic}**
Difficulty Level: {difficulty}
Current Date: """ + datetime.now().strftime("%Y-%m-%d") + """

1. Summary (150-200 words)
2. Key Formulas (if applicable)
3. 7 flashcards (Q: ... A: ...)
4. 21 quiz questions:
   - 7 Easy
   - 7 Medium
   - 7 Hard
   - Each MCQ with 4 options, correct answer (**Answer: X**) and explanation.

Format:
## Summary
## Key Formulas
## Flashcards
## Quiz Questions
### Easy
### Medium
### Hard
"""
)
flashcard_chain = LLMChain(llm=llm, prompt=flashcard_prompt)

# ✅ Quiz-Only Prompt
quiz_prompt = PromptTemplate(
    input_variables=["topic", "exam_type", "difficulty"],
    template="""
Generate 15 high-quality MCQs for {exam_type} topic: **{topic}**
Difficulty Level: {difficulty}
Current Date: """ + datetime.now().strftime("%Y-%m-%d") + """

Format each as:
Q1: ...
A. ...
B. ...
C. ...
D. ...
**Answer: B**
Explanation: ...
"""
)
quiz_chain = LLMChain(llm=llm, prompt=quiz_prompt)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        topic = request.form["topic"]
        exam_type = request.form.get("exam_type", "JEE")
        difficulty = request.form.get("difficulty", "Medium")
        response = flashcard_chain.run(topic=topic, exam_type=exam_type, difficulty=difficulty)
        return render_template("index.html", response=response, exam_type=exam_type)
    return render_template("index.html")

@app.route("/self_assess", methods=["GET", "POST"])
def self_assess():
    if request.method == "POST":
        topic = request.form["topic"]
        exam_type = request.form.get("exam_type", "JEE")
        difficulty = request.form.get("difficulty", "Medium")
        quiz_md = quiz_chain.run(topic=topic, exam_type=exam_type, difficulty=difficulty)

        pattern = r"Q\d+:(.*?)\nA\.(.*?)\nB\.(.*?)\nC\.(.*?)\nD\.(.*?)\n\*\*Answer: ([A-D])\*\*\nExplanation: (.*?)(?=\nQ|\Z)"
        matches = re.findall(pattern, quiz_md, re.DOTALL)

        quiz_data = []
        for idx, match in enumerate(matches):
            qtext, a, b, c, d, correct, expl = map(str.strip, match)
            quiz_data.append({
                "id": idx,
                "question": qtext,
                "options": [a, b, c, d],
                "correct": correct,
                "explanation": expl
            })

        return render_template("quiz.html", quiz=quiz_data, topic=topic, exam_type=exam_type)

    return render_template("self_assess.html")

@app.route("/result", methods=["POST"])
def result():
    total = int(request.form["total"])
    score = 0
    results = []

    for i in range(total):
        selected = request.form.get(f"q{i}", "")
        correct = request.form.get(f"correct{i}")
        explanation = request.form.get(f"expl{i}")
        question = request.form.get(f"qtext{i}")
        options = [
            request.form.get(f"opt{i}_0"),
            request.form.get(f"opt{i}_1"),
            request.form.get(f"opt{i}_2"),
            request.form.get(f"opt{i}_3")
        ]
        correct_index = "ABCD".index(correct)
        correct_text = options[correct_index]

        results.append({
            "question": question,
            "selected": selected,
            "correct": correct,
            "is_correct": selected == correct,
            "correct_text": correct_text,
            "explanation": explanation
        })
        if selected == correct:
            score += 1

    return render_template("result.html", score=score, total=total, results=results)

if __name__ == "__main__":
    app.run(debug=True)
