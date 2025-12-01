// N-gram Prediction Game JavaScript

// Game state variables
var currentKural = null;
var userTimerStart = null;
var userTimerInterval = null;
var userTimeMs = 0;
var gameState = 'waiting'; // 'waiting', 'playing', 'submitted', 'results'

// Initialize game on page load
$(document).ready(function () {
    loadNewKural();
    loadLeaderboard();

    // Allow Enter key to submit answer
    $('#user-answer-input').on('keypress', function (e) {
        if (e.which === 13) { // Enter key
            submitUserAnswer();
        }
    });
});

/**
 * Load a new random kural with masked word
 */
function loadNewKural() {
    // Reset game state
    gameState = 'waiting';
    userTimeMs = 0;
    currentKural = null;
    $('#user-answer-input').val('');
    $('#user-answer-input').prop('disabled', false);
    $('#submit-answer-btn').show();
    $('#next-kural-btn').hide();
    $('#results-container').hide();
    $('#kural-vilakam-container').hide();
    $('#timer-display').text('0.0');

    // Clear any existing timer
    if (userTimerInterval) {
        clearInterval(userTimerInterval);
        userTimerInterval = null;
    }

    // Fetch new kural
    $.ajax({
        url: '/ngram/get_kural',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            currentKural = response;
            displayMaskedLine(response.masked_line);
            startUserTimer();
            gameState = 'playing';
        },
        error: function (xhr, status, error) {
            console.error('Error loading kural:', error);
            $('#masked-line-text').text('குறள் ஏற்றுவதில் பிழை ஏற்பட்டது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.');
        }
    });
}

/**
 * Display the masked kural line
 */
function displayMaskedLine(maskedLine) {
    // Format the line for better display (handle multiple words per line)
    var words = maskedLine.split(' ');
    var formattedLine = words.join(' ');
    $('#masked-line-text').text(formattedLine);
}

/**
 * Start the user timer
 */
function startUserTimer() {
    userTimerStart = Date.now();
    userTimerInterval = setInterval(function () {
        var elapsed = (Date.now() - userTimerStart) / 1000;
        $('#timer-display').text(elapsed.toFixed(1));
        userTimeMs = Date.now() - userTimerStart;
    }, 100); // Update every 100ms for smooth display
}

/**
 * Stop the user timer
 */
function stopUserTimer() {
    if (userTimerInterval) {
        clearInterval(userTimerInterval);
        userTimerInterval = null;
    }
    if (userTimerStart) {
        userTimeMs = Date.now() - userTimerStart;
    }
}

/**
 * Submit user answer and get machine prediction
 */
function submitUserAnswer() {
    if (gameState !== 'playing' || !currentKural) {
        return;
    }

    var userAnswer = $('#user-answer-input').val().trim();
    if (!userAnswer) {
        alert('தயவுசெய்து ஒரு விடையை உள்ளிடுக.');
        return;
    }

    // Stop user timer
    stopUserTimer();
    gameState = 'submitted';

    // Disable input and submit button
    $('#user-answer-input').prop('disabled', true);
    $('#submit-answer-btn').hide();

    // Get machine prediction
    getMachinePrediction(userAnswer);
}

/**
 * Get machine prediction using N-gram model
 */
function getMachinePrediction(userAnswer) {
    var machineStartTime = Date.now();

    $.ajax({
        url: '/ngram/predict',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            masked_line: currentKural.masked_line,
            masked_index: currentKural.masked_index
        }),
        dataType: 'json',
        success: function (response) {
            var machineTimeMs = response.machine_time_ms || (Date.now() - machineStartTime);
            displayResults(userAnswer, response.prediction, machineTimeMs);
        },
        error: function (xhr, status, error) {
            console.error('Error getting prediction:', error);
            // Still display results with empty prediction
            displayResults(userAnswer, '', 0);
        }
    });
}

/**
 * Display comparison results
 */
