document.addEventListener('DOMContentLoaded', () => {
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
    const jsonFile = document.getElementById('jsonFile');
    const exportResultsBtn = document.getElementById('exportResultsBtn');

    let currentEndpoint = '/gsync';
    let lastSimulationData = null;

    // Export Results Logic
    exportResultsBtn.addEventListener('click', () => {
        if (!lastSimulationData) return;

        const zip = new JSZip();
        const prefix = document.getElementById('prefix').value || 'Unknown';
        
        // Add Image
        // Remove header if present (data:image/png;base64,)
        const imgData = lastSimulationData.image.replace(/^data:image\/(png|jpg);base64,/, "");
        zip.file(`SOL${prefix}.png`, imgData, {base64: true});

        // Add Data File
        if (lastSimulationData.bins && lastSimulationData.flux) {
            let datContent = "";
            for (let i = 0; i < lastSimulationData.bins.length; i++) {
                datContent += `${lastSimulationData.bins[i]} ${lastSimulationData.flux[i]}\n`;
            }
            zip.file(`fluxSOL${prefix}.dat`, datContent);
        }

        // Generate and Download
        zip.generateAsync({type:"blob"})
        .then(function(content) {
            const url = URL.createObjectURL(content);
            const a = document.createElement('a');
            a.href = url;
            a.download = `SOL${prefix}_Results.zip`;
            a.click();
            URL.revokeObjectURL(url);
        });
    });

    // JSON Import/Export Logic
    exportJsonBtn.addEventListener('click', () => {
        const formData = {
            prefix: document.getElementById('prefix').value,
            viewAngle: parseFloat(document.getElementById('viewAngle').value),
            height: parseFloat(document.getElementById('height').value),
            j1: parseInt(document.getElementById('j1').value),
            j2: parseInt(document.getElementById('j2').value),
            etr: parseFloat(document.getElementById('etr').value),
            np: parseFloat(document.getElementById('np').value),
            freq: document.getElementById('xData').value.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v)),
            sfu: document.getElementById('yData').value.split(',').map(v => parseFloat(v.trim())).filter(v => !isNaN(v)),
            params: {
                delta: {
                    value: parseFloat(document.getElementById('delta_val').value),
                    min: parseFloat(document.getElementById('delta_min').value),
                    max: parseFloat(document.getElementById('delta_max').value),
                    vary: document.getElementById('delta_vary').checked
                },
                nelectron: {
                    value: parseFloat(document.getElementById('nelectron_val').value),
                    min: parseFloat(document.getElementById('nelectron_min').value),
                    max: parseFloat(document.getElementById('nelectron_max').value),
                    vary: document.getElementById('nelectron_vary').checked
                },
                bmag: {
                    value: parseFloat(document.getElementById('bmag_val').value),
                    min: parseFloat(document.getElementById('bmag_min').value),
                    max: parseFloat(document.getElementById('bmag_max').value),
                    vary: document.getElementById('bmag_vary').checked
                },
                asize: {
                    value: parseFloat(document.getElementById('asize_val').value),
                    min: parseFloat(document.getElementById('asize_min').value),
                    max: parseFloat(document.getElementById('asize_max').value),
                    vary: document.getElementById('asize_vary').checked
                }
            }
        };

        const blob = new Blob([JSON.stringify(formData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `gsync_settings_${formData.prefix || 'config'}.json`;
        a.click();
        URL.revokeObjectURL(url);
    });

    importJsonBtn.addEventListener('click', () => jsonFile.click());

    jsonFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            try {
                const data = JSON.parse(event.target.result);
                
                // Fill Environment Settings
                if (data.prefix) document.getElementById('prefix').value = data.prefix;
                if (data.viewAngle !== undefined) document.getElementById('viewAngle').value = data.viewAngle;
                if (data.height !== undefined) document.getElementById('height').value = data.height;
                if (data.j1 !== undefined) document.getElementById('j1').value = data.j1;
                if (data.j2 !== undefined) document.getElementById('j2').value = data.j2;
                if (data.etr !== undefined) document.getElementById('etr').value = data.etr;
                if (data.np !== undefined) document.getElementById('np').value = data.np;
                
                // Fill Data
                if (data.freq) document.getElementById('xData').value = data.freq.join(', ');
                if (data.sfu) document.getElementById('yData').value = data.sfu.join(', ');

                // Fill Optimization Parameters
                if (data.params) {
                    const p = data.params;
                    if (p.delta) {
                        document.getElementById('delta_val').value = p.delta.value;
                        document.getElementById('delta_min').value = p.delta.min;
                        document.getElementById('delta_max').value = p.delta.max;
                        document.getElementById('delta_vary').checked = p.delta.vary;
                    }
                    if (p.nelectron) {
                        document.getElementById('nelectron_val').value = p.nelectron.value;
                        document.getElementById('nelectron_min').value = p.nelectron.min;
                        document.getElementById('nelectron_max').value = p.nelectron.max;
                        document.getElementById('nelectron_vary').checked = p.nelectron.vary;
                    }
                    if (p.bmag) {
                        document.getElementById('bmag_val').value = p.bmag.value;
                        document.getElementById('bmag_min').value = p.bmag.min;
                        document.getElementById('bmag_max').value = p.bmag.max;
                        document.getElementById('bmag_vary').checked = p.bmag.vary;
                    }
                    if (p.asize) {
                        document.getElementById('asize_val').value = p.asize.value;
                        document.getElementById('asize_min').value = p.asize.min;
                        document.getElementById('asize_max').value = p.asize.max;
                        document.getElementById('asize_vary').checked = p.asize.vary;
                    }
                }
                
                // Reset file input so same file can be imported again
                e.target.value = '';
                
            } catch (err) {
                alert('Error parsing JSON file: ' + err.message);
            }
        };
        reader.readAsText(file);
    });

    // Capture which button was clicked
    runBtn.addEventListener('click', () => currentEndpoint = '/gsync');
    runBtnPython.addEventListener('click', () => currentEndpoint = '/python/gsync');

    // Toggle Input Mode
    importMode.addEventListener('change', () => {
        if (importMode.checked) {
            importContainer.classList.remove('hidden');
            xDataText.placeholder = "Importing from file...";
            yDataText.placeholder = "Importing from file...";
            xDataText.readOnly = true;
            yDataText.readOnly = true;
            // Add a visual locked style
            xDataText.style.opacity = "0.7";
            yDataText.style.opacity = "0.7";
        } else {
            importContainer.classList.add('hidden');
            xDataText.placeholder = "e.g. 1e9, 2e9, 5e9";
            yDataText.placeholder = "e.g. 10, 50, 150";
            xDataText.readOnly = false;
            yDataText.readOnly = false;
            xDataText.style.opacity = "1";
            yDataText.style.opacity = "1";
        }
    });

    // File Import Logic
    datFile.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
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
            
            // Set prefix based on filename if possible
            const nameMatch = file.name.match(/NoRP (\d{4}-\d{2}-\d{2})/);
            if (nameMatch) {
                document.getElementById('prefix').value = nameMatch[1].replace(/-/g, '');
            }
        };
        reader.readAsText(file);
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // UI Feedback
        loader.classList.remove('hidden');
        resultsPanel.classList.add('hidden');
        runBtn.disabled = true;
        runBtnPython.disabled = true;

        try {
            // Build the data object
            const formData = {
                prefix: document.getElementById('prefix').value,
                viewAngle: parseFloat(document.getElementById('viewAngle').value),
                height: parseFloat(document.getElementById('height').value),
                j1: parseInt(document.getElementById('j1').value),
                j2: parseInt(document.getElementById('j2').value),
                etr: parseFloat(document.getElementById('etr').value),
                np: parseFloat(document.getElementById('np').value),
                freq: document.getElementById('xData').value.split(',').map(v => parseFloat(v.trim())),
                sfu: document.getElementById('yData').value.split(',').map(v => parseFloat(v.trim())),
                params: {
                    delta: {
                        value: parseFloat(document.getElementById('delta_val').value),
                        min: parseFloat(document.getElementById('delta_min').value),
                        max: parseFloat(document.getElementById('delta_max').value),
                        vary: document.getElementById('delta_vary').checked
                    },
                    nelectron: {
                        value: parseFloat(document.getElementById('nelectron_val').value),
                        min: parseFloat(document.getElementById('nelectron_min').value),
                        max: parseFloat(document.getElementById('nelectron_max').value),
                        vary: document.getElementById('nelectron_vary').checked
                    },
                    bmag: {
                        value: parseFloat(document.getElementById('bmag_val').value),
                        min: parseFloat(document.getElementById('bmag_min').value),
                        max: parseFloat(document.getElementById('bmag_max').value),
                        vary: document.getElementById('bmag_vary').checked
                    },
                    asize: {
                        value: parseFloat(document.getElementById('asize_val').value),
                        min: parseFloat(document.getElementById('asize_min').value),
                        max: parseFloat(document.getElementById('asize_max').value),
                        vary: document.getElementById('asize_vary').checked
            };

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
            alert('Simulation Aborted: ' + error.message);
        } finally {
            loader.classList.add('hidden');
            runBtn.disabled = false;
            runBtnPython.disabled = false;
        }
    });

    function displayResults(data) {
        lastSimulationData = data;
        resultsPanel.classList.remove('hidden');
        
        // Show Image
        if (data.image) {
            resultImage.src = `data:image/png;base64,${data.image}`;
        }

        // Show Fit Report
        fitReport.textContent = data.fit_report;

        // Show Best Values
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

        // Smooth scroll to results
        resultsPanel.scrollIntoView({ behavior: 'smooth' });
    }
});
