document.addEventListener('DOMContentLoaded', () => {
    const PARAM_NAMES = ['delta', 'nelectron', 'bmag', 'asize'];
    const EXAMPLE_SETTINGS_PATHS = [
        '../../examples/demo_settings.json',
        '/examples/demo_settings.json',
        'examples/demo_settings.json'
    ];

    const form = document.getElementById('gsyncForm');
    const runBtn = document.getElementById('runBtn');
    const runBtnPython = document.getElementById('runBtnPython');
    const loader = document.getElementById('loader');
    const resultsPanel = document.getElementById('resultsPanel');
    const resultImage = document.getElementById('resultImage');
    const fitReport = document.getElementById('fitReport');
    const bestValuesContainer = document.getElementById('bestValues');
    const datFile = document.getElementById('datFile');
    const xDataText = document.getElementById('xData');
    const yDataText = document.getElementById('yData');
    const importMode = document.getElementById('importMode');
    const importContainer = document.getElementById('importContainer');
    const importJsonBtn = document.getElementById('importJsonBtn');
    const exportJsonBtn = document.getElementById('exportJsonBtn');
    const fillExampleBtn = document.getElementById('fillExampleBtn');
    const jsonFile = document.getElementById('jsonFile');
    const exportResultsBtn = document.getElementById('exportResultsBtn');

    let currentEndpoint = '/gsync';
    let lastSimulationData = null;

    function parseNumber(value) {
        const parsed = parseFloat(value);
        return Number.isNaN(parsed) ? null : parsed;
    }

    function getParamConfig(name) {
        const vary = document.getElementById(`${name}_vary`).checked;
        const value = parseNumber(document.getElementById(`${name}_val`).value);

        if (!vary) {
            return {
                value,
                min: 0,
                max: 0,
                vary: false
            };
        }

        return {
            value,
            min: parseNumber(document.getElementById(`${name}_min`).value),
            max: parseNumber(document.getElementById(`${name}_max`).value),
            vary: true
        };
    }

    function buildFormData() {
        return {
            prefix: document.getElementById('prefix').value,
            viewAngle: parseNumber(document.getElementById('viewAngle').value),
            height: parseNumber(document.getElementById('height').value),
            j1: parseInt(document.getElementById('j1').value, 10),
            j2: parseInt(document.getElementById('j2').value, 10),
            etr: parseNumber(document.getElementById('etr').value),
            np: parseNumber(document.getElementById('np').value),
            freq: document.getElementById('xData').value.split(',').map(v => parseFloat(v.trim())).filter(v => !Number.isNaN(v)),
            sfu: document.getElementById('yData').value.split(',').map(v => parseFloat(v.trim())).filter(v => !Number.isNaN(v)),
            params: PARAM_NAMES.reduce((acc, name) => {
                acc[name] = getParamConfig(name);
                return acc;
            }, {})
        };
    }

    function updateParamRowState(name) {
        const row = document.querySelector(`.param-row[data-param="${name}"]`);
        const varyCheckbox = document.getElementById(`${name}_vary`);
        const minInput = document.getElementById(`${name}_min`);
        const maxInput = document.getElementById(`${name}_max`);
        const isFixed = !varyCheckbox.checked;

        row.classList.toggle('is-fixed', isFixed);
        minInput.disabled = isFixed;
        maxInput.disabled = isFixed;

        if (isFixed) {
            minInput.value = '';
            maxInput.value = '';
        }
    }

    function applySettings(data) {
        if (data.prefix !== undefined) document.getElementById('prefix').value = data.prefix;
        if (data.viewAngle !== undefined) document.getElementById('viewAngle').value = data.viewAngle;
        if (data.height !== undefined) document.getElementById('height').value = data.height;
        if (data.j1 !== undefined) document.getElementById('j1').value = data.j1;
        if (data.j2 !== undefined) document.getElementById('j2').value = data.j2;
        if (data.etr !== undefined) document.getElementById('etr').value = data.etr;
        if (data.np !== undefined) document.getElementById('np').value = data.np;

        if (Array.isArray(data.freq)) document.getElementById('xData').value = data.freq.join(', ');
        if (Array.isArray(data.sfu)) document.getElementById('yData').value = data.sfu.join(', ');

        if (data.params) {
            PARAM_NAMES.forEach(name => {
                const param = data.params[name];
                if (!param) return;

                document.getElementById(`${name}_val`).value = param.value ?? '';
                document.getElementById(`${name}_vary`).checked = Boolean(param.vary);
                document.getElementById(`${name}_min`).value = param.min ?? '';
                document.getElementById(`${name}_max`).value = param.max ?? '';
                updateParamRowState(name);
            });
        }
    }

    function downloadJsonFile(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    }

    async function loadExampleSettings() {
        for (const path of EXAMPLE_SETTINGS_PATHS) {
            try {
                const response = await fetch(path);
                if (response.ok) {
                    return await response.json();
                }
            } catch (error) {
                console.error(`Failed to load example from ${path}`, error);
            }
        }

        throw new Error('Could not locate demo_settings.json');
    }

    exportResultsBtn.addEventListener('click', () => {
        if (!lastSimulationData) return;

        const zip = new JSZip();
        const prefix = document.getElementById('prefix').value || 'Unknown';
        const imgData = lastSimulationData.image.replace(/^data:image\/(png|jpg);base64,/, '');
        zip.file(`SOL${prefix}.png`, imgData, { base64: true });

        if (lastSimulationData.bins && lastSimulationData.flux) {
            let datContent = '';
            for (let i = 0; i < lastSimulationData.bins.length; i += 1) {
                datContent += `${lastSimulationData.bins[i]} ${lastSimulationData.flux[i]}\n`;
            }
            zip.file(`fluxSOL${prefix}.dat`, datContent);
        }

        zip.generateAsync({ type: 'blob' }).then(content => {
            const url = URL.createObjectURL(content);
            const link = document.createElement('a');
            link.href = url;
            link.download = `SOL${prefix}_Results.zip`;
            link.click();
            URL.revokeObjectURL(url);
        });
    });

    exportJsonBtn.addEventListener('click', () => {
        const formData = buildFormData();
        downloadJsonFile(formData, `gsync_settings_${formData.prefix || 'config'}.json`);
    });

    importJsonBtn.addEventListener('click', () => jsonFile.click());

    fillExampleBtn.addEventListener('click', async () => {
        try {
            const exampleData = await loadExampleSettings();
            applySettings(exampleData);
        } catch (error) {
            console.error(error);
            alert(`Unable to load example settings: ${error.message}`);
        }
    });

    jsonFile.addEventListener('change', e => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = event => {
            try {
                const data = JSON.parse(event.target.result);
                applySettings(data);
                e.target.value = '';
            } catch (error) {
                alert(`Error parsing JSON file: ${error.message}`);
            }
        };
        reader.readAsText(file);
    });

    runBtn.addEventListener('click', () => {
        currentEndpoint = '/gsync';
    });

    runBtnPython.addEventListener('click', () => {
        currentEndpoint = '/python/gsync';
    });

    importMode.addEventListener('change', () => {
        if (importMode.checked) {
            importContainer.classList.remove('hidden');
            xDataText.placeholder = 'Importing from file...';
            yDataText.placeholder = 'Importing from file...';
            xDataText.readOnly = true;
            yDataText.readOnly = true;
            xDataText.style.opacity = '0.7';
            yDataText.style.opacity = '0.7';
            return;
        }

        importContainer.classList.add('hidden');
        xDataText.placeholder = 'e.g. 1e9, 2e9, 5e9';
        yDataText.placeholder = 'e.g. 10, 50, 150';
        xDataText.readOnly = false;
        yDataText.readOnly = false;
        xDataText.style.opacity = '1';
        yDataText.style.opacity = '1';
    });

    datFile.addEventListener('change', e => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = event => {
            const content = event.target.result;
            const lines = content.trim().split('\n');
            const freqs = [];
            const fluxes = [];

            lines.forEach(line => {
                const parts = line.trim().split(/\s+/);
                if (parts.length >= 2) {
                    freqs.push(parts[0]);
                    fluxes.push(parts[1]);
                }
            });

            xDataText.value = freqs.join(', ');
            yDataText.value = fluxes.join(', ');

            const nameMatch = file.name.match(/NoRP (\d{4}-\d{2}-\d{2})/);
            if (nameMatch) {
                document.getElementById('prefix').value = nameMatch[1].replace(/-/g, '');
            }
        };
        reader.readAsText(file);
    });

    form.addEventListener('submit', async e => {
        e.preventDefault();

        loader.classList.remove('hidden');
        resultsPanel.classList.add('hidden');
        runBtn.disabled = true;
        runBtnPython.disabled = true;

        try {
            const formData = buildFormData();
            const apiUrl = `/api${currentEndpoint}`;
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Simulation Failed');
            }

            const result = await response.json();
            displayResults(result.data);
        } catch (error) {
            console.error(error);
            alert(`Simulation Aborted: ${error.message}`);
        } finally {
            loader.classList.add('hidden');
            runBtn.disabled = false;
            runBtnPython.disabled = false;
        }
    });

    function displayResults(data) {
        lastSimulationData = data;
        resultsPanel.classList.remove('hidden');

        if (data.image) {
            resultImage.src = `data:image/png;base64,${data.image}`;
        }

        fitReport.textContent = data.fit_report;
        bestValuesContainer.innerHTML = '';

        if (data.best_values) {
            Object.entries(data.best_values).forEach(([key, val]) => {
                const card = document.createElement('div');
                card.className = 'best-value-card';

                const label = document.createElement('span');
                label.className = 'best-value-label';
                label.textContent = key;

                const valueDisplay = document.createElement('span');
                valueDisplay.className = 'best-value-data';
                valueDisplay.textContent = typeof val === 'number' ? val.toExponential(4) : val;

                card.appendChild(label);
                card.appendChild(valueDisplay);
                bestValuesContainer.appendChild(card);
            });
        }

        resultsPanel.scrollIntoView({ behavior: 'smooth' });
    }

    PARAM_NAMES.forEach(name => {
        document.getElementById(`${name}_vary`).addEventListener('change', () => {
            updateParamRowState(name);
        });
        updateParamRowState(name);
    });
});
