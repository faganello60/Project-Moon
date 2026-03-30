const form = document.getElementById("norp-form");
const apiBaseUrlInput = document.getElementById("api-base-url");
const fileInput = document.getElementById("norp-file");
const submitButton = document.getElementById("submit-button");
const statusCard = document.getElementById("status-card");
const obsDay = document.getElementById("obs-day");
const pointCount = document.getElementById("point-count");
const resultsPanel = document.getElementById("resultsPanel");
const windowsList = document.getElementById("windows-list");
const spectrumTableBody = document.getElementById("spectrum-table-body");
const lightcurveImage = document.getElementById("lightcurve-image");
const spectrumImage = document.getElementById("spectrum-image");
const lightcurvePlaceholder = document.getElementById("lightcurve-placeholder");
const spectrumPlaceholder = document.getElementById("spectrum-placeholder");

function setStatus(type, message) {
    statusCard.className = `status-card ${type}`;
    statusCard.textContent = message;
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

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const selectedFile = fileInput.files[0];
    if (!selectedFile) {
        setStatus("error", "Select a .fit, .fits, or .fits.gz file before submitting.");
        return;
    }

    submitButton.disabled = true;
    setStatus("loading", "Uploading file and waiting for backend analysis...");

    try {
        const apiBaseUrl = apiBaseUrlInput.value.trim().replace(/\/$/, "");
        const formData = new FormData();
        formData.append("file", selectedFile);

        const response = await fetch(`${apiBaseUrl}/norp/analyze`, {
            method: "POST",
            body: formData,
        });

        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.detail || "The backend returned an unexpected error.");
        }

        obsDay.textContent = payload.obs_day || "-";
        pointCount.textContent = String(payload.frequencies_hz?.length || 0);
        renderWindows(payload.windows || {});
        renderSpectrumTable(payload.frequencies_hz || [], payload.flux_sfu || []);
        renderImage(lightcurveImage, lightcurvePlaceholder, payload.plots_base64?.lightcurves_png_base64);
        renderImage(spectrumImage, spectrumPlaceholder, payload.plots_base64?.spectrum_png_base64);
        resultsPanel.classList.remove("hidden");

        setStatus("success", "Analysis completed successfully.");
    } catch (error) {
        renderWindows({});
        renderSpectrumTable([], []);
        renderImage(lightcurveImage, lightcurvePlaceholder, null);
        renderImage(spectrumImage, spectrumPlaceholder, null);
        obsDay.textContent = "-";
        pointCount.textContent = "-";
        resultsPanel.classList.add("hidden");
        setStatus("error", error.message || "Failed to execute the analysis.");
    } finally {
        submitButton.disabled = false;
    }
});
