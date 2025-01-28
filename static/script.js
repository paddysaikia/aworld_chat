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
        console.log("Fetching chat response with message:", message);

        const response = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ prompt: message }),
        });

        if (!response.ok) {
            console.error(`Error: ${response.status} ${response.statusText}`);
            throw new Error(`HTTP Error: ${response.status}`);
        }

        const data = await response.json();
        console.log("Parsed API Response:", data);
        return data.choices[0].message.content; // Update this path based on your response structure
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
