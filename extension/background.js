chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {

    if (request.type === "GET_SCORE") {

        fetch("http://127.0.0.1:8000/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(request.data)
        })
        .then(res => {
            if (!res.ok) throw new Error("API failed");
            return res.json();
        })
        .then(data => {
            console.log("✅ Background received:", data);
            sendResponse(data);
        })
        .catch(err => {
            console.error("❌ API error:", err);
            sendResponse({ error: true });
        });

        return true; // 🔥 MUST BE INSIDE if block
    }
});