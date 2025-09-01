document.getElementById("analyzeBtn").addEventListener("click", () => {
    const text = document.getElementById("inputText").value;
    const resultDiv = document.getElementById("result");

    if (!text) {
        resultDiv.innerHTML = "Please enter some text.";
        return;
    }

    // Call your Flask API endpoint
    fetch("http://127.0.0.1:5000/analyze", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
    })
    .then(response => response.json())
    .then(data => {
        resultDiv.innerHTML = `
            <strong>Verdict:</strong> ${data.label} <br>
            <strong>Confidence:</strong> ${(data.confidence*100).toFixed(2)}%
        `;
    })
    .catch(err => {
        resultDiv.innerHTML = "Error: Unable to reach API.";
        console.error(err);
    });
});

document.getElementById("goWebsiteBtn").addEventListener("click", () => {
    chrome.tabs.create({ url: "http://127.0.0.1:5000" });
});
