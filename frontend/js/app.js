// ======================================================
// Agentic RAG Frontend
// ======================================================

const API_BASE = "http://127.0.0.1:8000";


// ======================================================
// VIEW NAVIGATION
// ======================================================

const navItems = document.querySelectorAll(".nav-item");
const views = document.querySelectorAll(".view");

const pageTitles = {
    workspace: "Research Workspace",
    graph: "Knowledge Graph",
    vectors: "Vector Projection",
    compare: "Multi-Paper Compare",
    ingestion: "Document & OCR Ingestion",
    benchmarks: "RAG Benchmarks",
    docs: "Project Docs & Viva"
};

const pageSubtitles = {
    workspace:
        "Ask questions and retrieve verified knowledge from your documents.",

    graph:
        "Explore entities and relationships extracted from your knowledge base.",

    vectors:
        "Visualize document embeddings using dimensionality reduction.",

    compare:
        "Compare research papers across methodology, results and limitations.",

    ingestion:
        "Upload and process documents into the knowledge base.",

    benchmarks:
        "Evaluate retrieval and answer-generation performance.",

    docs:
        "Project architecture, methodology and viva preparation."
};


function showView(viewName) {

    views.forEach(view => {
        view.classList.remove("active");
    });

    navItems.forEach(item => {
        item.classList.remove("active");
    });

    const selectedView = document.getElementById(viewName);

    if (selectedView) {
        selectedView.classList.add("active");
    }

    const selectedNav = document.querySelector(
        `.nav-item[data-view="${viewName}"]`
    );

    if (selectedNav) {
        selectedNav.classList.add("active");
    }

    document.getElementById("page-title").textContent =
        pageTitles[viewName] || "Agentic RAG Platform";

    document.getElementById("page-subtitle").textContent =
        pageSubtitles[viewName] || "";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


navItems.forEach(item => {

    item.addEventListener("click", () => {

        const viewName = item.dataset.view;

        showView(viewName);

    });

});


document.querySelectorAll("[data-view-target]").forEach(button => {

    button.addEventListener("click", () => {

        showView(button.dataset.viewTarget);

    });

});


// ======================================================
// PROMPT CHIPS
// ======================================================

document.querySelectorAll(".prompt-chip").forEach(chip => {

    chip.addEventListener("click", () => {

        document.getElementById("queryInput").value =
            chip.textContent.trim();

        document.getElementById("queryInput").focus();

    });

});


// ======================================================
// ASK RAG
// ======================================================

const askButton = document.getElementById("askButton");

askButton.addEventListener("click", askQuestion);


async function askQuestion() {

    const queryInput = document.getElementById("queryInput");

    const question = queryInput.value.trim();

    if (!question) {

        alert("Please enter a question.");

        return;
    }

    setLoadingState(true);

    try {

        /*
         * This endpoint will be connected to the real
         * Agentic RAG orchestrator later.
         */

        const response = await fetch(
            `${API_BASE}/api/query`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    question: question
                })
            }
        );

        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }

        const data = await response.json();

        displayRAGResult(data);

    } catch (error) {

        console.error(error);

        /*
         * Backend endpoint does not exist yet.
         * Show a useful development message instead
         * of breaking the interface.
         */

        displayDevelopmentResult();

    } finally {

        setLoadingState(false);

    }
}


// ======================================================
// LOADING
// ======================================================

function setLoadingState(isLoading) {

    if (isLoading) {

        askButton.disabled = true;

        askButton.textContent =
            "Agents Processing...";

        document
            .querySelectorAll(".agent-step")
            .forEach(step => {
                step.classList.remove("active");
            });

    } else {

        askButton.disabled = false;

        askButton.textContent =
            "Ask Agentic RAG →";
    }

}


// ======================================================
// DISPLAY REAL RAG RESULT
// ======================================================

function displayRAGResult(data) {

    const answerContainer =
        document.getElementById("answerContainer");

    const verificationBadge =
        document.getElementById("verificationBadge");

    const sourcesContainer =
        document.getElementById("sourcesContainer");

    const sourceCount =
        document.getElementById("sourceCount");


    const answer =
        data.answer ||
        "No answer returned.";

    answerContainer.innerHTML = `
        <div class="answer-text">
            ${escapeHTML(answer)}
        </div>
    `;


    const status =
        data.verification_status ||
        "unverified";


    verificationBadge.textContent =
        status.toUpperCase();

    verificationBadge.className =
        "verification-badge";


    if (status === "verified") {

        verificationBadge.classList.add(
            "verified"
        );
    }


    const sources =
        data.sources || [];


    sourceCount.textContent =
        `${sources.length} source${sources.length === 1 ? "" : "s"}`;


    if (!sources.length) {

        sourcesContainer.innerHTML = `
            <div class="empty-state small">
                No sources returned.
            </div>
        `;

        return;
    }


    sourcesContainer.innerHTML =
        sources.map(source => {

            return `
                <div class="source-item">

                    <div class="source-top">

                        <span class="source-page">
                            Page ${source.page ?? "—"}
                        </span>

                        <span class="source-page">
                            Chunk ${source.chunk_index ?? "—"}
                        </span>

                    </div>

                    <div class="source-text">
                        ${escapeHTML(source.text || "Evidence retrieved.")}
                    </div>

                </div>
            `;

        }).join("");

}


