// ================= GLOBAL STATE =================
let currentRole = "";
let currentIndex = 0;
let currentQuestion = "";
let scores = [];
let questions = [];

// ================= START INTERVIEW =================
window.startInterview = async function () {

    currentRole = document.getElementById("role").value;
    currentIndex = 0;
    scores = [];
    questions = [];

    document.getElementById("chatBox").innerHTML = "";

    addMessage("bot", "🚀 Interview Started");
    addMessage("bot", "🧠 Role: " + currentRole);

    await generateQuestions(currentRole);
    showQuestion();
};

// ================= GENERATE QUESTIONS =================
async function generateQuestions(role) {

    try {

        const res = await fetch("/api/gemini", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt: `Generate 5 interview questions for ${role}. Return ONLY JSON array.`
            })
        });

        const data = await res.json();

        if (!data.candidates || !data.candidates.length) {
            addMessage("bot", "❌ AI failed to generate questions");
            return;
        }

        let text = data.candidates[0].content.parts[0].text;

        // FIXED: Strips out Markdown wrapper blocks (```json ... ```) safely
        const cleanText = text.replace(/```json|```/g, "").trim();
        questions = JSON.parse(cleanText);

        // FIXED: Guardrail check to verify the AI actually sent back an array
        if (!Array.isArray(questions) || questions.length === 0) {
            throw new Error("Invalid format: Expected a JSON array.");
        }

        addMessage("bot", "🧠 Questions generated");

    } catch (err) {
        console.error("Error generating questions:", err);
        addMessage("bot", "❌ Error generating questions");
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

    const answer = document.getElementById("answer").value.trim();
    if (!answer) return;

    addMessage("user", answer);
    document.getElementById("answer").value = "";

    try {

        const res = await fetch("/api/gemini", {
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

        const data = await res.json();

        if (!data.candidates || !data.candidates.length) {
            addMessage("bot", "❌ AI failed to evaluate");
            return;
        }

        let text = data.candidates[0].content.parts[0].text;

        // FIXED: Strips out Markdown wrapper blocks safely
        const cleanText = text.replace(/```json|```/g, "").trim();
        let result = JSON.parse(cleanText);

        // FIXED: Force the score to be treated as a number to prevent string concatenation bugs
        const numericScore = Number(result.score);
        scores.push(isNaN(numericScore) ? 0 : numericScore);

        addMessage("bot", "📊 Score: " + result.score);
        addMessage("bot", "💬 " + result.feedback);

        currentIndex++;
        setTimeout(showQuestion, 1200);

    } catch (err) {
        console.error("Error evaluating answer:", err);
        addMessage("bot", "❌ API Error");
    }
};

// ================= FINAL RESULT =================
function showFinalResult() {

    let total = scores.reduce((a, b) => a + b, 0);
    let avg = scores.length ? (total / scores.length).toFixed(1) : 0;

    addMessage("bot", "🏁 Interview Completed");
    addMessage("bot", "📊 Final Score: " + avg);
}

// ================= UI =================
function addMessage(sender, text) {

    const chatBox = document.getElementById("chatBox");

    const msg = document.createElement("div");
    msg.className = sender;
    msg.innerText = text;

    chatBox.appendChild(msg);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// ================= VOICE FIX =================
window.startVoice = function () {

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        alert("Speech not supported");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.start();

    recognition.onresult = function (event) {
        document.getElementById("answer").value =
            event.results[0][0].transcript;
    };

    recognition.onerror = function () {
        addMessage("bot", "❌ Voice error");
    };
};