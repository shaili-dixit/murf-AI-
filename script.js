let mediaRecorder, stream;
let audioChunks = [];

// Existing Day 1–7 UI elements
const startBtn = document.getElementById("start");
const stopBtn = document.getElementById("stop");
const audioPlayback = document.getElementById("audioPlayback");
const statusMsg = document.getElementById("status");
const transcriptOutput = document.getElementById("transcriptOutput");

// NEW Day 9 UI elements
const startDay9Btn = document.getElementById("startDay9");
const stopDay9Btn = document.getElementById("stopDay9");
const day9Audio = document.getElementById("day9Audio");
const day9Status = document.getElementById("day9Status");
const day9Reply = document.getElementById("day9Reply");

// ----------------------------
// Day 10: Chat History Support
// ----------------------------
let sessionId = localStorage.getItem("chat_session_id");
if (!sessionId) {
  sessionId = Math.random().toString(36).substring(2, 15);
  localStorage.setItem("chat_session_id", sessionId);
  console.log("New session created:", sessionId);
} else {
  console.log("Using existing session:", sessionId);
}

// ----------------------------
// OLD FLOW (process-to-murf)
// ----------------------------
startBtn.onclick = async () => {
  stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = event => {
    if (event.data.size > 0) {
      audioChunks.push(event.data);
    }
  };

  mediaRecorder.onstop = async () => {
    statusMsg.textContent = "Processing audio...";

    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.wav");

    try {
      const response = await fetch("http://127.0.0.1:8000/process-to-murf", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.error) {
        statusMsg.textContent = "❌ Error: " + data.error;
        return;
      }

      audioPlayback.src = data.murf_audio_url;
      audioPlayback.play();

      transcriptOutput.textContent = data.transcript || "No text found.";
      statusMsg.textContent = "✅ Murf voice generated!";
    } catch (err) {
      statusMsg.textContent = "❌ Upload failed. Check your backend.";
      console.error(err);
    }
  };

  mediaRecorder.start();
  startBtn.disabled = true;
  stopBtn.disabled = false;
  statusMsg.textContent = "Recording...";
};

stopBtn.onclick = () => {
  mediaRecorder.stop();
  stream.getTracks().forEach(track => track.stop());
  startBtn.disabled = false;
  stopBtn.disabled = true;
  statusMsg.textContent = "Stopped. Processing...";
};

// ----------------------------
// NEW FLOW (Day 9 + Day 10)
// ----------------------------
startDay9Btn.onclick = async () => {
  stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  audioChunks = [];

  mediaRecorder.ondataavailable = event => {
    if (event.data.size > 0) {
      audioChunks.push(event.data);
    }
  };

  mediaRecorder.onstop = async () => {
    day9Status.textContent = "Processing ...";

    const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
    const formData = new FormData();
    formData.append("file", audioBlob, "day9.wav");

    try {
      const response = await fetch(`http://127.0.0.1:8000/agent/chat/${sessionId}`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (data.error) {
        day9Status.textContent = "❌ Error: " + data.error;
        return;
      }

      // Append messages to chat view instead of plain transcript
      appendChatMessage("user", data.transcript || "No transcript.");
      appendChatMessage("bot", data.llm_reply || "No reply.");

      // Still update LLM reply section (optional, for clarity)
      day9Reply.textContent = data.llm_reply || "No reply.";

      // Play Murf-generated voice
      day9Audio.src = data.murf_audio_url;
      day9Audio.play();

      day9Status.textContent = "✅ Completed!";
    } catch (err) {
      day9Status.textContent = "❌ Pipeline failed. Check your backend.";
      console.error(err);
    }
  };

  mediaRecorder.start();
  startDay9Btn.disabled = true;
  stopDay9Btn.disabled = false;
  day9Status.textContent = "Recording...";
};

stopDay9Btn.onclick = () => {
  mediaRecorder.stop();
  stream.getTracks().forEach(track => track.stop());
  startDay9Btn.disabled = false;
  stopDay9Btn.disabled = true;
  day9Status.textContent = "Stopped. Processing...";
};

// ----------------------------
// Chat UI helper function
// ----------------------------
function appendChatMessage(sender, text) {
  const chatContainer = document.getElementById("chatContainer");
  const msg = document.createElement("div");

  msg.style.padding = "8px";
  msg.style.margin = "5px 0";
  msg.style.borderRadius = "8px";
  msg.style.maxWidth = "80%";
  msg.style.wordWrap = "break-word";

  if (sender === "user") {
    msg.style.backgroundColor = "#DCF8C6";
    msg.style.alignSelf = "flex-end";
    msg.textContent = "You: " + text;
  } else {
    msg.style.backgroundColor = "#E6E6E6";
    msg.style.alignSelf = "flex-start";
    msg.textContent = "AI: " + text;
  }

  msg.style.display = "inline-block";
  const wrapper = document.createElement("div");
  wrapper.style.display = "flex";
  wrapper.style.justifyContent = sender === "user" ? "flex-end" : "flex-start";
  wrapper.appendChild(msg);

  chatContainer.appendChild(wrapper);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}
