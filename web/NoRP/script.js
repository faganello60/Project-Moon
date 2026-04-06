const apiBaseUrlInput = document.getElementById("api-base-url");
const fileInput = document.getElementById("norp-file");
const modeAutomaticButton = document.getElementById("mode-automatic-button");
const modeManualButton = document.getElementById("mode-manual-button");
const manualRangePanel = document.getElementById("manual-range-panel");
const preFlareStartInput = document.getElementById("pre-flare-start");
const preFlareEndInput = document.getElementById("pre-flare-end");
const peakStartInput = document.getElementById("peak-start");
const peakEndInput = document.getElementById("peak-end");
const manualFinalButton = document.getElementById("manual-final-button");
const statusCard = document.getElementById("status-card");
const loader = document.getElementById("loader");
const loaderText = document.getElementById("loader-text");
const obsDay = document.getElementById("obs-day");
const pointCount = document.getElementById("point-count");
const resultsPanel = document.getElementById("resultsPanel");
const windowsList = document.getElementById("windows-list");
const spectrumTableBody = document.getElementById("spectrum-table-body");
const lightcurveImage = document.getElementById("lightcurve-image");
const spectrumImage = document.getElementById("spectrum-image");
const lightcurvePlaceholder = document.getElementById("lightcurve-placeholder");
const spectrumPlaceholder = document.getElementById("spectrum-placeholder");

let manualPreviewReady = false;

function setStatus(type, message) {
    statusCard.className = `status-card ${type}`;
    statusCard.textContent = message;
}

function setLoading(isLoading, message = "Calculating Trajectory...") {
    loaderText.textContent = message;
    loader.classList.toggle("hidden", !isLoading);
    modeAutomaticButton.disabled = isLoading;
    modeManualButton.disabled = isLoading;
    manualFinalButton.disabled = isLoading;
}

function clearResults() {
    renderWindows({});
    renderSpectrumTable([], []);
    renderImage(lightcurveImage, lightcurvePlaceholder, null);
    renderImage(spectrumImage, spectrumPlaceholder, null);
    obsDay.textContent = "-";
    pointCount.textContent = "-";
    resultsPanel.classList.add("hidden");
}

function updateManualState() {
    manualRangePanel.classList.toggle("hidden", !manualPreviewReady);
    manualFinalButton.classList.toggle("hidden", !manualPreviewReady);
}

function renderWindows(windows) {
    windowsList.innerHTML = "";
    const names = Object.keys(windows || {});

    if (names.length === 0) {
        windowsList.innerHTML = '<p class="placeholder">No windows returned.</p>';
        return;
    }

    names.forEach((name) => {
        const item = document.createElement("div");
        item.className = "window-entry";
        item.innerHTML = `
            <strong>${name}</strong>
            <span>Start: ${windows[name].start_time}</span>
            <span>End: ${windows[name].end_time}</span>
        `;
        windowsList.appendChild(item);
    });
}

