// CareerPilot Frontend

const API_URL = 'http://localhost:8000';

let generatedData = null;

// File upload handlers
document.getElementById('jdFile').addEventListener('change', handleFileUpload);
document.getElementById('resumeFile').addEventListener('change', handleFileUpload);

function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const fileName = file.name;
    const fileId = e.target.id;
    const nameSpanId = fileId === 'jdFile' ? 'jdFileName' : 'resumeFile';
    const textareaId = fileId === 'jdFile' ? 'jobDescription' : 'resumeText';

    document.getElementById(nameSpanId).textContent = fileName;

    const reader = new FileReader();
    reader.onload = (event) => {
        document.getElementById(textareaId).value = event.target.result;
        document.getElementById(nameSpanId).textContent += ' ✓';
    };
    reader.readAsText(file);
}

// Form Submit
document.getElementById('jobForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    await generateContent();
});

async function generateContent() {
    const btn = document.getElementById('generateBtn');
    const inputSection = document.getElementById('inputSection');
    const loadingSection = document.getElementById('loadingSection');
    const resultsSection = document.getElementById('resultsSection');

    btn.disabled = true;
    btn.querySelector('.btn-text').textContent = 'Generating...';
    inputSection.classList.add('hidden');
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');

    const data = {
        job_title: document.getElementById('jobTitle').value,
        company: document.getElementById('company').value,
        job_description: document.getElementById('jobDescription').value,
        resume_text: document.getElementById('resumeText').value,
        notes: document.getElementById('notes').value
    };

    try {
        const response = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorText = await response.text().catch(() => '');
            let detail = '';
            try {
                const errorData = JSON.parse(errorText || '{}');
                detail = errorData.detail || errorData.message || '';
            } catch (_) {
                detail = errorText;
            }
            throw new Error(detail || `Server error: ${response.status}`);
        }

        generatedData = await response.json();

        if (generatedData.status !== 'success') {
            throw new Error(generatedData.message || 'Generation failed');
        }

        displayResults(generatedData.outputs);

        loadingSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');

    } catch (error) {
        alert(error?.message || 'Error generating content. Please try again.');
        inputSection.classList.remove('hidden');
    } finally {
        btn.disabled = false;
        btn.querySelector('.btn-text').textContent = 'Generate Application Materials';
    }
}

function safeJsonParse(value) {
    if (value == null) return value;
    if (typeof value !== 'string') return value;
    let trimmed = value.trim();
    // Handle fenced code blocks like ```json ... ```
    if (trimmed.startsWith('```')) {
        const lines = trimmed.split('\n');
        if (lines.length >= 3 && lines[0].startsWith('```') && lines[lines.length - 1].trim() === '```') {
            trimmed = lines.slice(1, -1).join('\n').trim();
        }
        if (trimmed.toLowerCase().startsWith('json')) {
            const idx = trimmed.indexOf('\n');
            if (idx !== -1) trimmed = trimmed.slice(idx + 1).trim();
        }
    }
    if (!(trimmed.startsWith('{') || trimmed.startsWith('['))) return value;
    try { return JSON.parse(trimmed); } catch (_) { return value; }
}

function displayResults(outputs) {
    // Resume
    document.getElementById('resumeOutput').textContent = outputs.tailored_resume;

    // Cover Letter
    document.getElementById('coverOutput').textContent = outputs.cover_letter;

    // Interview Prep
    const interview = safeJsonParse(outputs.interview_prep) || {};
    const tips = interview.prep_tips || interview.tips || [];
    const commonQuestions = (interview.common_questions || [])
        .map(q => (typeof q === 'string' ? q : q?.question))
        .filter(Boolean);
    const behavioral = (interview.behavioral_questions || [])
        .map(q => q?.question)
        .filter(Boolean);
    const technical = (interview.technical_questions || [])
        .map(q => q?.question)
        .filter(Boolean);
    const questionsToAsk = interview.questions_to_ask_interviewer || interview.questions_to_ask || [];
    document.getElementById('interviewOutput').innerHTML = `
        <h4>Tips</h4>
        <ul>${tips.map(t => `<li>${t}</li>`).join('')}</ul>
        <h4>Questions</h4>
        <ul>${[...commonQuestions, ...behavioral, ...technical].map(q => `<li>${q}</li>`).join('')}</ul>
        <h4>Questions to Ask</h4>
        <ul>${questionsToAsk.map(q => `<li>${q}</li>`).join('')}</ul>
    `;

    // Review
    const review = safeJsonParse(outputs.review_feedback) || {};
    const overall = review.overall_assessment || review.overall_quality || '';
    const suggestions = review.top_priority_fixes || review.suggestions || [];
    document.getElementById('reviewOutput').innerHTML = `
        <h4>Overall</h4>
        <ul><li>${overall}</li></ul>
        <h4>Suggestions</h4>
        <ul>${suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
    `;
}

// Tab Navigation
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`${tab.dataset.tab}Tab`).classList.add('active');
    });
});

