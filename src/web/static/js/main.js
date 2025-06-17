/**
 * Main JavaScript for Steem Curator Analyzer
 */

// Config object to store application settings
const config = {
    darkMode: false,
    enableCaching: true,
    connectionTimeout: 30,
    nodesSelection: 'auto'
};

// DOM Ready Handler
$(document).ready(function() {
    // Initialize components
    initializeUI();
    setupEventListeners();
    loadUserPreferences();
});

/**
 * Initialize UI components
 */
function initializeUI() {
    console.log("Initializing UI components...");
    
    // Setup tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Check for existing results in session storage if caching is enabled
    if (config.enableCaching && sessionStorage.getItem('lastResults')) {
        try {
            const lastResults = JSON.parse(sessionStorage.getItem('lastResults'));
            const username = sessionStorage.getItem('lastUsername');
            const daysBack = sessionStorage.getItem('lastDaysBack');
            
            // Restore last search parameters
            $('#username').val(username);
            $('#days_back').val(daysBack);
            
            // Display last results
            displayResults(lastResults);
        } catch (e) {
            console.error("Error restoring cached results:", e);
            sessionStorage.removeItem('lastResults');
        }
    }
}

/**
 * Setup all event listeners
 */
function setupEventListeners() {
    // Analyze form submission
    $('#analyzeForm').on('submit', function(e) {
        e.preventDefault();
        performAnalysis();
    });
    
    // Export button
    $('#exportBtn').on('click', function() {
        exportToCsv();
    });
    
    // Settings form submission
    $('#settingsForm').on('submit', function(e) {
        e.preventDefault();
        saveSettings();
    });
    
    // Dark mode toggle
    $('#dark_mode').on('change', function() {
        toggleDarkMode($(this).is(':checked'));
    });
}

/**
 * Load user preferences from localStorage
 */
function loadUserPreferences() {
    try {
        const savedConfig = localStorage.getItem('curatorAnalyzerConfig');
        
        if (savedConfig) {
            const parsedConfig = JSON.parse(savedConfig);
            Object.assign(config, parsedConfig);
            
            // Apply loaded preferences to UI
            $('#dark_mode').prop('checked', config.darkMode);
            $('#enable_caching').prop('checked', config.enableCaching);
            $('#connection_timeout').val(config.connectionTimeout);
            $('#nodes_selection').val(config.nodesSelection);
            
            // Apply dark mode if enabled
            if (config.darkMode) {
                toggleDarkMode(true);
            }
        }
    } catch (e) {
        console.error("Error loading user preferences:", e);
    }
}

/**
 * Save settings to localStorage
 */
function saveSettings() {
    // Update config object
    config.darkMode = $('#dark_mode').is(':checked');
    config.enableCaching = $('#enable_caching').is(':checked');
    config.connectionTimeout = parseInt($('#connection_timeout').val()) || 30;
    config.nodesSelection = $('#nodes_selection').val();
    
    // Save to localStorage
    localStorage.setItem('curatorAnalyzerConfig', JSON.stringify(config));
    
    // Show confirmation message
    showAlert('Impostazioni salvate con successo', 'success');
}

/**
 * Toggle dark mode
 */
function toggleDarkMode(enable) {
    if (enable) {
        $('body').addClass('dark-mode');
    } else {
        $('body').removeClass('dark-mode');
    }
    config.darkMode = enable;
}

/**
 * Perform curator analysis
 */
function performAnalysis() {
    const username = $('#username').val().trim();
    const daysBack = parseInt($('#days_back').val());
    
    // Show loading indicator
    $('#loading').show();
    $('#resultsSection').hide();
    $('#alertContainer').empty();
    
    // Make AJAX request to analyze endpoint
    $.ajax({
        url: '/analyze',
        method: 'POST',
        data: {
            username: username,
            days_back: daysBack
        },
        success: function(response) {
            $('#loading').hide();
            
            if (response.error) {
                showAlert(response.error, 'danger');
            } else {
                // Save results to session storage if caching is enabled
                if (config.enableCaching) {
                    sessionStorage.setItem('lastResults', JSON.stringify(response));
                    sessionStorage.setItem('lastUsername', username);
                    sessionStorage.setItem('lastDaysBack', daysBack);
                }
                
                displayResults(response);
            }
        },
        error: function(xhr) {
            $('#loading').hide();
            let message = 'Errore durante l\'analisi';
            
            try {
                const response = JSON.parse(xhr.responseText);
                if (response.error) {
                    message = response.error;
                }
            } catch (e) {}
            
            showAlert(message, 'danger');
        }
    });
}

/**
 * Display analysis results in the UI
 */
function displayResults(data) {
    // Make sure we have data to display
    if (!data || !data.curator_data || data.curator_data.length === 0) {
        showAlert('Nessun dato trovato per questo curator', 'warning');
        return;
    }
    
    // Display statistics cards
    displayStatistics(data.statistics);
    
    // Populate data table
    populateDataTable(data.curator_data);
    
    // Show results section
    $('#resultsSection').show();
}

/**
 * Display statistics cards
 */
