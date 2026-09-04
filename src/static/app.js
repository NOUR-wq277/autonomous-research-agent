// ============================================================
// Autonomous Research Agent - Client Application Logic
// ============================================================

document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const questionInput = document.getElementById("research-question");
    const startBtn = document.getElementById("start-btn");
    const emptyState = document.getElementById("empty-state");
    const metricsGrid = document.getElementById("metrics-grid");
    const activitySection = document.getElementById("activity-section");
    const activityConsole = document.getElementById("activity-console");
    const resultsSection = document.getElementById("results-section");
    const reportRendered = document.getElementById("report-rendered");
    const sourcesContainer = document.getElementById("sources-container");
    const sourcesCountLabel = document.getElementById("tab-sources-count");
    const activeModelBadge = document.getElementById("active-model-badge");
    const copyReportBtn = document.getElementById("copy-report-btn");
    const downloadReportBtn = document.getElementById("download-report-btn");
    const toggleLogsBtn = document.getElementById("toggle-logs-btn");

    // Metric elements
    const metricSources = document.getElementById("metric-sources");
    const metricEvidence = document.getElementById("metric-evidence");
    const metricIterations = document.getElementById("metric-iterations");
    const metricConfidence = document.getElementById("metric-confidence");
    const metricDuration = document.getElementById("metric-duration");
    const iterationCounter = document.getElementById("iteration-counter");

    // Inspector elements
    const inspectPlanner = document.getElementById("inspect-planner-content");
    const inspectResearcher = document.getElementById("inspect-researcher-content");
    const inspectAnalyst = document.getElementById("inspect-analyst-content");
    const inspectVerifier = document.getElementById("inspect-verifier-content");

    // Nodes
    const nodes = {
        planner: document.getElementById("node-planner"),
        researcher: document.getElementById("node-researcher"),
        analyst: document.getElementById("node-analyst"),
        verifier: document.getElementById("node-verifier"),
        writer: document.getElementById("node-writer"),
    };

    let currentEventSource = null;
    let rawReportMarkdown = "";
    let startTime = 0;
    let timerInterval = null;

    // Check backend health on load
    fetch("/health")
        .then(res => res.json())
        .then(data => {
            if (data.primary_model && activeModelBadge) {
                activeModelBadge.textContent = data.primary_model;
            }
        })
        .catch(err => console.error("Health check error:", err));

    // Quick Prompt Chips
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const prompt = chip.getAttribute("data-prompt");
            if (prompt && questionInput) {
                questionInput.value = prompt;
                questionInput.focus();
            }
        });
    });

    // Tab Switching
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const tabId = btn.getAttribute("data-tab");
            const content = document.getElementById(tabId);
            if (content) content.classList.add("active");
        });
    });

    // Toggle logs visibility
    if (toggleLogsBtn && activityConsole) {
        toggleLogsBtn.addEventListener("click", () => {
            if (activityConsole.style.display === "none") {
                activityConsole.style.display = "flex";
                toggleLogsBtn.textContent = "Collapse Logs";
            } else {
                activityConsole.style.display = "none";
                toggleLogsBtn.textContent = "Expand Logs";
            }
        });
    }

    // Helper: Reset Pipeline Node UI
    function resetPipelineUI() {
        Object.values(nodes).forEach(node => {
            node.className = "pipeline-node waiting";
            const icon = node.querySelector(".node-status-icon");
            if (icon) icon.textContent = "○";
        });
        if (iterationCounter) iterationCounter.textContent = "Iteration 1/3";
        if (activityConsole) activityConsole.innerHTML = "";
    }

    // Helper: Set Node Status
    function setNodeStatus(agentName, status) {
        const node = nodes[agentName];
        if (!node) return;

        node.className = `pipeline-node ${status}`;
        const icon = node.querySelector(".node-status-icon");
        if (!icon) return;

        if (status === "running") icon.textContent = "◉";
        else if (status === "completed") icon.textContent = "✓";
        else if (status === "review") icon.textContent = "⚠";
        else if (status === "failed") icon.textContent = "✕";
        else icon.textContent = "○";
    }

    // Helper: Append log message
    function appendLog(message, type = "info") {
        if (!activityConsole) return;
        const entry = document.createElement("div");
        entry.className = `log-entry log-${type}`;
        const time = new Date().toLocaleTimeString();
        entry.textContent = `[${time}] ${message}`;
        activityConsole.appendChild(entry);
        activityConsole.scrollTop = activityConsole.scrollHeight;
    }

    // Start Research Action
    startBtn.addEventListener("click", () => {
        const question = questionInput.value.trim();
        if (!question) {
            alert("Please enter a research objective or question.");
            questionInput.focus();
            return;
        }

        // Lock UI & Show Running State
        startBtn.disabled = true;
        startBtn.querySelector(".btn-text").textContent = "Researching...";
        if (emptyState) emptyState.style.display = "none";
        if (metricsGrid) metricsGrid.style.display = "grid";
        if (activitySection) activitySection.style.display = "block";
        if (resultsSection) resultsSection.style.display = "none";

        resetPipelineUI();
        startTime = Date.now();
        if (timerInterval) clearInterval(timerInterval);
        timerInterval = setInterval(() => {
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            if (metricDuration) metricDuration.textContent = `${elapsed}s`;
        }, 100);

        appendLog(`Initiating autonomous research for: "${question}"`, "info");

        // Connect to SSE Stream
        const streamUrl = `/research/stream?question=${encodeURIComponent(question)}`;
        if (currentEventSource) {
            currentEventSource.close();
        }

        currentEventSource = new EventSource(streamUrl);

        currentEventSource.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                handleStreamEvent(msg);
            } catch (err) {
                console.warn("Non-JSON SSE data:", event.data);
            }
        };

        currentEventSource.onerror = (err) => {
            console.error("SSE stream error, falling back to POST /research:", err);
            currentEventSource.close();
            // Fallback to standard POST
            fallbackPostResearch(question);
        };
    });

    // Handle SSE events
    function handleStreamEvent(msg) {
        const { event, data } = msg;

        switch (event) {
            case "planner_started":
                setNodeStatus("planner", "running");
                appendLog("[Planner] Deconstructing research objective into subquestions...", "info");
                break;

            case "planner_completed":
                setNodeStatus("planner", "completed");
                appendLog(`[Planner] Created plan with ${data.subquestions ? data.subquestions.length : 0} subquestions and ${data.search_queries ? data.search_queries.length : 0} search queries.`, "success");
                if (inspectPlanner) {
                    inspectPlanner.textContent = JSON.stringify(data, null, 2);
                }
                break;

            case "researcher_started":
                setNodeStatus("researcher", "running");
                if (iterationCounter && data.iteration) {
                    iterationCounter.textContent = `Iteration ${data.iteration}/3`;
                    if (metricIterations) metricIterations.textContent = data.iteration;
                }
                appendLog(`[Researcher] Executing grounded web searches across ${data.queries_count || 0} queries...`, "info");
                if (data.queries) {
                    data.queries.forEach(q => appendLog(`  🔎 Search query: "${q}"`, "info"));
                }
                break;

            case "researcher_completed":
                setNodeStatus("researcher", "completed");
                appendLog(`[Researcher] Accumulated ${data.total_sources} authoritative sources, ${data.total_evidence} verified evidence points.`, "success");
                if (metricSources) metricSources.textContent = data.total_sources;
                if (metricEvidence) metricEvidence.textContent = data.total_evidence;
                if (inspectResearcher) {
                    inspectResearcher.textContent = JSON.stringify(data, null, 2);
                }
                break;

            case "analyst_started":
                setNodeStatus("analyst", "running");
                appendLog("[Analyst] Synthesizing evidence, mapping entities, and identifying market dynamics...", "info");
                break;

            case "analyst_completed":
                setNodeStatus("analyst", "completed");
                appendLog(`[Analyst] Synthesized findings: ${(data.entities || []).length} entities, ${(data.opportunities || []).length} strategic opportunities identified.`, "success");
                if (inspectAnalyst) {
                    inspectAnalyst.textContent = JSON.stringify(data, null, 2);
                }
                break;

            case "verifier_started":
                setNodeStatus("verifier", "running");
                appendLog("[Verifier] Auditing evidence coverage, source authority, and claim grounding...", "info");
                break;

            case "verifier_completed":
                if (data.is_sufficient) {
                    setNodeStatus("verifier", "completed");
                    appendLog(`[Verifier] Evidence sufficiency APPROVED (Confidence: ${(data.confidence * 100).toFixed(0)}%). Reason: ${data.reason}`, "success");
                } else {
                    setNodeStatus("verifier", "review");
                    appendLog(`[Verifier] Gaps identified: ${data.missing_topics ? data.missing_topics.join(', ') : 'More data needed'}. Preparing loopback...`, "warning");
                }
                if (metricConfidence) {
                    metricConfidence.textContent = `${(data.confidence * 100).toFixed(0)}%`;
                }
                if (inspectVerifier) {
                    inspectVerifier.textContent = JSON.stringify(data, null, 2);
                }
                break;

            case "loopback_triggered":
                appendLog(`[Router] Triggering research loop ${data.next_iteration}/${data.max_iterations} for missing topics...`, "warning");
                setNodeStatus("researcher", "running");
                break;

            case "writer_started":
                setNodeStatus("writer", "running");
                appendLog("[Writer] Drafting final structured intelligence report with citations...", "info");
                break;

            case "writer_completed":
                setNodeStatus("writer", "completed");
                appendLog(`[Writer] Report published: "${data.title}" (${data.sections_count} sections).`, "success");
                break;

            case "complete":
                if (currentEventSource) currentEventSource.close();
                clearInterval(timerInterval);
                finishResearchSuccess(data);
                break;

            case "error":
                if (currentEventSource) currentEventSource.close();
                clearInterval(timerInterval);
                finishResearchError(data.message || "An unknown error occurred.");
                break;
        }
    }

    // Fallback POST /research
    async function fallbackPostResearch(question) {
        try {
            setNodeStatus("planner", "running");
            appendLog("[Fallback] Executing research via synchronous API...", "info");
            const resp = await fetch("/research", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question }),
            });

            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                throw new Error(errData.detail || `HTTP error ${resp.status}`);
            }

            const data = await resp.json();
            clearInterval(timerInterval);
            Object.keys(nodes).forEach(k => setNodeStatus(k, "completed"));
            finishResearchSuccess(data);
        } catch (e) {
            clearInterval(timerInterval);
            finishResearchError(e.message);
        }
    }

    // Finalize Success
    function finishResearchSuccess(response) {
        startBtn.disabled = false;
        startBtn.querySelector(".btn-text").textContent = "Start Research";
        appendLog("========== Research Pipeline Complete ==========", "success");

        if (resultsSection) resultsSection.style.display = "block";

        const report = response.report || {};
        rawReportMarkdown = report.full_markdown || "";

        // Render Markdown
        if (reportRendered && typeof marked !== "undefined") {
            reportRendered.innerHTML = marked.parse(rawReportMarkdown);
        }

        // Render Sources
        const sources = report.sources || [];
        if (sourcesCountLabel) sourcesCountLabel.textContent = sources.length;
        if (sourcesContainer) {
            sourcesContainer.innerHTML = "";
            if (sources.length === 0) {
                sourcesContainer.innerHTML = "<p class='text-muted'>No external sources were cited.</p>";
            } else {
                sources.forEach((src, idx) => {
                    const card = document.createElement("div");
                    card.className = "source-card";
                    card.innerHTML = `
                        <div class="source-meta">
                            <span class="source-domain">${src.domain || 'web'}</span>
                            <span class="source-rel">Rel: ${(src.reliability_score * 100).toFixed(0)}%</span>
                        </div>
                        <div class="source-title">[${idx + 1}] ${src.title}</div>
                        ${src.url ? `<a href="${src.url}" target="_blank" rel="noopener noreferrer" class="source-url">${src.url}</a>` : '<span class="source-url text-muted">Grounded Web Discovery</span>'}
                    `;
                    sourcesContainer.appendChild(card);
                });
            }
        }

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: "smooth" });
    }

    // Finalize Error
    function finishResearchError(errorMessage) {
        startBtn.disabled = false;
        startBtn.querySelector(".btn-text").textContent = "Start Research";
        appendLog(`[ERROR] ${errorMessage}`, "error");
        alert(`Research Pipeline Failed: ${errorMessage}`);
    }

    // Copy Report Button
    if (copyReportBtn) {
        copyReportBtn.addEventListener("click", () => {
            if (!rawReportMarkdown) return;
            navigator.clipboard.writeText(rawReportMarkdown)
                .then(() => {
                    const originalText = copyReportBtn.textContent;
                    copyReportBtn.textContent = "✓ Copied!";
                    setTimeout(() => { copyReportBtn.textContent = originalText; }, 2000);
                })
                .catch(err => alert("Failed to copy report: " + err));
        });
    }

    // Download Markdown Button
    if (downloadReportBtn) {
        downloadReportBtn.addEventListener("click", () => {
            if (!rawReportMarkdown) return;
            const blob = new Blob([rawReportMarkdown], { type: "text/markdown;charset=utf-8;" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "autonomous_research_report.md";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }
});
