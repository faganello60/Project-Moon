document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = window.APP_CONFIG?.API_BASE_URL || 'http://localhost:8000';
    const ACCEPTED_EXTENSIONS = ['.fits', '.fit', '.gz', '.fits.gz'];
    const COLORS = ['#00d2ff', '#ff8a5b', '#73f5b1', '#ffcf5c', '#f777ff', '#9ec5ff', '#ff6b90'];

    const fitsFileInput = document.getElementById('fitsFile');
    const selectFileBtn = document.getElementById('selectFileBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const dropZone = document.getElementById('dropZone');
    const selectedFileName = document.getElementById('selectedFileName');
    const errorMessage = document.getElementById('errorMessage');
    const loader = document.getElementById('loader');
    const resultsPanel = document.getElementById('resultsPanel');
    const obsDayValue = document.getElementById('obsDayValue');
    const startTimeValue = document.getElementById('startTimeValue');
    const endTimeValue = document.getElementById('endTimeValue');
    const frequenciesValue = document.getElementById('frequenciesValue');

    const fullChartCard = document.getElementById('fullChartCard');
    const rangeChartCard = document.getElementById('rangeChartCard');
    const fullChartHint = document.getElementById('fullChartHint');
    const rangeChartHint = document.getElementById('rangeChartHint');
    const selectionHint = document.getElementById('selectionHint');
    const backgroundPanel = document.getElementById('backgroundPanel');
    const backgroundSubtractedPanel = document.getElementById('backgroundSubtractedPanel');
    const backgroundSubtractedHint = document.getElementById('backgroundSubtractedHint');
    const backgroundAveragesSummary = document.getElementById('backgroundAveragesSummary');

    const preFlareStartInput = document.getElementById('preFlareStartInput');
    const preFlareEndInput = document.getElementById('preFlareEndInput');
    const startFlareInput = document.getElementById('startFlareInput');
    const endFlareInput = document.getElementById('endFlareInput');
    const timeStepButtons = Array.from(document.querySelectorAll('.time-step-btn'));
    const removeBackgroundBtn = document.getElementById('removeBackgroundBtn');
    const cutRangeBar = document.getElementById('cutRangeBar');
    const cutRangeBtn = document.getElementById('cutRangeBtn');
    const fullResetZoomBtn = document.getElementById('fullResetZoomBtn');

    const fullChartEl = document.getElementById('fullNorpChart');
    const rangeChartStage = document.getElementById('rangeChartStage');
    const rangeChartEl = document.getElementById('rangeNorpChart');
    const backgroundSubtractedChartStage = document.getElementById('backgroundSubtractedChartStage');
    const backgroundSubtractedChartEl = document.getElementById('backgroundSubtractedChart');
    const startPreFlareHandle = document.getElementById('startPreFlareHandle');
    const endPreFlareHandle = document.getElementById('endPreFlareHandle');
    const startFlareHandle = document.getElementById('startFlareHandle');
    const endFlareHandle = document.getElementById('endFlareHandle');

    let selectedFile = null;
    let fullChart = null;
    let rangeChart = null;
    let backgroundSubtractedChart = null;
    let lastFullLightCurves = null;
    let lastRangeLightCurves = null;
    let lastBackgroundSubtractedLightCurves = null;
    let currentVisibleRange = null;
    let selectedBackgroundRange = null;
    let selectedFlareRange = null;
    let draggingBoundary = null;
    let draggingFlareBoundary = null;
    let timeStepHoldTimeout = null;
    let timeStepHoldInterval = null;

    function setFullChartVisibility(isVisible) {
        fullChartCard.classList.toggle('hidden', !isVisible);
    }

    function setRangeChartVisibility(isVisible) {
        rangeChartCard.classList.toggle('hidden', !isVisible);
    }

    function setCutRangeVisibility(isVisible) {
        cutRangeBar.classList.toggle('hidden', !isVisible);
    }

    function setBackgroundPanelVisibility(isVisible) {
        backgroundPanel.classList.toggle('hidden', !isVisible);
    }

    function setBackgroundSubtractedVisibility(isVisible) {
        backgroundSubtractedPanel.classList.toggle('hidden', !isVisible);
    }

    function setLoading(isLoading) {
        loader.classList.toggle('hidden', !isLoading);
        analyzeBtn.disabled = isLoading || !selectedFile;
        selectFileBtn.disabled = isLoading;
        cutRangeBtn.disabled = isLoading || !selectedFile || !lastFullLightCurves;
        removeBackgroundBtn.disabled = isLoading || !selectedFile || !selectedBackgroundRange || !Number.isFinite(selectedBackgroundRange.end);
        fullResetZoomBtn.disabled = isLoading || !selectedFile || !lastFullLightCurves;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function clearError() {
        errorMessage.textContent = '';
        errorMessage.classList.add('hidden');
    }

    function isAcceptedFile(file) {
        const lowerName = file.name.toLowerCase();
        return ACCEPTED_EXTENSIONS.some(extension => lowerName.endsWith(extension));
    }

    function destroyFullChart() {
        if (fullChart) {
            fullChart.dispose();
            fullChart = null;
        }
    }

    function destroyRangeChart() {
        if (rangeChart) {
            rangeChart.dispose();
            rangeChart = null;
        }
    }

    function destroyBackgroundSubtractedChart() {
        if (backgroundSubtractedChart) {
            backgroundSubtractedChart.dispose();
            backgroundSubtractedChart = null;
        }
    }

    function resetUiState() {
        lastFullLightCurves = null;
        lastRangeLightCurves = null;
        lastBackgroundSubtractedLightCurves = null;
        currentVisibleRange = null;
        selectedBackgroundRange = null;
        selectedFlareRange = null;
        destroyFullChart();
        destroyRangeChart();
        destroyBackgroundSubtractedChart();
        setFullChartVisibility(false);
        setRangeChartVisibility(false);
        setCutRangeVisibility(false);
        setBackgroundPanelVisibility(false);
        setBackgroundSubtractedVisibility(false);
        preFlareStartInput.value = '';
        preFlareEndInput.value = '';
        startFlareInput.value = '';
        endFlareInput.value = '';
        selectionHint.textContent = 'Enter the pre-flare interval shown on the chart.';
        backgroundAveragesSummary.innerHTML = '';
        removeBackgroundBtn.disabled = true;
        cutRangeBtn.disabled = true;
        syncFlareSelectionHandles();
    }

    function setSelectedFile(file) {
        if (!file) {
            selectedFile = null;
            selectedFileName.textContent = 'No file selected';
            analyzeBtn.disabled = true;
            resetUiState();
            return;
        }

        if (!isAcceptedFile(file)) {
            setSelectedFile(null);
            showError('Unsupported file type. Please upload a .fits, .fit, .gz, or .fits.gz file.');
            return;
        }

        clearError();
        selectedFile = file;
        selectedFileName.textContent = `${file.name} • ${(file.size / 1024 / 1024).toFixed(2)} MB`;
        analyzeBtn.disabled = false;
        resetUiState();
        resultsPanel.classList.add('hidden');
    }

    function formatUtcTimestamp(timestamp) {
        return new Intl.DateTimeFormat('en-GB', {
            dateStyle: 'medium',
            timeStyle: 'medium',
            timeZone: 'UTC'
        }).format(new Date(timestamp));
    }

    function formatUtcTick(timestamp) {
        return new Intl.DateTimeFormat('en-GB', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            timeZone: 'UTC'
        }).format(new Date(timestamp));
    }

    function normalizeRange(start, end) {
        if (!Number.isFinite(start) || !Number.isFinite(end)) {
            return null;
        }

        return start <= end
            ? { start, end }
            : { start: end, end: start };
    }

    function getFullTimeRange(lightCurves) {
        const time = lightCurves?.time || [];
        if (!time.length) {
            return null;
        }

        return normalizeRange(time[0], time[time.length - 1]);
    }

    function buildPoints(time, sfu) {
        if (!Array.isArray(time) || !Array.isArray(sfu) || time.length !== sfu.length) {
            return [];
        }

        return time.map((value, index) => [value, sfu[index]]);
    }

    function buildScatterDatasets(lightCurves) {
        const time = lightCurves.time || [];

        return (lightCurves.frequencies || []).map((frequency, index) => ({
            name: frequency.name,
            data: buildPoints(time, frequency.sfu || []),
            type: 'scatter',
            symbol: 'circle',
            symbolSize: 2,
            itemStyle: {
                color: COLORS[index % COLORS.length],
            },
            large: true,
            largeThreshold: 5000,
            progressive: 20000,
            progressiveThreshold: 10000,
            progressiveChunkMode: 'mod',
        }));
    }

    function buildLineDatasets(lightCurves) {
        const time = lightCurves.time || [];

        return (lightCurves.frequencies || []).map((frequency, index) => ({
            name: frequency.name,
            data: buildPoints(time, frequency.sfu || []),
            type: 'line',
            showSymbol: false,
            symbol: 'none',
            sampling: 'lttb',
            lineStyle: {
                width: 1,
                type: 'solid',
                color: COLORS[index % COLORS.length],
            },
            itemStyle: {
                color: COLORS[index % COLORS.length],
            },
        }));
    }

    function buildChartOption(lightCurves, datasets, hintEl, enableZoom) {
        const time = lightCurves.time || [];
        const minTime = time.length ? time[0] : null;
        const maxTime = time.length ? time[time.length - 1] : null;
        const edgePadding = time.length > 1
            ? Math.max(1000, Math.round((time[time.length - 1] - time[0]) / Math.max(time.length - 1, 1)))
            : 1000;
        const paddedMinTime = Number.isFinite(minTime) ? minTime - edgePadding : null;
        const paddedMaxTime = Number.isFinite(maxTime) ? maxTime + edgePadding : null;

        hintEl.textContent = enableZoom
            ? 'Use mouse wheel or pinch to zoom, drag to pan.'
            : 'Adjust the pre-flare interval below.';

        return {
            animation: false,
            backgroundColor: 'transparent',
            color: COLORS,
            grid: {
                left: 72,
                right: 28,
                top: 44,
                bottom: enableZoom ? 70 : 52,
            },
            legend: {
                top: 0,
                textStyle: {
                    color: '#f4f8ff',
                },
            },
            tooltip: {
                trigger: datasets[0]?.type === 'line' ? 'axis' : 'item',
                confine: true,
                backgroundColor: 'rgba(3, 8, 18, 0.94)',
                borderColor: 'rgba(0, 210, 255, 0.3)',
                textStyle: {
                    color: '#f4f8ff',
                },
                formatter(params) {
                    if (!params) {
                        return '';
                    }

                    const items = Array.isArray(params) ? params : [params];
                    if (!items.length) {
                        return '';
                    }

                    const lines = [formatUtcTimestamp(items[0].value[0])];
                    for (const item of items) {
                        lines.push(`${item.marker}${item.seriesName}: ${item.value[1]}`);
                    }
                    return lines.join('<br>');
                },
            },
            xAxis: {
                type: 'value',
                min: paddedMinTime,
                max: paddedMaxTime,
                name: 'Time (UTC)',
                nameLocation: 'middle',
                nameGap: 36,
                axisLabel: {
                    color: '#ccefff',
                    formatter: value => formatUtcTick(value),
                    hideOverlap: true,
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(204, 239, 255, 0.35)',
                    },
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(0, 210, 255, 0.08)',
                    },
                },
            },
            yAxis: {
                type: 'value',
                name: 'Flux (SFU)',
                nameLocation: 'middle',
                nameGap: 52,
                axisLabel: {
                    color: '#ccefff',
                },
                axisLine: {
                    lineStyle: {
                        color: 'rgba(204, 239, 255, 0.35)',
                    },
                },
                splitLine: {
                    lineStyle: {
                        color: 'rgba(0, 210, 255, 0.08)',
                    },
                },
            },
            dataZoom: enableZoom ? [
                {
                    type: 'inside',
                    xAxisIndex: 0,
                    filterMode: 'none',
                    minSpan: 0,
                    zoomOnMouseWheel: true,
                    moveOnMouseMove: true,
                    moveOnMouseWheel: false,
                    preventDefaultMouseMove: true,
                },
                {
                    type: 'slider',
                    xAxisIndex: 0,
                    height: 28,
                    bottom: 18,
                    showDataShadow: false,
                    borderColor: 'rgba(0, 210, 255, 0.18)',
                    backgroundColor: 'rgba(255, 255, 255, 0.04)',
                    fillerColor: 'rgba(0, 210, 255, 0.12)',
                    textStyle: {
                        color: 'rgba(224, 224, 224, 0.68)',
                    },
                },
            ] : [],
            series: datasets,
        };
    }

    function renderFullChart(lightCurves) {
        destroyFullChart();
        const datasets = buildScatterDatasets(lightCurves);
        const time = lightCurves.time || [];
        currentVisibleRange = time.length ? normalizeRange(time[0], time[time.length - 1]) : null;

        fullChart = echarts.init(fullChartEl, null, {
            renderer: 'canvas',
            useDirtyRect: true,
        });

        fullChart.setOption(buildChartOption(lightCurves, datasets, fullChartHint, true));
        fullChart.on('datazoom', () => updateVisibleRange());
        fullResetZoomBtn.disabled = false;
    }

    function renderRangeChart(lightCurves) {
        destroyRangeChart();
        rangeChart = echarts.init(rangeChartEl, null, {
            renderer: 'canvas',
            useDirtyRect: true,
        });

        rangeChart.setOption(buildChartOption(lightCurves, buildScatterDatasets(lightCurves), rangeChartHint, false));
        syncSelectionHandles();
    }

    function renderBackgroundSubtractedChart(lightCurves) {
        destroyBackgroundSubtractedChart();
        lastBackgroundSubtractedLightCurves = lightCurves;
        backgroundSubtractedChart = echarts.init(backgroundSubtractedChartEl, null, {
            renderer: 'canvas',
            useDirtyRect: true,
        });

        backgroundSubtractedChart.setOption(
            buildChartOption(lightCurves, buildLineDatasets(lightCurves), backgroundSubtractedHint, true),
        );
        backgroundSubtractedChart.on('datazoom', () => syncFlareSelectionToVisibleRange());
        syncFlareSelectionToVisibleRange();
    }

    function renderBackgroundAverages(backgroundAverages) {
        backgroundAveragesSummary.innerHTML = '';

        const entries = Object.entries(backgroundAverages || {});
        if (!entries.length) {
            return;
        }

        for (const [frequency, value] of entries) {
            const card = document.createElement('div');
            card.className = 'background-average-card';
            card.innerHTML = `
                <span>${frequency}</span>
                <strong>${Number(value).toFixed(3)} SFU</strong>
            `;
            backgroundAveragesSummary.appendChild(card);
        }
    }

    function renderSummary(responseData) {
        const info = responseData.date_information || {};
        obsDayValue.textContent = info.obs_day || '-';
        startTimeValue.textContent = info.start_time || '-';
        endTimeValue.textContent = info.end_time || '-';
        frequenciesValue.textContent = (responseData.frequencies || []).join(', ') || '-';
    }

    function updateRangeSummaryFromLightCurves(lightCurves) {
        const time = lightCurves?.time || [];
        if (!time.length) {
            startTimeValue.textContent = '-';
            endTimeValue.textContent = '-';
            return;
        }

        startTimeValue.textContent = formatUtcTimestamp(time[0]);
        endTimeValue.textContent = formatUtcTimestamp(time[time.length - 1]);
    }

    function updateVisibleRange() {
        if (!fullChart || !lastFullLightCurves) {
            currentVisibleRange = null;
            cutRangeBtn.disabled = true;
            return;
        }

        const fullRange = getFullTimeRange(lastFullLightCurves);
        const chartOptions = fullChart.getOption();
        const zoomConfig = chartOptions?.dataZoom?.[0];

        if (!fullRange || !zoomConfig) {
            currentVisibleRange = fullRange;
        } else {
            const startPercent = Number.isFinite(zoomConfig.start) ? zoomConfig.start : 0;
            const endPercent = Number.isFinite(zoomConfig.end) ? zoomConfig.end : 100;
            const span = fullRange.end - fullRange.start;
            currentVisibleRange = normalizeRange(
                fullRange.start + (span * startPercent) / 100,
                fullRange.start + (span * endPercent) / 100,
            );
        }

        cutRangeBtn.disabled = !selectedFile || !lastFullLightCurves || !currentVisibleRange;
    }

    function getChartVisibleRange(chartInstance, lightCurves) {
        if (!chartInstance || !lightCurves) {
            return null;
        }

        const fullRange = getFullTimeRange(lightCurves);
        const chartOptions = chartInstance.getOption();
        const zoomConfig = chartOptions?.dataZoom?.[0];

        if (!fullRange || !zoomConfig) {
            return fullRange;
        }

        const startPercent = Number.isFinite(zoomConfig.start) ? zoomConfig.start : 0;
        const endPercent = Number.isFinite(zoomConfig.end) ? zoomConfig.end : 100;
        const span = fullRange.end - fullRange.start;

        return normalizeRange(
            fullRange.start + (span * startPercent) / 100,
            fullRange.start + (span * endPercent) / 100,
        );
    }

    function updateSelectionHint() {
        if (!selectedBackgroundRange) {
            selectionHint.textContent = 'Enter the pre-flare interval shown on the chart.';
            return;
        }

        selectionHint.textContent = `Background range: ${formatUtcTimestamp(selectedBackgroundRange.start)} to ${formatUtcTimestamp(selectedBackgroundRange.end)}.`;
    }

    function updateBackgroundButtonState() {
        removeBackgroundBtn.disabled = !selectedFile || !selectedBackgroundRange || !Number.isFinite(selectedBackgroundRange.end);
    }

    function syncBackgroundInputs(range) {
        if (!range) {
            preFlareStartInput.value = '';
            preFlareEndInput.value = '';
            return;
        }

        preFlareStartInput.value = toDatetimeLocalValue(range.start);
        preFlareEndInput.value = toDatetimeLocalValue(range.end);
    }

    function syncFlareInputs(range) {
        if (!range) {
            startFlareInput.value = '';
            endFlareInput.value = '';
            return;
        }

        startFlareInput.value = toDatetimeLocalValue(range.start);
        endFlareInput.value = toDatetimeLocalValue(range.end);
    }

    function clearBackgroundSelection() {
        selectedBackgroundRange = null;
        syncBackgroundInputs(null);
        updateSelectionHint();
        updateBackgroundButtonState();
        syncSelectionHandles();
    }

    function clampTimestampToRangeChart(timestamp) {
        const fullRange = getFullTimeRange(lastRangeLightCurves);
        if (!fullRange || !Number.isFinite(timestamp)) {
            return timestamp;
        }

        return Math.min(Math.max(timestamp, fullRange.start), fullRange.end);
    }

    function clampTimestampToLightCurves(lightCurves, timestamp) {
        const fullRange = getFullTimeRange(lightCurves);
        if (!fullRange || !Number.isFinite(timestamp)) {
            return timestamp;
        }

        return Math.min(Math.max(timestamp, fullRange.start), fullRange.end);
    }

    function syncSelectionHandles() {
        if (!rangeChart || !selectedBackgroundRange) {
            startPreFlareHandle.classList.add('hidden');
            endPreFlareHandle.classList.add('hidden');
            return;
        }

        const startPixel = rangeChart.convertToPixel({ xAxisIndex: 0 }, selectedBackgroundRange.start);
        const endPixel = rangeChart.convertToPixel({ xAxisIndex: 0 }, selectedBackgroundRange.end);

        if (!Number.isFinite(startPixel) || !Number.isFinite(endPixel)) {
            startPreFlareHandle.classList.add('hidden');
            endPreFlareHandle.classList.add('hidden');
            return;
        }

        startPreFlareHandle.style.left = `${startPixel}px`;
        endPreFlareHandle.style.left = `${endPixel}px`;
        startPreFlareHandle.classList.remove('hidden');
        endPreFlareHandle.classList.remove('hidden');
    }

    function syncFlareSelectionHandles() {
        if (!backgroundSubtractedChart || !selectedFlareRange) {
            startFlareHandle.classList.add('hidden');
            endFlareHandle.classList.add('hidden');
            return;
        }

        const startPixel = backgroundSubtractedChart.convertToPixel({ xAxisIndex: 0 }, selectedFlareRange.start);
        const endPixel = backgroundSubtractedChart.convertToPixel({ xAxisIndex: 0 }, selectedFlareRange.end);

        if (!Number.isFinite(startPixel) || !Number.isFinite(endPixel)) {
            startFlareHandle.classList.add('hidden');
            endFlareHandle.classList.add('hidden');
            return;
        }

        startFlareHandle.style.left = `${startPixel}px`;
        endFlareHandle.style.left = `${endPixel}px`;
        startFlareHandle.classList.remove('hidden');
        endFlareHandle.classList.remove('hidden');
    }

    function syncFlareSelectionToVisibleRange() {
        selectedFlareRange = getChartVisibleRange(
            backgroundSubtractedChart,
            lastBackgroundSubtractedLightCurves,
        );
        syncFlareInputs(selectedFlareRange);
        syncFlareSelectionHandles();
    }

    function setBackgroundSelection(start, end) {
        selectedBackgroundRange = normalizeRange(start, end);
        syncBackgroundInputs(selectedBackgroundRange);
        updateSelectionHint();
        updateBackgroundButtonState();
        syncSelectionHandles();
    }

    function setFlareSelection(start, end) {
        selectedFlareRange = normalizeRange(start, end);
        syncFlareInputs(selectedFlareRange);
        syncFlareSelectionHandles();
    }

    function updateDraggedBoundary(clientX) {
        if (!rangeChart || !selectedBackgroundRange || !draggingBoundary) {
            return;
        }

        const rect = rangeChartStage.getBoundingClientRect();
        const pixelX = clientX - rect.left;
        const pixelY = Math.max(44, Math.min(rangeChart.getHeight() - 52, Math.round(rangeChart.getHeight() / 2)));
        const timestamp = clampTimestampToRangeChart(
            rangeChart.convertFromPixel({ xAxisIndex: 0 }, [pixelX, pixelY]),
        );

        if (!Number.isFinite(timestamp)) {
            return;
        }

        if (draggingBoundary === 'start') {
            setBackgroundSelection(timestamp, selectedBackgroundRange.end);
            return;
        }

        setBackgroundSelection(selectedBackgroundRange.start, timestamp);
    }

    function updateDraggedFlareBoundary(clientX) {
        if (!backgroundSubtractedChart || !selectedFlareRange || !draggingFlareBoundary) {
            return;
        }

        const rect = backgroundSubtractedChartStage.getBoundingClientRect();
        const pixelX = clientX - rect.left;
        const pixelY = Math.max(44, Math.min(backgroundSubtractedChart.getHeight() - 52, Math.round(backgroundSubtractedChart.getHeight() / 2)));
        const timestamp = clampTimestampToLightCurves(
            lastBackgroundSubtractedLightCurves,
            backgroundSubtractedChart.convertFromPixel({ xAxisIndex: 0 }, [pixelX, pixelY]),
        );

        if (!Number.isFinite(timestamp)) {
            return;
        }

        if (draggingFlareBoundary === 'start') {
            setFlareSelection(timestamp, selectedFlareRange.end);
            return;
        }

        setFlareSelection(selectedFlareRange.start, timestamp);
    }

    function toDatetimeLocalValue(timestamp) {
        if (!Number.isFinite(timestamp)) {
            return '';
        }

        const date = new Date(timestamp);
        const year = date.getUTCFullYear();
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const day = String(date.getUTCDate()).padStart(2, '0');
        const hours = String(date.getUTCHours()).padStart(2, '0');
        const minutes = String(date.getUTCMinutes()).padStart(2, '0');
        const seconds = String(date.getUTCSeconds()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
    }

    function parseDatetimeInput(value) {
        if (!value) {
            return null;
        }

        const timestamp = Date.parse(`${value}Z`);
        return Number.isFinite(timestamp) ? timestamp : null;
    }

    function initializeDefaultBackgroundRange(lightCurves) {
        const time = lightCurves?.time || [];
        if (!time.length) {
            clearBackgroundSelection();
            return;
        }

        const start = time[0];
        const end = Math.min(start + (2 * 60 * 1000), time[time.length - 1]);
        setBackgroundSelection(start, end);
    }

    function initializeDefaultFlareRange(lightCurves) {
        const fullRange = getFullTimeRange(lightCurves);
        if (!fullRange) {
            selectedFlareRange = null;
            syncFlareInputs(null);
            syncFlareSelectionHandles();
            return;
        }

        setFlareSelection(fullRange.start, fullRange.end);
    }

    function handleBackgroundInputChange() {
        const start = parseDatetimeInput(preFlareStartInput.value);
        const end = parseDatetimeInput(preFlareEndInput.value);

        if (!Number.isFinite(start) || !Number.isFinite(end)) {
            selectedBackgroundRange = null;
            updateSelectionHint();
            updateBackgroundButtonState();
            syncSelectionHandles();
            return;
        }

        setBackgroundSelection(
            clampTimestampToRangeChart(start),
            clampTimestampToRangeChart(end),
        );
    }

    function handleFlareInputChange() {
        const start = parseDatetimeInput(startFlareInput.value);
        const end = parseDatetimeInput(endFlareInput.value);

        if (!Number.isFinite(start) || !Number.isFinite(end)) {
            selectedFlareRange = null;
            syncFlareSelectionHandles();
            return;
        }

        setFlareSelection(
            clampTimestampToLightCurves(lastBackgroundSubtractedLightCurves, start),
            clampTimestampToLightCurves(lastBackgroundSubtractedLightCurves, end),
        );
    }

    function handleTimeInputStep(input) {
        if (input === preFlareStartInput || input === preFlareEndInput) {
            handleBackgroundInputChange();
            return;
        }

        if (input === startFlareInput || input === endFlareInput) {
            handleFlareInputChange();
        }
    }

    function stepTimeInput(input, direction) {
        const currentTimestamp = parseDatetimeInput(input.value);
        if (!Number.isFinite(currentTimestamp)) {
            return;
        }

        const steppedTimestamp = currentTimestamp + (direction * 1000);
        input.value = toDatetimeLocalValue(steppedTimestamp);
        handleTimeInputStep(input);
    }

    function clearTimeStepHold() {
        if (timeStepHoldTimeout) {
            window.clearTimeout(timeStepHoldTimeout);
            timeStepHoldTimeout = null;
        }

        if (timeStepHoldInterval) {
            window.clearInterval(timeStepHoldInterval);
            timeStepHoldInterval = null;
        }
    }

    function startTimeStepHold(input, direction) {
        clearTimeStepHold();
        stepTimeInput(input, direction);
        timeStepHoldTimeout = window.setTimeout(() => {
            timeStepHoldInterval = window.setInterval(() => {
                stepTimeInput(input, direction);
            }, 100);
        }, 350);
    }

    async function analyzeSelectedFile() {
        if (!selectedFile) {
            showError('Select a file before running the analysis.');
            return;
        }

        clearError();
        setLoading(true);

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch(`${API_BASE_URL}/norp/analyze`, {
                method: 'POST',
                body: formData,
            });

            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.detail || 'NorP analysis failed.');
            }

            renderSummary(payload);
            lastFullLightCurves = payload.light_curves || { time: [], frequencies: [] };
            lastRangeLightCurves = null;
            updateRangeSummaryFromLightCurves(lastFullLightCurves);
            resultsPanel.classList.remove('hidden');
            setFullChartVisibility(true);
            setRangeChartVisibility(false);
            setCutRangeVisibility(true);
            setBackgroundPanelVisibility(false);
            setBackgroundSubtractedVisibility(false);
            renderFullChart(lastFullLightCurves);
        } catch (error) {
            showError(error.message || 'Unable to analyze the selected file.');
        } finally {
            setLoading(false);
        }
    }

    async function cutVisibleRange() {
        if (!selectedFile) {
            showError('Select a file before cutting the current view.');
            return;
        }

        if (!currentVisibleRange) {
            showError('Zoom to a valid range before cutting.');
            return;
        }

        clearError();
        setLoading(true);

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('start_time', Math.round(currentVisibleRange.start));
        formData.append('end_time', Math.round(currentVisibleRange.end));

        try {
            const response = await fetch(`${API_BASE_URL}/norp/analyze-range`, {
                method: 'POST',
                body: formData,
            });

            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.detail || 'NorP range analysis failed.');
            }

            lastRangeLightCurves = payload.light_curves || { time: [], frequencies: [] };
            updateRangeSummaryFromLightCurves(lastRangeLightCurves);
            resultsPanel.classList.remove('hidden');
            setFullChartVisibility(false);
            setRangeChartVisibility(true);
            setCutRangeVisibility(false);
            setBackgroundPanelVisibility(true);
            setBackgroundSubtractedVisibility(false);
            renderRangeChart(lastRangeLightCurves);
            initializeDefaultBackgroundRange(lastRangeLightCurves);
        } catch (error) {
            showError(error.message || 'Unable to cut the visible range.');
        } finally {
            setLoading(false);
        }
    }

    async function removeBackgroundNoise() {
        if (!selectedFile) {
            showError('Select a file before removing background noise.');
            return;
        }

        const selectedRange = getFullTimeRange(lastRangeLightCurves);
        if (!selectedRange) {
            showError('Cut a valid range before removing background noise.');
            return;
        }

        if (!selectedBackgroundRange || !Number.isFinite(selectedBackgroundRange.end)) {
            showError('Fill a valid pre-flare interval before removing noise.');
            return;
        }

        clearError();
        setLoading(true);

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('start_time', Math.round(selectedRange.start));
        formData.append('end_time', Math.round(selectedRange.end));
        formData.append('pre_flare_start', Math.round(selectedBackgroundRange.start));
        formData.append('pre_flare_end', Math.round(selectedBackgroundRange.end));

        try {
            const response = await fetch(`${API_BASE_URL}/norp/remove-background-noise`, {
                method: 'POST',
                body: formData,
            });

            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.detail || 'NorP background noise removal failed.');
            }

            resultsPanel.classList.remove('hidden');
            syncBackgroundInputs(selectedBackgroundRange);
            setBackgroundSubtractedVisibility(true);
            renderBackgroundAverages(payload.light_curves?.background_averages);
            renderBackgroundSubtractedChart(payload.light_curves || { time: [], frequencies: [] });
            initializeDefaultFlareRange(payload.light_curves || { time: [], frequencies: [] });
        } catch (error) {
            showError(error.message || 'Unable to remove background noise.');
        } finally {
            setLoading(false);
        }
    }

    selectFileBtn.addEventListener('click', () => fitsFileInput.click());
    fitsFileInput.addEventListener('change', event => {
        setSelectedFile(event.target.files?.[0] || null);
    });

    analyzeBtn.addEventListener('click', analyzeSelectedFile);
    cutRangeBtn.addEventListener('click', cutVisibleRange);
    preFlareStartInput.addEventListener('change', handleBackgroundInputChange);
    preFlareEndInput.addEventListener('change', handleBackgroundInputChange);
    startFlareInput.addEventListener('change', handleFlareInputChange);
    endFlareInput.addEventListener('change', handleFlareInputChange);
    timeStepButtons.forEach(button => {
        const targetId = button.dataset.target;
        const direction = Number(button.dataset.direction || 0);
        const input = document.getElementById(targetId);

        if (!(input instanceof HTMLInputElement) || !direction) {
            return;
        }

        button.addEventListener('mousedown', event => {
            event.preventDefault();
            startTimeStepHold(input, direction);
        });
        button.addEventListener('mouseup', clearTimeStepHold);
        button.addEventListener('mouseleave', clearTimeStepHold);
        button.addEventListener('touchstart', event => {
            event.preventDefault();
            startTimeStepHold(input, direction);
        }, { passive: false });
        button.addEventListener('touchend', clearTimeStepHold);
        button.addEventListener('touchcancel', clearTimeStepHold);
    });
    document.addEventListener('mouseup', clearTimeStepHold);
    document.addEventListener('touchend', clearTimeStepHold);
    removeBackgroundBtn.addEventListener('click', removeBackgroundNoise);

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, event => {
            event.preventDefault();
            dropZone.classList.add('is-active');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, event => {
            event.preventDefault();
            dropZone.classList.remove('is-active');
        });
    });

    dropZone.addEventListener('drop', event => {
        const [file] = event.dataTransfer?.files || [];
        setSelectedFile(file || null);
    });

    dropZone.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            fitsFileInput.click();
        }
    });

    fullResetZoomBtn.addEventListener('click', () => {
        if (!fullChart) {
            return;
        }

        fullChart.dispatchAction({
            type: 'dataZoom',
            start: 0,
            end: 100,
        });
        updateVisibleRange();
    });

    startPreFlareHandle.addEventListener('mousedown', event => {
        event.preventDefault();
        draggingBoundary = 'start';
    });

    endPreFlareHandle.addEventListener('mousedown', event => {
        event.preventDefault();
        draggingBoundary = 'end';
    });

    startFlareHandle.addEventListener('mousedown', event => {
        event.preventDefault();
        draggingFlareBoundary = 'start';
    });

    endFlareHandle.addEventListener('mousedown', event => {
        event.preventDefault();
        draggingFlareBoundary = 'end';
    });

    document.addEventListener('mousemove', event => {
        if (draggingBoundary) {
            event.preventDefault();
            updateDraggedBoundary(event.clientX);
        }

        if (draggingFlareBoundary) {
            event.preventDefault();
            updateDraggedFlareBoundary(event.clientX);
        }
    });

    document.addEventListener('mouseup', () => {
        draggingBoundary = null;
        draggingFlareBoundary = null;
    });

    window.addEventListener('resize', () => {
        fullChart?.resize();
        rangeChart?.resize();
        backgroundSubtractedChart?.resize();
        syncSelectionHandles();
        syncFlareSelectionHandles();
    });

    analyzeBtn.disabled = true;
    resetUiState();
});