function displayStatistics(stats) {
    if (!stats) return;
    
    const cardsContainer = $('#statisticsCards');
    cardsContainer.empty();
    
    // Add total votes card
    cardsContainer.append(`
        <div class="col-md-3 mb-3">
            <div class="stats-card">
                <h6 class="text-uppercase mb-1"><i class="fas fa-check-circle me-2"></i>Voti totali</h6>
                <h2>${stats.total_votes}</h2>
                <p class="small mb-0">Negli ultimi ${stats.days_back} giorni</p>
            </div>
        </div>
    `);
    
    // Add total rewards card
    cardsContainer.append(`
        <div class="col-md-3 mb-3">
            <div class="stats-card">
                <h6 class="text-uppercase mb-1"><i class="fas fa-gem me-2"></i>Rewards totali</h6>
                <h2>${stats.total_rewards_sp.toFixed(2)} SP</h2>
                <p class="small mb-0">~${stats.total_rewards_sbd.toFixed(2)} SBD</p>
            </div>
        </div>
    `);
    
    // Add average efficiency card
    cardsContainer.append(`
        <div class="col-md-3 mb-3">
            <div class="stats-card">
                <h6 class="text-uppercase mb-1"><i class="fas fa-bolt me-2"></i>Efficienza media</h6>
                <h2>${stats.avg_efficiency.toFixed(2)}%</h2>
                <p class="small mb-0">Max: ${stats.max_efficiency.toFixed(2)}%</p>
            </div>
        </div>
    `);
    
    // Add timing card
    cardsContainer.append(`
        <div class="col-md-3 mb-3">
            <div class="stats-card">
                <h6 class="text-uppercase mb-1"><i class="fas fa-clock me-2"></i>Timing medio</h6>
                <h2>${stats.avg_vote_time.toFixed(1)} min</h2>
                <p class="small mb-0">Dopo pubblicazione post</p>
            </div>
        </div>
    `);
}

/**
 * Populate data table with curator data
 */
function populateDataTable(data) {
    const tableBody = $('#dataTableBody');
    tableBody.empty();
    
    data.forEach(function(item) {
        const row = $('<tr></tr>');
        
        // Format timestamp
        const timestamp = new Date(item.timestamp).toLocaleString();
        
        // Format efficiency class
        let efficiencyClass = 'efficiency-medium';
        if (item.efficiency >= 80) {
            efficiencyClass = 'efficiency-high';
        } else if (item.efficiency < 50) {
            efficiencyClass = 'efficiency-low';
        }
        
        // Add cells
        row.append(`<td class="timestamp-cell">${timestamp}</td>`);
        row.append(`<td>${item.curator}</td>`);
        row.append(`<td>${item.comment_author}</td>`);
        row.append(`<td class="permlink-cell" title="${item.comment_permlink}">
            <a href="https://steemit.com/@${item.comment_author}/${item.comment_permlink}" 
               target="_blank" rel="noopener noreferrer">
                ${item.comment_permlink}
            </a>
        </td>`);
        row.append(`<td>${item.reward_sp.toFixed(4)}</td>`);
        row.append(`<td>${(item.vote_info.weight / 100).toFixed(2)}</td>`);
        row.append(`<td>${item.vote_value_steem.toFixed(4)}</td>`);
        row.append(`<td>${item.voted_after_minutes.toFixed(1)}</td>`);
        row.append(`<td class="${efficiencyClass}">${item.efficiency.toFixed(2)}%</td>`);
        
        tableBody.append(row);
    });
}

/**
 * Export data to CSV file
 */
function exportToCsv() {
    // Get data from session storage if available
    let data = null;
    
    if (sessionStorage.getItem('lastResults')) {
        try {
            const lastResults = JSON.parse(sessionStorage.getItem('lastResults'));
            data = lastResults.curator_data;
        } catch (e) {
            console.error("Error retrieving data for export:", e);
        }
    }
    
    if (!data || data.length === 0) {
        showAlert('Nessun dato disponibile per l\'esportazione', 'warning');
        return;
    }
    
    // Create CSV header
    const header = [
        'Timestamp', 
        'Curator', 
        'Autore', 
        'Permlink', 
        'Reward SP', 
        'Peso Voto', 
        'Valore Voto', 
        'Minuti Post', 
        'Efficienza'
    ].join(',');
    
    // Create CSV rows
    const rows = data.map(item => [
        `"${item.timestamp}"`,
        `"${item.curator}"`,
        `"${item.comment_author}"`,
        `"${item.comment_permlink}"`,
        item.reward_sp,
        item.vote_info.weight / 100,
        item.vote_value_steem,
        item.voted_after_minutes,
        item.efficiency
    ].join(','));
    
    // Combine header and rows
    const csv = [header, ...rows].join('\n');
    
    // Create download link
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    // Create download element
    const link = document.createElement('a');
    const date = new Date().toISOString().split('T')[0];
    link.href = url;
    link.download = `curator_${$('#username').val()}_${date}.csv`;
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Display an alert message to the user
 */
function showAlert(message, type) {
    const alertContainer = $('#alertContainer');
    alertContainer.empty();
    
    const alert = $(`
        <div class="alert alert-${type} alert-dismissible fade show alert-custom mt-3" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);
    
    alertContainer.append(alert);
    
    // Auto dismiss after 5 seconds
    setTimeout(function() {
        alert.alert('close');
    }, 5000);
}
