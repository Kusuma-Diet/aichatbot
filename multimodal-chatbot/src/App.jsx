import React, { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [query, setQuery] = useState("");
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") document.body.classList.add("dark");
  }, [messages]);

  const toggleTheme = () => {
    document.body.classList.toggle("dark");
    const theme = document.body.classList.contains("dark") ? "dark" : "light";
    localStorage.setItem("theme", theme);
  };

  const handleSubmit = async () => {
    if (!query.trim() && !file) {
      alert("Please enter a question or upload an image.");
      return;
    }

    let newMessages = [...messages];
    if (query) {
      newMessages.push({ type: "user", content: query, timestamp: new Date().toLocaleTimeString() });
      setQuery("");
    } else {
      newMessages.push({ type: "user", content: "Uploading image...", timestamp: new Date().toLocaleTimeString() });
    }

    setMessages(newMessages);
    setIsLoading(true);

    const formData = new FormData();
    if (query) formData.append("query", query);
    if (file) formData.append("file", file);

    const res = await fetch("/api/chat", {
  method: "POST",
  body: formData
});

let data;
try {
  data = await res.json();
} catch (e) {
  data = { response: "⚠️ Server error or invalid response. Please try again." };
}

    setIsLoading(false);
    setFile(null);
    document.getElementById("fileInput").value = "";
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        AI Chatbot
        <button className="theme-toggle" onClick={toggleTheme}>🌓</button>
      </div>
      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={msg.type === "user" ? "message-user" : "message-bot"}>
            {msg.type === "bot" && <div className="avatar">🤖</div>}
            <div className={msg.type === "user" ? "message-content-user" : "message-content-bot"}>
              {msg.content}
              <div className="timestamp">{msg.timestamp}</div>
            </div>
            {msg.type === "user" && <div className="avatar">👤</div>}
          </div>
        ))}
        {isLoading && <div className="loading-spinner"></div>}
        <div ref={chatEndRef} />
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          className="input-field"
          onKeyPress={(e) => e.key === "Enter" && handleSubmit()}
        />
        <input
          id="fileInput"
          type="file"
          accept=".jpg,.jpeg,.png"
          onChange={(e) => setFile(e.target.files[0])}
          className="hidden"
        />
        <label htmlFor="fileInput" className="upload-btn">📎</label>
        <button onClick={handleSubmit} className="send-btn" disabled={isLoading}>
          {isLoading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

export default App;