// Copy buttons (event delegation)
document.addEventListener('click', (e) => {
    if (e.target.matches('.copy-btn[data-copy]')) {
        const targetId = e.target.dataset.copy;
        const text = document.getElementById(targetId).textContent;
        navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!');
    }
    if (e.target.matches('.copy-btn') && !e.target.dataset.copy) {
        const el = document.getElementById('interviewOutput');
        navigator.clipboard.writeText(el.textContent);
        showToast('Copied to clipboard!');
    }
});

function copyInterview() {
    const el = document.getElementById('interviewOutput');
    navigator.clipboard.writeText(el.textContent);
    showToast('Copied to clipboard!');
}

// Individual PDF download
async function downloadSinglePDF(type) {
    if (!generatedData) return;

    const jobTitle = document.getElementById('jobTitle').value || 'Resume';
    const company = document.getElementById('company').value || '';
    const resumeText = document.getElementById('resumeText').value || '';
    const candidateName = resumeText.split('\n')[0].trim() || 'Candidate';

    const sectionMap = {
        'resume': { key: 'tailored_resume', title: `${candidateName}_${jobTitle}` },
        'cover': { key: 'cover_letter', title: 'Cover_Letter' },
        'interview': { key: 'interview_prep', title: 'Interview_Prep' },
        'review': { key: 'review_feedback', title: 'Review_Feedback' }
    };

    const config = sectionMap[type];
    let content = generatedData.outputs[config.key];

    // Format content for interview/review
    if (type === 'interview') {
        content = formatInterview(content);
    } else if (type === 'review') {
        content = formatReview(content);
    }

    try {
        const response = await fetch(`${API_URL}/generate-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sections: { [config.title]: content } })
        });

        if (!response.ok) throw new Error('PDF generation failed');

        const result = await response.json();

        if (result.status === 'success' && result.pdf) {
            const binaryString = atob(result.pdf);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            const blob = new Blob([bytes], { type: 'application/pdf' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${config.title}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
        }
    } catch (error) {
        // Fallback to text file
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${config.title}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

function formatInterview(data) {
    const interview = safeJsonParse(data) || {};
    const tips = interview.prep_tips || interview.tips || [];
    const commonQuestions = (interview.common_questions || [])
        .map(q => (typeof q === 'string' ? q : q?.question))
        .filter(Boolean);
    const behavioral = (interview.behavioral_questions || []).map(q => q?.question).filter(Boolean);
    const technical = (interview.technical_questions || []).map(q => q?.question).filter(Boolean);
    const questionsToAsk = interview.questions_to_ask_interviewer || interview.questions_to_ask || [];
    const questions = [...commonQuestions, ...behavioral, ...technical];
    return `INTERVIEW PREPARATION\n${'─'.repeat(50)}\n\nTips:\n${tips.map(t => '  • ' + t).join('\n')}\n\nQuestions:\n${questions.map(q => '  • ' + q).join('\n')}\n\nQuestions to Ask:\n${questionsToAsk.map(q => '  • ' + q).join('\n')}`;
}

function formatReview(data) {
    const review = safeJsonParse(data) || {};
    const overall = review.overall_assessment || review.overall_quality || '';
    const suggestions = review.top_priority_fixes || review.suggestions || [];
    return `REVIEW FEEDBACK\n${'─'.repeat(50)}\n\nOverall: ${overall}\n\nSuggestions:\n${suggestions.map(s => '  • ' + s).join('\n')}`;
}

// Email Modal
document.getElementById('sendEmailBtn').addEventListener('click', () => {
    document.getElementById('emailModal').classList.remove('hidden');
});

document.getElementById('cancelEmailBtn').addEventListener('click', () => {
    document.getElementById('emailModal').classList.add('hidden');
});

document.getElementById('emailForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!generatedData) return;

    const email = document.getElementById('emailAddress').value;
    const statusEl = document.getElementById('emailStatus');

    statusEl.classList.remove('hidden', 'success', 'error');
    statusEl.textContent = 'Sending...';

    const body = `
CareerPilot Application Materials
===================================

Job: ${document.getElementById('jobTitle').value} at ${document.getElementById('company').value}

---
TAILORED RESUME:
${generatedData.outputs.tailored_resume}

---
COVER LETTER:
${generatedData.outputs.cover_letter}

---
INTERVIEW PREP:
${formatInterview(generatedData.outputs.interview_prep)}
    `.trim();

    try {
        const response = await fetch(`${API_URL}/send-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                subject: `CareerPilot Materials for ${document.getElementById('jobTitle').value} at ${document.getElementById('company').value}`,
                body,
                attachments: []
            })
        });

        const result = await response.json();

        if (result.status === 'success') {
            statusEl.classList.add('success');
            statusEl.textContent = result.message;
            setTimeout(() => {
                document.getElementById('emailModal').classList.add('hidden');
                statusEl.classList.add('hidden');
            }, 2000);
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        statusEl.classList.add('error');
        statusEl.textContent = error.message || 'Failed to send email. Check SMTP settings in .env';
    }
});

// Toast notification
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}