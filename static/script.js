const chatbox = document.getElementById("chatbox");
const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");

const appendMessage = (sender, message) => {
    const messageDiv = document.createElement("div");
    messageDiv.textContent = `${sender}: ${message}`;
    chatbox.appendChild(messageDiv);
    chatbox.scrollTop = chatbox.scrollHeight; // Auto-scroll to the bottom
};

const fetchChatResponse = async (message) => {
    try {
        const response = await fetch("https://aworld-chat.onrender.com/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ prompt: message }),
        });
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error("Error fetching chat response:", error);
        return "Sorry, something went wrong. Please try again later.";
    }
};

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
