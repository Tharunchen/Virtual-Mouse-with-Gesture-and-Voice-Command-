// ====== Voice Bot Frontend (clean) ======

// Elements
const chatBoxEl   = document.getElementById("chat-box");
const userInputEl = document.getElementById("userInput");
const voiceSelEl  = document.getElementById("voiceSelect");

// ---------- Speech Synthesis (Bot talk-back) ----------
let voices = [];
let selectedVoice = null;

function loadVoices() {
  voices = window.speechSynthesis.getVoices();
  if (!voiceSelEl) return;

  voiceSelEl.innerHTML = "";
  voices.forEach((v, i) => {
    const opt = document.createElement("option");
    opt.value = String(i);
    opt.textContent = v.name + (v.lang ? ` (${v.lang})` : "");
    voiceSelEl.appendChild(opt);
  });

  // Default to the first available voice
  if (voices.length > 0) {
    selectedVoice = voices[0];
    voiceSelEl.value = "0";
  }
}

// Populate voices (some browsers fire this async)
window.speechSynthesis.onvoiceschanged = loadVoices;
if (window.speechSynthesis.getVoices().length) {
  loadVoices();
}

voiceSelEl?.addEventListener("change", function () {
  const idx = parseInt(this.value, 10);
  selectedVoice = voices[idx] || null;
});

// Expose to Python: speak(text)
eel.expose(speak);
function speak(text) {
  console.log("Speaking:", text);
  const utter = new SpeechSynthesisUtterance(text);
  if (selectedVoice) {
    console.log("Using voice:", selectedVoice.name, selectedVoice.lang);
    utter.voice = selectedVoice;
  } else {
    console.warn("No voice selected!");
  }
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utter);
}

// ---------- Chat UI helpers ----------
function addMessage(sender, text, cls) {
  const msgDiv = document.createElement("div");
  msgDiv.classList.add("message", cls);
  msgDiv.innerText = (sender === "Bot" ? "🤖 " : "🧑 ") + text;
  chatBoxEl.appendChild(msgDiv);
  chatBoxEl.scrollTop = chatBoxEl.scrollHeight;
}

// Expose to Python: addMsgToChat(msg)
eel.expose(addMsgToChat);
function addMsgToChat(msg) {
  console.log("Message from Python:", msg);
  // Python already calls eel.speak(msg), so we don't auto-speak here
}

// Optional typing indicators (used by your Python earlier)
eel.expose(showTypingIndicator);
function showTypingIndicator() {
  const typing = document.createElement("div");
  typing.id = "typing";
  typing.classList.add("typing");
  typing.innerText = "🤖 Bot is typing...";
  chatBoxEl.appendChild(typing);
  chatBoxEl.scrollTop = chatBoxEl.scrollHeight;
}

eel.expose(hideTypingIndicator);
function hideTypingIndicator() {
  const typing = document.getElementById("typing");
  if (typing) typing.remove();
}


// ---------- Sending text ----------
function sendMessage() {
  const msg = userInputEl.value.trim();
  if (!msg) return;

  addMessage("You", msg, "user-msg");
  eel.getUserInput(msg);
  userInputEl.value = "";
}

// Keep Enter-to-send working
userInputEl.addEventListener("keypress", function (e) {
  if (e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
});

// ---------- Speech Recognition (Mic) ----------
let recognition = null;
let recognizing = false;

(function setupRecognition() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    console.warn("SpeechRecognition not supported in this browser.");
    return;
  }
  recognition = new SR();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onstart = function () {
    recognizing = true;
  };
  recognition.onend = function () {
    recognizing = false;
  };
  recognition.onresult = function (event) {
    try {
      const transcript = event.results[0][0].transcript;
      addMessage("You", transcript, "user-msg");
      eel.getUserInput(transcript);
    } catch (e) {
      console.error("onresult error:", e);
    }
  };
  recognition.onerror = function (event) {
    console.error("Speech recognition error:", event.error);
    // common: "no-speech", "audio-capture", "not-allowed"
    recognizing = false;
  };
})();

// Called by your mic button: <button onclick="startListening()">🎤</button>
eel.expose(startListening);
function startListening() {
  if (!recognition) return;
  if (recognizing) return;
  recognition.start();
}

eel.expose(stopListening);
function stopListening() {
  if (!recognition) return;
  if (recognizing) recognition.stop();
}

  eel.expose(closeWindow);
  function closewindow() {
  window.close();
}
// Keep global access for your inline onclick handlers
window.sendMessage = sendMessage;
window.startListening = startListening;