// ======================================================
// DEVELOPMENT RESULT
// ======================================================

function displayDevelopmentResult() {

    const answerContainer =
        document.getElementById("answerContainer");

    const verificationBadge =
        document.getElementById("verificationBadge");

    answerContainer.innerHTML = `
        <div class="answer-text">

            <strong>Frontend connected successfully.</strong>

            <br><br>

            The FastAPI endpoint
            <code>/api/query</code>
            is not implemented yet.

            <br><br>

            Your current backend already contains the
            Planner, Retriever, Synthesizer and Fact-Checker
            agents. We will connect this interface to that
            pipeline next.

        </div>
    `;

    verificationBadge.textContent =
        "BACKEND PENDING";

    verificationBadge.className =
        "verification-badge";

}


// ======================================================
// DOCUMENT UPLOAD
// ======================================================

const fileInput =
    document.getElementById("fileInput");

const selectFileButton =
    document.getElementById("selectFileButton");

const uploadArea =
    document.getElementById("uploadArea");


selectFileButton.addEventListener(
    "click",
    () => fileInput.click()
);


fileInput.addEventListener(
    "change",
    () => {

        if (fileInput.files.length > 0) {

            uploadDocument(
                fileInput.files[0]
            );

        }

    }
);


// Drag & Drop

uploadArea.addEventListener(
    "dragover",
    event => {

        event.preventDefault();

        uploadArea.classList.add("dragover");

    }
);


uploadArea.addEventListener(
    "dragleave",
    () => {

        uploadArea.classList.remove(
            "dragover"
        );

    }
);


uploadArea.addEventListener(
    "drop",
    event => {

        event.preventDefault();

        uploadArea.classList.remove(
            "dragover"
        );

        const file =
            event.dataTransfer.files[0];

        if (file) {

            uploadDocument(file);

        }

    }
);


async function uploadDocument(file) {

    const resultContainer =
        document.getElementById("uploadResult");

    resultContainer.innerHTML = `
        <div class="source-item">
            Uploading <strong>${escapeHTML(file.name)}</strong>...
        </div>
    `;


    const formData =
        new FormData();

    formData.append(
        "file",
        file
    );


    try {

        const response = await fetch(
            `${API_BASE}/api/upload`,
            {
                method: "POST",
                body: formData
            }
        );


        if (!response.ok) {

            throw new Error(
                `Upload failed: ${response.status}`
            );

        }


        const data =
            await response.json();


        resultContainer.innerHTML = `
            <div class="source-item">

                <div class="source-page">
                    Upload Successful
                </div>

                <div class="source-text">

                    File:
                    ${escapeHTML(data.filename)}

                    <br>

                    Pages:
                    ${data.total_pages}

                    <br><br>

                    ${escapeHTML(data.message)}

                </div>

            </div>
        `;


        updateKnowledgeBase(
            data
        );


    } catch (error) {

        console.error(error);


        resultContainer.innerHTML = `
            <div class="source-item">

                <div class="source-page">
                    Upload failed
                </div>

                <div class="source-text">
                    ${escapeHTML(error.message)}
                </div>

            </div>
        `;

    }

}


// ======================================================
// KNOWLEDGE BASE
// ======================================================

function updateKnowledgeBase(data) {

    const documentCount =
        document.getElementById("documentCount");

    const current =
        Number(documentCount.textContent) || 0;

    documentCount.textContent =
        current + 1;

}


// ======================================================
// THEME BUTTON
// ======================================================

document
    .getElementById("themeButton")
    .addEventListener("click", () => {

        document.body.classList.toggle(
            "light-mode"
        );

    });


// ======================================================
// DOCUMENTATION LINKS
// ======================================================

document.querySelectorAll(".doc-link").forEach(link => {

    link.addEventListener("click", () => {

        document.querySelectorAll(".doc-link")
            .forEach(item => {
                item.classList.remove("active");
            });

        link.classList.add("active");

    });

});


// ======================================================
// UTILITY
// ======================================================

function escapeHTML(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


// ======================================================
// INITIALIZATION
// ======================================================

showView("workspace");

console.log(
    "Agentic RAG frontend initialized."
);