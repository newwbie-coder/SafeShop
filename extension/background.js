function postJson(path, data) {
    return fetch("http://127.0.0.1:8000" + path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    }).then(async (res) => {
        const body = await res.json().catch(() => ({ error: true }));
        if (!res.ok && body.error == null) {
            body.error = true;
        }
        return body;
    });
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {

    if (request.type === "GET_SCORE") {
        postJson("/analyze", request.data)
            .then((data) => sendResponse(data))
            .catch((err) => {
                console.error("SafeShop API error:", err);
                sendResponse({ error: true });
            });
        return true;
    }

    if (request.type === "GET_OCR") {
        postJson("/analyze_image", request.data)
            .then((data) => sendResponse(data))
            .catch((err) => {
                console.error("SafeShop OCR error:", err);
                sendResponse({ error: true });
            });
        return true;
    }

    if (request.type === "SEND_FEEDBACK") {
        postJson("/feedback", request.data)
            .then((data) => sendResponse(data))
            .catch((err) => {
                console.error("SafeShop feedback error:", err);
                sendResponse({ error: true });
            });
        return true;
    }
});