function renderSpectrumTable(frequencies, fluxes) {
    spectrumTableBody.innerHTML = "";

    if (!frequencies?.length) {
        spectrumTableBody.innerHTML = '<tr><td colspan="2" class="placeholder-cell">No data returned.</td></tr>';
        return;
    }

    frequencies.forEach((frequency, index) => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${Number(frequency).toExponential(5)}</td>
            <td>${Number(fluxes[index]).toFixed(5)}</td>
        `;
        spectrumTableBody.appendChild(row);
    });
}

function renderImage(imgElement, placeholderElement, base64Value) {
    if (!base64Value) {
        imgElement.style.display = "none";
        placeholderElement.style.display = "block";
        return;
    }

    imgElement.src = `data:image/png;base64,${base64Value}`;
    imgElement.style.display = "block";
    placeholderElement.style.display = "none";
}

function populateManualInputs(windows) {
    preFlareStartInput.value = windows?.pre_flare?.start_time || "";
    preFlareEndInput.value = windows?.pre_flare?.end_time || "";
    peakStartInput.value = windows?.peak?.start_time || "";
    peakEndInput.value = windows?.peak?.end_time || "";
}

function renderAutomaticPayload(payload) {
    obsDay.textContent = payload.obs_day || "-";
    pointCount.textContent = String(payload.frequencies_hz?.length || 0);
    renderWindows(payload.windows || {});
    renderSpectrumTable(payload.frequencies_hz || [], payload.flux_sfu || []);
    renderImage(lightcurveImage, lightcurvePlaceholder, payload.plots_base64?.lightcurves_png_base64);
    renderImage(spectrumImage, spectrumPlaceholder, payload.plots_base64?.spectrum_png_base64);
    resultsPanel.classList.remove("hidden");
}

function renderManualPreviewPayload(payload) {
    obsDay.textContent = payload.obs_day || "-";
    pointCount.textContent = "-";
    renderWindows(payload.suggested_windows || {});
    renderSpectrumTable([], []);
    renderImage(lightcurveImage, lightcurvePlaceholder, payload.background_removed_lightcurve_png_base64);
    renderImage(spectrumImage, spectrumPlaceholder, null);
    populateManualInputs(payload.suggested_windows || {});
    resultsPanel.classList.remove("hidden");
}

function renderManualFinalPayload(payload) {
    obsDay.textContent = payload.obs_day || "-";
    pointCount.textContent = String(payload.frequencies_hz?.length || 0);
    renderWindows({
        pre_flare: payload.pre_flare_window,
        peak: payload.peak_window,
    });
    renderSpectrumTable(payload.frequencies_hz || [], payload.flux_sfu || []);
    renderImage(lightcurveImage, lightcurvePlaceholder, null);
    renderImage(spectrumImage, spectrumPlaceholder, payload.spectrum_png_base64);
    resultsPanel.classList.remove("hidden");
}

async function parseResponse(response) {
    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.detail || "The backend returned an unexpected error.");
    }
    return payload;
}

function getSelectedFile() {
    const selectedFile = fileInput.files[0];
    if (!selectedFile) {
        throw new Error("Select a .fit, .fits, or .fits.gz file before submitting.");
    }
    return selectedFile;
}

function createFileFormData(file) {
    const formData = new FormData();
    formData.append("file", file);
    return formData;
}

async function runAutomaticAnalysis() {
    const selectedFile = getSelectedFile();
    const apiBaseUrl = apiBaseUrlInput.value.trim().replace(/\/$/, "");
    manualPreviewReady = false;
    updateManualState();
    clearResults();
    setLoading(true, "Running automatic NoRP analysis...");
    setStatus("loading", "Uploading file and waiting for backend analysis...");

    try {
        const response = await fetch(`${apiBaseUrl}/norp/analyze`, {
            method: "POST",
            body: createFileFormData(selectedFile),
        });
        const payload = await parseResponse(response);
        renderAutomaticPayload(payload);
        setStatus("success", "Automatic analysis completed successfully.");
    } finally {
        setLoading(false);
    }
}

async function runManualPreview() {
    const selectedFile = getSelectedFile();
    const apiBaseUrl = apiBaseUrlInput.value.trim().replace(/\/$/, "");
    manualPreviewReady = false;
    updateManualState();
    clearResults();
    setLoading(true, "Loading manual preview...");
    setStatus("loading", "Previewing the event so you can choose the time ranges.");

    try {
        const response = await fetch(`${apiBaseUrl}/norp/manual/preview`, {
            method: "POST",
            body: createFileFormData(selectedFile),
        });
        const payload = await parseResponse(response);
        renderManualPreviewPayload(payload);
        manualPreviewReady = true;
        updateManualState();
        setStatus("success", "Preview loaded. Review the suggested windows and choose the ranges you want.");
    } finally {
        setLoading(false);
    }
}

async function runManualFinalAnalysis() {
    const selectedFile = getSelectedFile();
    if (!preFlareStartInput.value || !preFlareEndInput.value || !peakStartInput.value || !peakEndInput.value) {
        throw new Error("Fill in the pre-flare and peak ranges before running the final manual analysis.");
    }

    const apiBaseUrl = apiBaseUrlInput.value.trim().replace(/\/$/, "");
    setLoading(true, "Running final manual analysis...");
    setStatus("loading", "Sending your selected ranges to the backend.");

    try {
        const formData = createFileFormData(selectedFile);
        formData.append("pre_flare_start", preFlareStartInput.value);
        formData.append("pre_flare_end", preFlareEndInput.value);
        formData.append("peak_start", peakStartInput.value);
        formData.append("peak_end", peakEndInput.value);

        const response = await fetch(`${apiBaseUrl}/norp/manual/final`, {
            method: "POST",
            body: formData,
        });
        const payload = await parseResponse(response);
        renderManualFinalPayload(payload);
        setStatus("success", "Manual analysis completed successfully.");
    } finally {
        setLoading(false);
    }
}

modeAutomaticButton.addEventListener("click", async () => {
    try {
        await runAutomaticAnalysis();
    } catch (error) {
        clearResults();
        setStatus("error", error.message || "Failed to execute the analysis.");
    }
});

modeManualButton.addEventListener("click", async () => {
    try {
        await runManualPreview();
    } catch (error) {
        clearResults();
        setStatus("error", error.message || "Failed to execute the analysis.");
    }
});

manualFinalButton.addEventListener("click", async () => {
    try {
        await runManualFinalAnalysis();
    } catch (error) {
        setStatus("error", error.message || "Failed to execute the manual analysis.");
    }
});

updateManualState();
