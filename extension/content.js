// ============================
// SINGLE RUN GUARD
// ============================
if (window.safeShopInjected) {
    console.log("⛔ Already injected, skipping...");
} else {
    window.safeShopInjected = true;

    console.log("SafeShop loaded");

    // ============================
    // GLOBAL STYLES
    // ============================
    const style = document.createElement("style");
    style.innerHTML = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }`;
    document.head.appendChild(style);

    // ============================
    // HELPERS
    // ============================
    function getRiskColor(risk) {
        if (risk === "high") return "#ff4d4f";
        if (risk === "medium" || risk === "moderate") return "#ffb300";
        return "#52c41a";
    }

    function beautifyReason(r) {
        return r
            .replace("Refined/processed oils used", "Uses refined oils")
            .replace("Unknown additive present", "Contains unidentified additive")
            .replace("High salt", "High salt (BP risk)");
    }

    function getSeverity(reason) {
        const r = reason.toLowerCase();

        if (r.includes("trans fat") || r.includes("harmful") || r.includes("msg"))
            return "high";

        if (r.includes("processed") || r.includes("additive") || r.includes("refined"))
            return "medium";

        return "low";
    }

    function groupReasons(reasons) {
        const grouped = { high: [], medium: [], low: [] };

        reasons.forEach(r => {
            const severity = getSeverity(r);
            grouped[severity].push(r);
        });

        return grouped;
    }

    // ============================
    // 🧠 DYNAMIC ADVICE ENGINE
    // ============================
    function getDynamicAdvice(result) {

        const advice = [];
        const reasons = (result.reasons || []).join(" ").toLowerCase();

        // 🚨 TRANS FAT
        if (reasons.includes("trans fat")) {
            advice.push("❌ Avoid frequent consumption (heart risk)");
            advice.push("✔️ Very occasional intake only");
        }

        // 🧂 HIGH SALT
        if (reasons.includes("high sodium") || reasons.includes("high salt")) {
            advice.push("⚠️ Limit intake (BP risk)");
        }

        // 🍜 MSG / FLAVOUR ENHANCERS
        if (result.flags?.msg) {
            advice.push("⚠️ Contains flavour enhancers (may trigger sensitivity)");
        }

        // 🏭 ULTRA PROCESSED
        if (result.flags?.ultra_processed) {
            advice.push("⚠️ Highly processed — avoid daily consumption");
        }

        // 🧪 ADDITIVES COUNT
        const additivesCount =
            (result.additives?.primary?.length || 0) +
            (result.additives?.generic?.length || 0);

        if (additivesCount > 5) {
            advice.push("⚠️ Contains many additives — prefer natural foods");
        }

        // 📊 SCORE BASE FALLBACK
        if (advice.length === 0) {
            if (result.score < 40) {
                advice.push("⚠️ Occasional consumption recommended");
            } else {
                advice.push("✔️ Safe in moderation");
            }
        }

        return advice;
    }

    // ============================
    // TOOLTIP
    // ============================
    function createTooltip() {
        let tooltip = document.getElementById("safe-tooltip");

        if (!tooltip) {
            tooltip = document.createElement("div");
            tooltip.id = "safe-tooltip";

            Object.assign(tooltip.style, {
                position: "fixed",
                background: "#1a1a1a",
                color: "white",
                padding: "8px 10px",
                borderRadius: "8px",
                fontSize: "12px",
                zIndex: "9999999",
                pointerEvents: "none",
                opacity: "0",
                transition: "opacity 0.2s ease",
                boxShadow: "0 2px 10px rgba(0,0,0,0.4)"
            });

            document.body.appendChild(tooltip);
        }

        return tooltip;
    }

    // ============================
    // GET DATA
    // ============================
    function getProductName() {
        let el = document.querySelector('h1') 
              || document.querySelector('[class*="Title"]') 
              || document.querySelector('[class*="name"]');

        return el ? el.innerText.trim() : null;
    }

    function getNutritionText() {
        let text = document.body.innerText;
        let match = text.match(/Nutritional[\s\S]*?(?=How to Use|Other Product Info|$)/i);
        return match ? match[0] : "";
    }

    function getIngredientsText() {

        const label = [...document.querySelectorAll("span")]
            .find(el => el.innerText.trim().toLowerCase() === "ingredients");

        if (!label) return "";

        let wrapper = label.closest("div");
        if (!wrapper) return "";

        let next = wrapper.nextElementSibling;
        if (!next) return "";

        let bullets = next.querySelector(".bullets");

        if (!bullets) return next.innerText.trim();

        return bullets.innerText.replace(/["']/g, "").trim();
    }

    // ============================
    // API CALL
    // ============================
    function getScoreFromAPI(productData) {
        return new Promise((resolve) => {
            chrome.runtime.sendMessage(
                { type: "GET_SCORE", data: productData },
                (response) => {
                    if (chrome.runtime.lastError) {
                        console.error("❌ Runtime error:", chrome.runtime.lastError);
                        resolve(null);
                        return;
                    }
                    resolve(response || null);
                }
            );
        });
    }

    // ============================
    // UI
    // ============================
function renderUI(result) {

    if (!result) return;

    let existing = document.getElementById("safe-shop-box");
    if (existing) existing.remove();

    let isExpanded = false;

    const score = result.score;
    const verdict = result.verdict;
    const reasons = result.reasons || [];
    const healthFlags = result.health_flags || [];

    const additives = [
        ...(result.additives?.primary || []),
        ...(result.additives?.generic || [])
    ];

    const nutrition = result.parsed_nutrition || {};

    const scoreColor =
        score >= 70 ? "#22c55e" :
        score >= 40 ? "#f59e0b" :
        "#ef4444";

    const glow = score < 40
        ? "0 0 25px rgba(239,68,68,0.4)"
        : "0 0 15px rgba(0,0,0,0.3)";

    const topReasons = reasons.slice(0, 3);
    const advice = getDynamicAdvice(result);

    function getLevel(value, type) {
        if (type === "sodium") {
            if (value > 500) return { label: "High", value: 100 };
            if (value > 200) return { label: "Medium", value: 60 };
            return { label: "Low", value: 30 };
        }
        if (type === "sugar") {
            if (value > 20) return { label: "High", value: 100 };
            if (value > 10) return { label: "Medium", value: 60 };
            return { label: "Low", value: 30 };
        }
        if (type === "fat") {
            if (value > 10) return { label: "High", value: 100 };
            if (value > 5) return { label: "Medium", value: 60 };
            return { label: "Low", value: 30 };
        }
    }

    const sodium = getLevel(nutrition.sodium_mg || 0, "sodium");
    const sugar = getLevel(nutrition.sugar_g || 0, "sugar");
    const fat = getLevel(nutrition.saturated_fat_g || 0, "fat");

    let box = document.createElement("div");
    box.id = "safe-shop-box";

    box.innerHTML = `
    <div id="safe-main" style="
        position: fixed;
        top: 90px;
        right: 20px;
        width: 300px;
        padding: 16px;
        border-radius: 16px;
        background: rgba(20,20,20,0.55);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: ${glow};
        color: white;
        font-family: Inter, Arial;
        cursor: pointer;
        transition: all 0.3s ease;
        z-index: 999999;
    ">

        <!-- HEADER -->
        <div style="display:flex;justify-content:space-between;align-items:center;">

            <div style="display:flex;align-items:center;gap:12px;">

                <div style="
                    width:52px;
                    height:52px;
                    border-radius:50%;
                    background: conic-gradient(
                        ${scoreColor},
                        ${scoreColor} ${score}%,
                        rgba(255,255,255,0.08) ${score}%
                    );
                    box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
                    display:flex;
                    align-items:center;
                    justify-content:center;
                    font-size:13px;
                    font-weight:600;
                ">
                    ${Math.round(score)}
                </div>

                <div>
                    <div style="font-size:14px;font-weight:600;">Safe Score</div>
                    <div style="font-size:12px;opacity:0.6;">${verdict}</div>
                </div>
            </div>

            <div id="safe-arrow" style="
                font-size:16px;
                transition: transform 0.3s ease;
            ">⌄</div>
        </div>

        <!-- DETAILS -->
        <div id="safe-details" style="
            max-height:0;
            overflow:hidden;
            opacity:0;
            transition: all 0.35s ease;
            margin-top:0;
        ">

            ${createCard("Health Risks", healthFlags.map(f => f.message), "#f87171")}

            ${createNutritionCard()}

            ${createCard("Key Issues", topReasons.map(r => beautifyReason(r)))}

            ${createCard("Advice", advice)}

            ${createCard("Additives (" + additives.length + ")", additives.map(a => `
                <span class="safe-additive"
                    data-name="${a.name}"
                    data-code="${a.code || ''}"
                    data-risk="${a.risk}"
                    data-category="${a.category || ''}"
                    style="color:${getRiskColor(a.risk)};cursor:pointer;">
                    ${a.name}
                </span>
            `))}
        </div>
    </div>
    `;

    document.body.appendChild(box);

    function createCard(title, items, color = "#ffffff") {
        if (!items || items.length === 0) return "";

        return `
        <div style="
            background: rgba(255,255,255,0.03);
            padding: 10px;
            border-radius: 10px;
            margin-top:10px;
        ">
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;color:${color}">
                ${title}
            </div>
            ${items.map(i => `
                <div style="font-size:12px;opacity:0.8;margin-bottom:3px;">
                    ${i}
                </div>
            `).join("")}
        </div>`;
    }

    function createNutritionCard() {
        return `
        <div style="
            background: rgba(255,255,255,0.03);
            padding: 10px;
            border-radius: 10px;
            margin-top:10px;
        ">
            <div style="font-size:12px;font-weight:600;margin-bottom:6px;">
                Nutrition Impact
            </div>

            ${createBar("Sodium", sodium)}
            ${createBar("Sugar", sugar)}
            ${createBar("Fat", fat)}
        </div>`;
    }

    function createBar(label, obj) {
        return `
        <div style="margin-bottom:6px;">
            <div style="font-size:11px;opacity:0.7;">
                ${label} • ${obj.label}
            </div>
            <div style="
                height:6px;
                background: rgba(255,255,255,0.08);
                border-radius:6px;
                overflow:hidden;
            ">
                <div style="
                    width:${obj.value}%;
                    height:100%;
                    background:${obj.label === "High" ? "#ef4444" : obj.label === "Medium" ? "#f59e0b" : "#22c55e"};
                    transition: width 0.6s ease;
                    border-radius:6px;
                "></div>
            </div>
        </div>`;
    }

    // ===== TOGGLE (FINAL FIXED)
    const main = box.querySelector("#safe-main");
    const details = box.querySelector("#safe-details");
    const arrow = box.querySelector("#safe-arrow");

    main.addEventListener("click", () => {
        isExpanded = !isExpanded;

        if (isExpanded) {
            details.style.maxHeight = "70vh";   // ✅ responsive
            details.style.overflowY = "auto";   // ✅ scroll
            details.style.opacity = "1";
            details.style.marginTop = "12px";
        } else {
            details.style.maxHeight = "0";
            details.style.overflowY = "hidden";
            details.style.opacity = "0";
            details.style.marginTop = "0";
        }

        arrow.style.transform = isExpanded ? "rotate(180deg)" : "rotate(0deg)";
    });

    // ===== TOOLTIP
    const tooltip = createTooltip();

    document.querySelectorAll(".safe-additive").forEach(el => {
        el.addEventListener("mousemove", (e) => {

            tooltip.innerHTML = `
                <b>${el.dataset.name}</b><br/>
                ${el.dataset.code ? `(${el.dataset.code.toUpperCase()})<br/>` : ""}
                Risk: ${el.dataset.risk}<br/>
                Category: ${el.dataset.category}
            `;

            let x = e.clientX + 10;
            let y = e.clientY + 10;

            if (x + 200 > window.innerWidth) x -= 220;
            if (y + 80 > window.innerHeight) y -= 100;

            tooltip.style.left = x + "px";
            tooltip.style.top = y + "px";
            tooltip.style.opacity = "1";
        });

        el.addEventListener("mouseleave", () => {
            tooltip.style.opacity = "0";
        });
    });
}
    // ============================
    // MAIN
    // ============================
    async function runSafeShop() {

    const name = getProductName();
    if (!name) return;

    const ingredientsText = getIngredientsText(); // may be empty
    const nutritionText = getNutritionText();

    const data = {
        name,
        nutrition_text: nutritionText || "",
        ingredients: ingredientsText || ""
    };

    const result = await getScoreFromAPI(data);

    console.log("API:", result);

    if (!result) return;

    renderUI(result);
}

    // ============================
    // EXECUTION
    // ============================
    let attempts = 0;

    const interval = setInterval(() => {

        if (attempts > 5) {
            clearInterval(interval);
            return;
        }

        const name = getProductName();
        const nutrition = getNutritionText();

        // 🔥 NEW LOGIC: run if ANY useful data exists
        if (name && (nutrition || getIngredientsText())) {
            runSafeShop();
            clearInterval(interval);
        }

        attempts++;

    }, 1500);
}