function displayResults(userAnswer, machinePrediction, machineTimeMs) {
    var correctWord = currentKural.correct_word;
    var userCorrect = (userAnswer === correctWord);
    var machineCorrect = (machinePrediction === correctWord);

    // Display user result
    var userResultText = userCorrect ?
        '✓ சரி!' :
        '✗ தவறு';
    var userResultColor = userCorrect ? 'green' : 'red';
    $('#user-result').html('<span style="color: ' + userResultColor + '; font-size: 20px;">' +
        userResultText + '</span><br>' + userAnswer);
    $('#user-time').text('நேரம்: ' + (userTimeMs / 1000).toFixed(2) + ' வினாடிகள்');

    // Display machine result
    var machineResultText = machineCorrect ?
        '✓ சரி!' :
        '✗ தவறு';
    var machineResultColor = machineCorrect ? 'green' : 'red';
    $('#machine-result').html('<span style="color: ' + machineResultColor + '; font-size: 20px;">' +
        machineResultText + '</span><br>' + (machinePrediction || '(கணிப்பு இல்லை)'));
    $('#machine-time').text('நேரம்: ' + (machineTimeMs / 1000).toFixed(2) + ' வினாடிகள்');

    // Display correct word
    $('#correct-word-display').text('சரியான விடை: ' + correctWord);

    // Show results
    $('#results-container').show();

    // Show kural explanation
    if (currentKural.porul) {
        displayKuralExplanation(currentKural.porul);
    }

    // Show next button
    $('#next-kural-btn').show();

    // Submit score to server
    submitScore(userAnswer, machinePrediction, machineTimeMs, userCorrect, machineCorrect);

    gameState = 'results';
}

/**
 * Display kural explanation
 */
function displayKuralExplanation(porul) {
    var explanationHtml = '';

    if (porul.Muuvey) {
        explanationHtml += '<p><span> மு.வ : </span>' + porul.Muuvey + '</p>';
    }

    if (porul.salaman) {
        explanationHtml += '<p><span> சாலமன் பாப்பையா : </span>' + porul.salaman + '</p>';
    }

    $('#kural-vilakam-content').html(explanationHtml);
    $('#kural-vilakam-container').show();
}

/**
 * Submit score to server
 */
function submitScore(userAnswer, machinePrediction, machineTimeMs, userCorrect, machineCorrect) {
    $.ajax({
        url: '/ngram/submit_score',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            kural_id: currentKural.kural_id,
            correct_word: currentKural.correct_word,
            user_answer: userAnswer,
            machine_prediction: machinePrediction,
            user_time_ms: userTimeMs,
            machine_time_ms: machineTimeMs,
            user_correct: userCorrect,
            machine_correct: machineCorrect
        }),
        dataType: 'json',
        success: function (response) {
            console.log('Score submitted successfully');
            // Optionally reload leaderboard
            loadLeaderboard();
        },
        error: function (xhr, status, error) {
            console.error('Error submitting score:', error);
        }
    });
}

/**
 * Load and display leaderboard
 */
function loadLeaderboard() {
    $.ajax({
        url: '/ngram/leaderboard',
        type: 'GET',
        dataType: 'json',
        success: function (response) {
            displayLeaderboard(response.leaderboard || []);
        },
        error: function (xhr, status, error) {
            console.error('Error loading leaderboard:', error);
            $('#leaderboard-table').html(
                '<tr><td colspan="4" style="text-align: center; padding: 20px;">Leaderboard ஏற்றுவதில் பிழை</td></tr>'
            );
        }
    });
}

/**
 * Display leaderboard data
 */
function displayLeaderboard(leaderboard) {
    var tableHtml = '<tr class="leaderboard-heading">' +
        '<th>Rank</th>' +
        '<th class="user-name">User Name</th>' +
        '<th class="diamond-points">Correct</th>' +
        '<th class="diamond-points">Avg Time</th>' +
        '</tr>';

    if (leaderboard.length === 0) {
        tableHtml += '<tr><td colspan="4" style="text-align: center; padding: 20px;">இன்னும் எவரும் விளையாடவில்லை</td></tr>';
    } else {
        leaderboard.forEach(function (entry) {
            var avgTimeSeconds = (entry.avg_time_ms / 1000).toFixed(2);
            tableHtml += '<tr>' +
                '<td class="rank">#' + entry.rank + '</td>' +
                '<td class="user-name">' + (entry.user_name || 'Anonymous') + '</td>' +
                '<td class="diamond-points">' + entry.total_correct + '</td>' +
                '<td class="diamond-points">' + avgTimeSeconds + 's</td>' +
                '</tr>';
        });
    }

    $('#leaderboard-table').html(tableHtml);
}

