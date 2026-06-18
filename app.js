
// ========== PUB KVIZ MASTER - RENDER KLIJENT ==========
class PubKvizClient {
    constructor() {
        this.socket = null;
        this.teamName = null;
        this.playerName = null;
        this.currentQuestion = null;
        this.timerInterval = null;
        this.canBuzz = false;
        this.canAnswer = false;
        this.quizActive = false;
        this.teams = [];
        this.score = 0;
        this.correctCount = 0;
        this.questionStartTime = 0;
        this.disabledOptions = [];
        this.connected = false;
        
        this.joinPanel = document.getElementById('joinPanel');
        this.quizPanel = document.getElementById('quizPanel');
        this.resultsPanel = document.getElementById('resultsPanel');
        this.teamNameInput = document.getElementById('teamNameInput');
        this.playerNameInput = document.getElementById('playerNameInput');
        this.statusDiv = document.getElementById('status');
        this.quizTitle = document.getElementById('quizTitle');
        this.questionArea = document.getElementById('questionArea');
        this.leaderboardArea = document.getElementById('leaderboardArea');
        this.resultsArea = document.getElementById('resultsArea');
        
        this.init();
    }
    
    init() {
        document.getElementById('joinBtn').addEventListener('click', () => this.joinGame());
        document.getElementById('buzzBtn').addEventListener('click', () => this.buzz());
        
        document.getElementById('teamNameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinGame();
        });
        document.getElementById('playerNameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinGame();
        });
        
        this.autoConnect();
    }
    
    autoConnect() {
        const savedTeam = localStorage.getItem('pubKvizTeam');
        const savedPlayer = localStorage.getItem('pubKvizPlayer');
        if (savedTeam && savedPlayer) {
            this.teamNameInput.value = savedTeam;
            this.playerNameInput.value = savedPlayer;
            setTimeout(() => this.joinGame(), 1000);
        }
    }
    
    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.hostname;
        const port = window.location.port || '65432';
        return `${protocol}//${host}:${port}`;
    }
    
    joinGame() {
        const teamName = this.teamNameInput.value.trim();
        const playerName = this.playerNameInput.value.trim();
        
        if (!teamName || teamName.length < 2) {
            this.showStatus('Ime tima mora imati najmanje 2 karaktera', 'error');
            return;
        }
        
        if (!playerName || playerName.length < 2) {
            this.showStatus('Vaše ime mora imati najmanje 2 karaktera', 'error');
            return;
        }
        
        this.teamName = teamName;
        this.playerName = playerName;
        
        localStorage.setItem('pubKvizTeam', teamName);
        localStorage.setItem('pubKvizPlayer', playerName);
        
        this.showStatus('Povezivanje sa serverom...', 'info');
        
        if (this.socket) {
            this.socket.close();
        }
        
        try {
            const wsUrl = this.getWebSocketUrl();
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                this.connected = true;
                this.showStatus('✅ Povezani na server', 'success');
                this.socket.send(JSON.stringify({
                    type: 'client_login',
                    team_name: this.teamName,
                    player_name: this.playerName
                }));
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleMessage(message);
                } catch (e) {
                    console.error('Greška pri parsiranju poruke:', e);
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket greška:', error);
                this.showStatus('❌ Greška pri povezivanju', 'error');
            };
            
            this.socket.onclose = () => {
                this.connected = false;
                this.showStatus('🔌 Konekcija prekinuta', 'error');
            };
        } catch (e) {
            this.showStatus('❌ Greška: ' + e.message, 'error');
        }
    }
    
    handleMessage(message) {
        console.log('Primljena poruka:', message.type);
        
        switch(message.type) {
            case 'login_success':
                this.showStatus('✅ Uspešno prijavljeni!', 'success');
                this.joinPanel.style.display = 'none';
                this.quizPanel.style.display = 'block';
                this.quizTitle.textContent = '🎯 ' + (message.quiz_name || 'Pub Kviz');
                document.getElementById('yourTeamName').textContent = this.teamName;
                break;
                
            case 'welcome':
                this.showStatus('📡 Povezani na server', 'success');
                break;
                
            case 'question':
                this.showQuestion(message);
                break;
                
            case 'teams_update':
            case 'participants_update':
                this.updateTeams(message.teams || []);
                break;
                
            case 'state_update':
                this.updateState(message);
                break;
                
            case 'buzz':
                this.onBuzz(message.team_name);
                break;
                
            case 'answer_submitted':
                this.onAnswerSubmitted(message);
                break;
                
            case 'lifeline_used':
                if (message.lifeline === '50_50' && message.disabled_options) {
                    this.disabledOptions = message.disabled_options;
                }
                break;
                
            case 'results':
                this.showResults(message.results);
                break;
                
            case 'error':
                this.showStatus('❌ ' + message.message, 'error');
                break;
                
            case 'ping':
                this.socket.send(JSON.stringify({type: 'pong'}));
                break;
                
            default:
                console.log('Nepoznata poruka:', message);
        }
    }
    
    showQuestion(data) {
        this.currentQuestion = data;
        this.canBuzz = true;
        this.canAnswer = false;
        this.disabledOptions = data.disabled_options || [];
        this.questionStartTime = Date.now();
        
        const qArea = this.questionArea;
        const timeLeft = Math.ceil(data.time_left || data.time || 15);
        
        let html = `
            <div class="question-container">
                <div class="question-header">
                    <span class="question-number">Pitanje ${data.index + 1}/${data.total}</span>
                    <span class="timer" id="questionTimer">${timeLeft}s</span>
                </div>
                <div class="question-text">${this.escapeHtml(data.question)}</div>
                <div class="options-grid" id="optionsGrid">
        `;
        
        data.options.forEach((option, idx) => {
            const disabled = this.disabledOptions.includes(idx);
            const letter = String.fromCharCode(65 + idx);
            html += `
                <div class="option ${disabled ? 'disabled' : ''}" 
                     data-index="${idx}" 
                     onclick="client.answer(${idx})">
                    <span class="option-letter">${letter}</span>
                    <span class="option-text">${this.escapeHtml(option)}</span>
                </div>
            `;
        });
        
        html += `
                </div>
                <button id="buzzBtn" class="buzz-button" onclick="client.buzz()">
                    🔔 BUZZ!
                </button>
                <div id="buzzStatus" class="buzz-status"></div>
            </div>
        `;
        
        qArea.innerHTML = html;
        
        if (this.timerInterval) clearInterval(this.timerInterval);
        let remaining = timeLeft;
        this.timerInterval = setInterval(() => {
            remaining--;
            const timerEl = document.getElementById('questionTimer');
            if (timerEl) {
                timerEl.textContent = remaining + 's';
                if (remaining <= 5) timerEl.style.color = '#ff4444';
                else timerEl.style.color = '#ffd700';
            }
            if (remaining <= 0) {
                clearInterval(this.timerInterval);
                this.endQuestion();
            }
        }, 1000);
        
        this.resultsPanel.style.display = 'none';
        this.quizPanel.style.display = 'block';
        
        if (data.teams) {
            this.updateTeams(data.teams);
        }
    }
    
    answer(answerIndex) {
        if (!this.canAnswer) {
            this.showBuzzStatus('⏳ Sačekajte da buzz-ujete prvo!', 'info');
            return;
        }
        
        if (this.disabledOptions.includes(answerIndex)) {
            this.showBuzzStatus('❌ Ova opcija je isključena!', 'error');
            return;
        }
        
        const responseTime = (Date.now() - this.questionStartTime) / 1000;
        this.canAnswer = false;
        
        this.socket.send(JSON.stringify({
            type: 'answer',
            team_name: this.teamName,
            answer_index: answerIndex,
            response_time: responseTime
        }));
        
        document.querySelectorAll('.option').forEach(el => {
            el.style.opacity = '0.5';
            el.style.cursor = 'default';
        });
    }
    
    buzz() {
        if (!this.canBuzz) {
            this.showBuzzStatus('⏳ Sačekajte malo pre nego što ponovo buzz-ujete', 'info');
            return;
        }
        
        this.canBuzz = false;
        document.getElementById('buzzBtn').disabled = true;
        this.showBuzzStatus('⏳ Čekamo odgovor...', 'info');
        
        this.socket.send(JSON.stringify({
            type: 'buzz',
            team_name: this.teamName
        }));
    }
    
    onBuzz(teamName) {
        if (teamName === this.teamName) {
            this.canAnswer = true;
            this.showBuzzStatus('✅ Vi ste buzz-ovali! Odaberite odgovor.', 'success');
            document.getElementById('buzzBtn').style.display = 'none';
            document.querySelectorAll('.option:not(.disabled)').forEach(el => {
                el.style.opacity = '1';
                el.style.cursor = 'pointer';
            });
        } else {
            this.showBuzzStatus('🔔 ' + teamName + ' je buzz-ovao!', 'info');
            this.canBuzz = false;
        }
    }
    
    onAnswerSubmitted(data) {
        if (data.team_name === this.teamName) {
            if (data.is_correct) {
                this.showBuzzStatus('✅ TAČNO! +' + (data.points || 10) + ' poena!', 'success');
                this.score += data.points || 10;
                this.correctCount++;
                document.querySelectorAll('.option').forEach(el => {
                    if (el.dataset.index == data.answer_index) {
                        el.style.backgroundColor = '#00cc44';
                    }
                });
            } else {
                this.showBuzzStatus('❌ NETAČNO! -' + (data.points || 5) + ' poena!', 'error');
                this.score -= data.points || 5;
                document.querySelectorAll('.option').forEach(el => {
                    if (el.dataset.index == data.answer_index) {
                        el.style.backgroundColor = '#cc4444';
                    }
                });
            }
            document.getElementById('yourScore').textContent = this.score;
        }
        
        if (data.is_correct !== undefined && this.currentQuestion) {
            const correctIdx = this.currentQuestion.correct;
            document.querySelectorAll('.option').forEach(el => {
                if (el.dataset.index == correctIdx && data.team_name !== this.teamName) {
                    el.style.backgroundColor = '#00cc44';
                }
            });
        }
    }
    
    endQuestion() {
        if (this.timerInterval) clearInterval(this.timerInterval);
        this.canBuzz = false;
        this.canAnswer = false;
        
        const qArea = this.questionArea;
        qArea.innerHTML = `
            <div class="waiting-container">
                <div class="waiting-icon">⏳</div>
                <div class="waiting-text">Čekamo sledeće pitanje...</div>
            </div>
        `;
        
        setTimeout(() => {
            this.canBuzz = true;
        }, 2000);
    }
    
    updateTeams(teams) {
        this.teams = teams || [];
        const lbArea = document.getElementById('leaderboardList');
        if (!lbArea) return;
        
        let html = '';
        const sorted = [...this.teams].sort((a, b) => (b.score || 0) - (a.score || 0));
        
        sorted.slice(0, 8).forEach((team, idx) => {
            const isMe = team.name === this.teamName;
            const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : (idx + 1) + '.';
            html += `
                <div class="leaderboard-item ${isMe ? 'me' : ''}">
                    <span class="rank">${medal}</span>
                    <span class="team-name">${this.escapeHtml(team.name)}</span>
                    <span class="team-score">${team.score || 0}</span>
                </div>
            `;
        });
        
        if (sorted.length === 0) {
            html = '<div class="no-teams">Nema prijavljenih timova</div>';
        }
        
        lbArea.innerHTML = html;
        
        const myTeam = this.teams.find(t => t.name === this.teamName);
        if (myTeam) {
            this.score = myTeam.score || 0;
            const scoreEl = document.getElementById('yourScore');
            if (scoreEl) scoreEl.textContent = this.score;
        }
    }
    
    updateState(state) {
        if (state.quiz_active && state.current_question >= 0) {
            this.quizActive = true;
            if (state.question) {
                const data = {
                    index: state.current_question,
                    total: state.total_questions,
                    question: state.question.text,
                    options: state.question.options,
                    time: state.question.total_time,
                    time_left: state.question.time_left,
                    disabled_options: state.question.disabled_options || [],
                    teams: state.teams
                };
                this.showQuestion(data);
            }
        } else {
            this.quizActive = false;
            this.quizPanel.style.display = 'block';
            this.questionArea.innerHTML = `
                <div class="waiting-container">
                    <div class="waiting-icon">🎯</div>
                    <div class="waiting-text">Čekamo početak kviza...</div>
                </div>
            `;
        }
        
        if (state.teams) {
            this.updateTeams(state.teams);
        }
    }
    
    showResults(results) {
        this.quizPanel.style.display = 'none';
        this.resultsPanel.style.display = 'block';
        
        let html = `
            <h2>🏆 KONAČNI REZULTATI 🏆</h2>
            <div class="results-list">
        `;
        
        results.forEach((team, idx) => {
            const medal = idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : (idx + 1) + '.';
            const isMe = team.name === this.teamName;
            html += `
                <div class="result-item ${isMe ? 'me' : ''}">
                    <span class="result-rank">${medal}</span>
                    <span class="result-name">${this.escapeHtml(team.name)}</span>
                    <span class="result-score">${team.score} poena</span>
                    <span class="result-correct">✅ ${team.correct_count || 0}</span>
                </div>
            `;
        });
        
        html += '</div>';
        
        const myResult = results.find(r => r.name === this.teamName);
        if (myResult) {
            html += `
                <div class="my-result">
                    <h3>📍 VAŠ REZULTAT</h3>
                    <div class="my-result-details">
                        <span>Tim: ${this.escapeHtml(myResult.name)}</span>
                        <span>Poeni: ${myResult.score}</span>
                        <span>Tačni odgovori: ${myResult.correct_count || 0}</span>
                    </div>
                </div>
            `;
        }
        
        this.resultsArea.innerHTML = html;
        this.addConfetti();
    }
    
    addConfetti() {
        const colors = ['#ffd700', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#ff6b6b'];
        const container = this.resultsPanel;
        
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.top = '-10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.width = Math.random() * 8 + 4 + 'px';
            confetti.style.height = Math.random() * 8 + 4 + 'px';
            confetti.style.position = 'absolute';
            confetti.style.animation = 'confettiFall ' + (Math.random() * 3 + 2) + 's linear infinite';
            confetti.style.animationDelay = Math.random() * 2 + 's';
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
            container.appendChild(confetti);
        }
    }
    
    showBuzzStatus(message, type) {
        const el = document.getElementById('buzzStatus');
        if (el) {
            el.textContent = message;
            el.className = 'buzz-status ' + type;
            el.style.display = 'block';
        }
    }
    
    showStatus(message, type) {
        if (this.statusDiv) {
            this.statusDiv.textContent = message;
            this.statusDiv.className = 'status ' + type;
        }
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

let client = null;
document.addEventListener('DOMContentLoaded', () => {
    client = new PubKvizClient();
});
