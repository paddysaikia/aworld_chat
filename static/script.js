const chatbox = document.getElementById("chatbox");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

// Append a message to the chatbox
const appendMessage = (sender, message) => {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender === "You" ? "user" : "bot");
    messageDiv.textContent = message;
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight; // Auto-scroll to the bottom
};

// Show introductory message when the chatbox is initialized
window.addEventListener("DOMContentLoaded", () => {
    appendMessage("A WORLD", "Hello! I'm Ava, here to support you in exploring 'A World.' How can I assist you today?");
});

// Fetch chat response from the server
const fetchChatResponse = async (message) => {
    try {
        const response = await fetch("https://aworld-chat.onrender.com/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer YOUR_API_SECRET_KEY" // Add the correct API key here
            },
            body: JSON.stringify({ prompt: message }),
        });
        if (!response.ok) {
            console.error(`Error: ${response.status} ${response.statusText}`);
            throw new Error(`HTTP Error: ${response.status}`);
        }
        const data = await response.json();
        console.log("API Response:", data);
        return data.response;
    } catch (error) {
        console.error("Error fetching chat response:", error);
        return "Sorry, something went wrong. Please try again later.";
    }
};

// Handle send button click
sendButton.addEventListener("click", async () => {
    const message = userInput.value.trim();
    if (!message) return;
    appendMessage("You", message);
    userInput.value = "";

    const aiResponse = await fetchChatResponse(message);
    appendMessage("A WORLD", aiResponse);
});

// Send message on Enter key press
userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendButton.click();
});
