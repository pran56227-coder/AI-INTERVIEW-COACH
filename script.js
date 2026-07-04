// ================= GLOBAL STATE =================
let currentRole = "";
let currentIndex = 0;
let currentQuestion = "";
let scores = [];
let questions = [];

// UPDATED BACKEND ROUTE TO GROQ
const BACKEND_URL = "/api/groq";

// ================= HELPER: SAFE BUTTON LOADING STATES =================
function setButtonState(actionType, isLoading, defaultText) {
    let btn = null;
    
    if (actionType === "start") {
        btn = document.querySelector("button[onclick*='startInterview']");
    } else if (actionType === "send") {
        btn = document.querySelector("button[onclick*='sendAnswer']");
    }

    if (!btn) return;

    if (isLoading) {
        btn.disabled = true;
        btn.innerText = "⏳ Processing...";
    } else {
        btn.disabled = false;
        btn.innerText = defaultText;
    }
}

// ================= HELPER: SAFELY EXTRACT ERROR STRING =================
function getCleanErrorMessage(errorData) {
    if (!errorData) return "Unknown Error";
    if (typeof errorData === 'string') return errorData;
    if (errorData.message) return String(errorData.message);
    if (errorData.details) return String(errorData.details);
    
    try {
        return JSON.stringify(errorData);
    } catch (e) {
        return String(errorData);
    }
}

// ================= START INTERVIEW =================
window.startInterview = async function () {
    currentRole = document.getElementById("role").value;
    currentIndex = 0;
    scores = [];
    questions = [];

    document.getElementById("chatBox").innerHTML = "";

    addMessage("bot", "🚀 Interview Started");
    addMessage("bot", "🧠 Role: " + currentRole);

    setButtonState("start", true, "🎯 Start Interview");

    await generateQuestions(currentRole);
    
    setButtonState("start", false, "🎯 Start Interview");
    showQuestion();
};

// ================= GENERATE QUESTIONS =================
async function generateQuestions(role) {
    try {
        const res = await fetch(BACKEND_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt: `Generate 5 interview questions for ${role}. Return ONLY JSON array.`
            })
        });

        if (res.status === 429) {
            addMessage("bot", "⏳ API rate limit reached. The AI is a bit busy. Please wait 60 seconds.");
            return;
        }

        const data = await res.json();

        if (data.error) {
            const errorStr = getCleanErrorMessage(data.error);
            addMessage("bot", "❌ Backend Error: " + errorStr);
            return;
        }

        if (!data.candidates || !data.candidates.length) {
            addMessage("bot", "❌ AI failed to generate questions");
            return;
        }

        let text = data.candidates[0].content.parts[0].text;
        const cleanText = text.replace(/```json|```/g, "").trim();
        questions = JSON.parse(cleanText);

        if (!Array.isArray(questions) || questions.length === 0) {
            throw new Error("Invalid format: Expected a JSON array.");
        }

        addMessage("bot", "🧠 Questions generated");

    } catch (err) {
        console.error("Error generating questions:", err);
        addMessage("bot", "❌ Connection timed out or server setup missing. Please try again.");
    }
}

// ================= SHOW QUESTION =================
function showQuestion() {
    currentQuestion = questions[currentIndex];

    if (!currentQuestion) {
        showFinalResult();
        return;
    }

    addMessage("bot", "🎯 Question " + (currentIndex + 1));
    addMessage("bot", currentQuestion);
}

// ================= SEND ANSWER =================
window.sendAnswer = async function () {
    const answerElement = document.getElementById("answer");
    const answer = answerElement ? answerElement.value.trim() : "";
    if (!answer) return;

    setButtonState("send", true, "🚀 Submit");

    addMessage("user", answer);
    if (answerElement) answerElement.value = "";

    try {
        const res = await fetch(BACKEND_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt: `Evaluate this answer:
Role: ${currentRole}
Question: ${currentQuestion}
Answer: ${answer}
Return JSON with score, feedback, improvement, correct_answer`
            })
        });

        if (res.status === 429) {
            addMessage("bot", "⏳ API busy. Retrying submission in 10 seconds...");
            if (answerElement) answerElement.value = answer; 
            setButtonState("send", false, "🚀 Submit");
            setTimeout(window.sendAnswer, 10000);
            return;
        }

        const data = await res.json();

        if (data.error) {
            const errorStr = getCleanErrorMessage(data.error);
            addMessage("bot", "❌ Evaluation Error: " + errorStr);
            setButtonState("send", false, "🚀 Submit");
            return;
        }

        if (!data.candidates || !data.candidates.length) {
            addMessage("bot", "❌ AI failed to evaluate");
            setButtonState("send", false, "🚀 Submit");
            return;
        }

        let text = data.candidates[0].content.parts[0].text;
        const cleanText = text.replace(/```json|
