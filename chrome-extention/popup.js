document.addEventListener("DOMContentLoaded", () => {
    const analyzeBtn = document.getElementById("analyzeBtn");
    const goWebsiteBtn = document.getElementById("goWebsiteBtn");
    const resultDiv = document.getElementById("result");
    const inputField = document.getElementById("inputText");
    const API_URL = "http://127.0.0.1:5000/analyze";

    const showMessage = (message) => {
        resultDiv.innerHTML = message;
    };

    const analyzeText = async () => {
        const text = inputField.value.trim();
        if (!text) {
            showMessage("⚠️ Please enter some text.");
            return;
        }

        showMessage("⏳ Analyzing...");

        try {
            const response = await fetch(API_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });

            const data = await response.json();

            if (data.error) {
                showMessage(`❌ Error: ${data.error}`);
                return;
            }

            const { label, confidence, explanation } = data;
            if (label && confidence !== undefined) {
                showMessage(`
                    ✅ <strong>Verdict:</strong> ${label} <br>
                    📊 <strong>Confidence:</strong> ${(confidence * 100).toFixed(2)}% <br>
                    💡 <strong>Explanation:</strong> ${explanation || "No explanation available."}
                `);
            } else {
                showMessage("⚠️ Unexpected response from server.");
                console.warn("Unexpected API response:", data);
            }
        } catch (err) {
            showMessage("❌ Error: Unable to connect to API. Make sure Flask server is running.");
            console.error("Fetch error:", err);
        }
    };

    analyzeBtn.addEventListener("click", analyzeText);
    goWebsiteBtn.addEventListener("click", () => {
        chrome.tabs.create({ url: "http://127.0.0.1:5000" });
    });
});
