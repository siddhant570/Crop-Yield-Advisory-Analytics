/**
 * Crop Yield Advisory Analytics - Client Script
 * Handles Chart.js chart initializations, live table search, and interactive filters.
 */

document.addEventListener("DOMContentLoaded", function () {
    console.log("Crop Yield Advisory Analytics - Client Script Initialized");

    // Initialize Dashboard Charts if chart data is embedded
    if (typeof dashboardChartData !== "undefined") {
        initDashboardCharts(dashboardChartData);
    }

    // Initialize Visualization Page Charts if visualization payload exists
    if (typeof visChartData !== "undefined") {
        initVisualizationCharts(visChartData);
    }

    // Live table search handler
    const searchInput = document.getElementById("tableSearchInput");
    if (searchInput) {
        searchInput.addEventListener("keyup", function () {
            const filter = searchInput.value.toLowerCase();
            const rows = document.querySelectorAll("#agriDataTable tbody tr");

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? "" : "none";
            });
        });
    }
});

/**
 * Renders the 4 summary charts on Dashboard page
 */
function initDashboardCharts(data) {
    const ctxCrop = document.getElementById("dashCropYieldChart");
    if (ctxCrop) {
        new Chart(ctxCrop, {
            type: "bar",
            data: {
                labels: data.crop_labels,
                datasets: [{
                    label: "Average Yield (tons/ha)",
                    data: data.crop_yields,
                    backgroundColor: "#2d6a4f",
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, title: { display: true, text: "Yield (tons/ha)" } } }
            }
        });
    }

    const ctxRain = document.getElementById("dashRainfallChart");
    if (ctxRain) {
        new Chart(ctxRain, {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Rainfall vs Yield",
                    data: data.rainfall_scatter,
                    backgroundColor: "#1d4ed8"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: "Rainfall (mm)" } },
                    y: { title: { display: true, text: "Yield (tons/ha)" } }
                }
            }
        });
    }

    const ctxTemp = document.getElementById("dashTempChart");
    if (ctxTemp) {
        new Chart(ctxTemp, {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Temperature vs Yield",
                    data: data.temp_scatter,
                    backgroundColor: "#d97706"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: "Temperature (°C)" } },
                    y: { title: { display: true, text: "Yield (tons/ha)" } }
                }
            }
        });
    }

    const ctxFert = document.getElementById("dashFertChart");
    if (ctxFert) {
        new Chart(ctxFert, {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Fertilizer vs Yield",
                    data: data.fert_scatter,
                    backgroundColor: "#059669"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: "Fertilizer (kg/ha)" } },
                    y: { title: { display: true, text: "Yield (tons/ha)" } }
                }
            }
        });
    }
}

/**
 * Renders the 5 specialized charts on Crop Yield Visualization page
 */
function initVisualizationCharts(data) {
    // 1. Crop-wise Yield Bar Chart
    const ctx1 = document.getElementById("visCropYieldChart");
    if (ctx1) {
        new Chart(ctx1, {
            type: "bar",
            data: {
                labels: data.crop_labels,
                datasets: [{
                    label: "Avg Yield (tons/ha)",
                    data: data.crop_yields,
                    backgroundColor: ["#1b4332", "#2d6a4f", "#40916c", "#52b788", "#74c69d", "#95d5b2"],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    // 2. Rainfall Scatter
    const ctx2 = document.getElementById("visRainfallChart");
    if (ctx2) {
        new Chart(ctx2, {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Rainfall (mm) vs Yield",
                    data: data.rainfall_scatter,
                    backgroundColor: "#2563eb",
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: "Rainfall (mm)" } },
                    y: { title: { display: true, text: "Yield (tons/ha)" } }
                }
            }
        });
    }

    // 3. Temp Scatter
    const ctx3 = document.getElementById("visTempChart");
    if (ctx3) {
        new Chart(ctx3, {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Temperature (°C) vs Yield",
                    data: data.temp_scatter,
                    backgroundColor: "#ea580c",
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: "Temperature (°C)" } },
                    y: { title: { display: true, text: "Yield (tons/ha)" } }
                }
            }
        });
    }

    // 4. Fertilizer Chart
    const ctx4 = document.getElementById("visFertChart");
    if (ctx4) {
        new Chart(ctx4, {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Fertilizer (kg/ha) vs Yield",
                    data: data.fert_scatter,
                    backgroundColor: "#16a34a",
                    pointRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { title: { display: true, text: "Fertilizer (kg/ha)" } },
                    y: { title: { display: true, text: "Yield (tons/ha)" } }
                }
            }
        });
    }

    // 5. Irrigation Bar Chart
    const ctx5 = document.getElementById("visIrrChart");
    if (ctx5) {
        new Chart(ctx5, {
            type: "bar",
            data: {
                labels: data.irr_labels,
                datasets: [{
                    label: "Average Yield by Irrigation Method",
                    data: data.irr_yields,
                    backgroundColor: "#0891b2",
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { y: { beginAtZero: true } }
            }
        });
    }
}

/**
 * Toggle Add Record Form Visibility
 */
function toggleAddRecordForm(e) {
    if (e && e.preventDefault) {
        e.preventDefault();
    }
    const formCard = document.getElementById("addRecordFormContainer");
    if (formCard) {
        const isHidden = window.getComputedStyle(formCard).display === "none";
        if (isHidden) {
            formCard.style.display = "block";
            formCard.scrollIntoView({ behavior: 'smooth' });
            const firstInput = document.getElementById("crop_type");
            if (firstInput) firstInput.focus();
        } else {
            formCard.style.display = "none";
        }
    }
}

/**
 * Toggle External Dataset Import Form Visibility
 */
function toggleImportDatasetForm(e) {
    if (e && e.preventDefault) {
        e.preventDefault();
    }
    const formCard = document.getElementById("importDatasetFormContainer");
    if (formCard) {
        const isHidden = window.getComputedStyle(formCard).display === "none";
        if (isHidden) {
            formCard.style.display = "block";
            formCard.scrollIntoView({ behavior: 'smooth' });
            const firstInput = document.getElementById("dataset_file");
            if (firstInput) firstInput.focus();
        } else {
            formCard.style.display = "none";
        }
    }
}
