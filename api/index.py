let currentRole = "";
let currentIndex = 0;
let currentQuestion = "";
let scores = [];
let questions = [];

const BACKEND_URL = "/api/groq";

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

async function generateQuestions(role) {
    try {
        const res = await fetch(BACKEND_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt: "Generate 5 interview questions for " + role + ". Return ONLY JSON array."
            })
        });

        if (res.status === 429) {
            addMessage("bot", "⏳ API rate limit reached. Please wait 60 seconds.");
            return;
        }

        const data = await res.json();

        if (data.error) {
            addMessage("bot", "❌ Backend Error: " + getCleanErrorMessage(data.error));
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
            throw new Error("Expected a JSON array.");
        }

        addMessage("bot", "🧠 Questions generated");

    } catch (err) {
        console.error(err);
        addMessage("bot", "❌ Connection issue or server setup missing.");
    }
}

function showQuestion() {
    currentQuestion = questions[currentIndex];
    if (!currentQuestion) {
        showFinalResult();
        return;
    }
    addMessage("bot", "🎯 Question " + (currentIndex + 1));
    addMessage("bot", currentQuestion);
}

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
                prompt: "Evaluate this answer:\nRole: " + currentRole + "\nQuestion: " + currentQuestion + "\nAnswer: " + answer + "\nReturn JSON with score, feedback, improvement, correct_answer"
            })
        });

        if (res.status === 429) {
            addMessage("bot", "⏳ API busy. Retrying in 10 seconds...");
            if (answerElement) answerElement.value = answer; 
            setButtonState("send", false, "🚀 Submit");
            setTimeout(window.sendAnswer, 10000);
            return;
        }

        const data = await res.json();

        if (data.error) {
            addMessage("bot", "❌ Evaluation Error: " + getCleanErrorMessage(data.error));
            return;
        }

        let text = data.candidates[0].content.parts[0].text;
        const cleanText = text.replace(/```json|```/g, "").trim();
        let result = JSON.parse(cleanText);

        const numericScore = Number(result.score);
        scores.push(isNaN(numericScore) ? 0 : numericScore);

        addMessage("bot", "📊 Score: " + result.score);
        addMessage("bot", "💬 " + result.feedback);

        currentIndex++;
        setTimeout(showQuestion, 1200);

    } catch (err) {
        console.error(err);
        addMessage("bot", "❌ API Error occurred processing evaluation.");
    } finally {
        setButtonState("send", false, "🚀 Submit");
    }
};

function showFinalResult() {
    let total = scores.reduce((a, b) => a + b, 0);
    let avg = scores.length ? (total / scores.length).toFixed(1) : 0;
    addMessage("bot", "🏁 Interview Completed");
    addMessage("bot", "📊 Final Score: " + avg);
}

function addMessage(sender, text) {
    const chatBox = document.getElementById("chatBox");
    if (!chatBox) return;

    const msg = document.createElement("div");
    msg.className = sender;
    msg.innerText = text;
    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

let recognition = null; 
window.startVoice = function () {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Speech recognition is not supported on this browser. Try Chrome.");
        return;
    }

    if (recognition) {
        try { recognition.abort(); } catch(e) {}
    }

    recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = false; 

    addMessage("bot", "🎙️ Listening...");

    recognition.onresult = function (event) {
        if (event.results && event.results[0] && event.results[0][0]) {
            document.getElementById("answer").value = event.results[0][0].transcript;
        }
    };

    recognition.onerror = function (event) {
        console.error(event.error);
        if (event.error === 'not-allowed') {
            addMessage("bot", "❌ Microphone permission denied.");
        } else {
            addMessage("bot", "❌ Voice error: " + event.error);
        }
    };

    try {
        recognition.start();
    } catch (err) {
        console.error(err);
    }
};
