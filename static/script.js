document.addEventListener("DOMContentLoaded", () => {
    const chatbox = document.getElementById("chatbox");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    // Function to append messages to the chatbox
    const appendMessage = (sender, message) => {
        const messageDiv = document.createElement("div");
        messageDiv.textContent = `${sender}: ${message}`;
        if (sender === "You") {
            messageDiv.style.textAlign = "right"; // Align user messages to the right
        }
        chatbox.appendChild(messageDiv);
        chatbox.scrollTop = chatbox.scrollHeight; // Auto-scroll to the bottom
    };

    // Event listener for send button
    sendButton.addEventListener("click", async () => {
        const message = userInput.value.trim();
        if (!message) return;
        appendMessage("You", message); // Display user's message
        userInput.value = "";

        try {
            const response = await fetch("https://aworld-chat.onrender.com/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ prompt: message }),
            });
            const data = await response.json();
            if (data.response) {
                appendMessage("GPT", data.response); // Display GPT's response
            } else {
                appendMessage("GPT", "An error occurred, please try again.");
            }
        } catch (error) {
            appendMessage("GPT", "Error: Unable to connect to the server.");
        }
    });

    // Allow "Enter" key to send messages
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendButton.click();
        }
    });
});

