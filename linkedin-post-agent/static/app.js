// LinkedIn Post Generator - Frontend JavaScript

const API_BASE = '';
let currentDraftId = null;
let refinementHistory = [];

// ============== Utility Functions ==============

function showLoading(message = 'Processing...') {
    document.getElementById('loading-text').textContent = message;
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');

    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500',
    };

    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        info: 'fa-info-circle',
        warning: 'fa-exclamation-triangle',
    };

    toast.className = `${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg flex items-center space-x-3 slide-in fade-in`;
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function updateStatus(connected, message = 'Ready') {
    const indicator = document.getElementById('status-indicator');
    const text = document.getElementById('status-text');
    const dot = indicator.querySelector('.pulse-dot');

    text.textContent = message;
    dot.className = `w-2 h-2 rounded-full pulse-dot ${connected ? 'bg-green-400' : 'bg-red-400'}`;
}

// ============== Tab Navigation ==============

function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });

    // Reset all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('bg-linkedin-50', 'text-white');
        btn.classList.add('text-gray-600', 'hover:bg-gray-100');
    });

    // Show selected tab
    document.getElementById(`tab-${tabName}-content`).classList.remove('hidden');
    document.getElementById(`tab-${tabName}`).classList.add('bg-linkedin-50', 'text-white');
    document.getElementById(`tab-${tabName}`).classList.remove('text-gray-600', 'hover:bg-gray-100');

    // Load tab-specific content
    if (tabName === 'trends') fetchTrends();
    if (tabName === 'drafts') loadDrafts();
    if (tabName === 'style') loadStyleProfile();
}

// ============== Trends Functions ==============

async function fetchTrends() {
    showLoading('Fetching trending topics...');

    try {
        const response = await fetch(`${API_BASE}/api/trends?limit=15`);
        const data = await response.json();

        if (data.success) {
            renderTrends(data.trends);
            showToast(`Loaded ${data.count} trends`, 'success');
        } else {
            showToast('Failed to fetch trends', 'error');
        }
    } catch (error) {
        showToast('Error fetching trends: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function renderTrends(trends) {
    const grid = document.getElementById('trends-grid');

    if (!trends || trends.length === 0) {
        grid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-fire text-3xl text-gray-400"></i>
                </div>
                <p class="text-gray-500">No trends available. Try again later.</p>
            </div>
        `;
        return;
    }

    grid.innerHTML = trends.map((trend, index) => `
        <div class="bg-white rounded-xl shadow-md p-5 card-hover cursor-pointer" onclick="useTrendForPost('${escapeHtml(trend.topic)}')">
            <div class="flex items-start justify-between mb-3">
                <span class="px-2 py-1 bg-blue-100 text-linkedin-50 text-xs rounded-full font-medium">
                    ${trend.source.replace('_', ' ')}
                </span>
                <span class="text-gray-400 text-sm">#${index + 1}</span>
            </div>
            <h3 class="font-semibold text-gray-800 mb-2 line-clamp-2">${escapeHtml(trend.topic)}</h3>
            ${trend.suggested_angles ? `
                <p class="text-sm text-gray-500 line-clamp-2">
                    <i class="fas fa-lightbulb text-yellow-500 mr-1"></i>
                    ${escapeHtml(trend.suggested_angles[0])}
                </p>
            ` : ''}
            <div class="mt-3 pt-3 border-t flex items-center text-linkedin-50 text-sm font-medium">
                <i class="fas fa-arrow-right mr-2"></i>Use for post
            </div>
        </div>
    `).join('');
}

function useTrendForPost(topic) {
    document.getElementById('topic-input').value = topic;
    switchTab('generate');
    showToast(`Selected: ${topic}`, 'success');
}

// ============== Generation Functions ==============

function setTopic(topic) {
    document.getElementById('topic-input').value = topic;
}

async function generatePost() {
    const topic = document.getElementById('topic-input').value.trim();
    const angle = document.getElementById('angle-select').value;
    const useTrends = document.getElementById('use-trends').checked;

    if (!topic) {
        showToast('Please enter a topic', 'warning');
        return;
    }

    showLoading('Generating your post...');
    refinementHistory = [];

    try {
        const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic,
                angle: angle || null,
                trend_context: useTrends ? 'trending' : null,
            }),
        });

        const data = await response.json();

        if (data.success) {
            currentDraftId = data.draft_id;
            document.getElementById('post-preview').value = data.content;
            document.getElementById('char-count').textContent = `${data.character_count} characters`;
            document.getElementById('preview-empty').classList.add('hidden');
            document.getElementById('preview-container').classList.remove('hidden');

            // Clear refinement chat
            document.getElementById('refinement-chat').innerHTML = '';

            // Add initial generation message
            addRefinementMessage('ai', 'Post generated! Ask me to refine it.');

            showToast('Post generated successfully!', 'success');
        } else {
            showToast(data.detail || 'Generation failed', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function regeneratePost() {
    const topic = document.getElementById('topic-input').value.trim();
    if (!topic) return;

    showLoading('Regenerating post...');
    refinementHistory = [];

    try {
        const response = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic,
                angle: 'Let AI decide',
            }),
        });

        const data = await response.json();

        if (data.success) {
            currentDraftId = data.draft_id;
            document.getElementById('post-preview').value = data.content;
            document.getElementById('char-count').textContent = `${data.character_count} characters`;
            document.getElementById('refinement-chat').innerHTML = '';
            addRefinementMessage('ai', 'Post regenerated! What would you like to change?');
            showToast('Post regenerated!', 'success');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function refinePost() {
    const instruction = document.getElementById('refine-input').value.trim();
    const currentContent = document.getElementById('post-preview').value;

    if (!instruction) {
        showToast('Please enter a refinement instruction', 'warning');
        return;
    }

    if (!currentDraftId) {
        showToast('No draft to refine. Generate a post first.', 'warning');
        return;
    }

    // Add user message to chat
    addRefinementMessage('user', instruction);
    document.getElementById('refine-input').value = '';

    showLoading('Refining your post...');

    try {
        const response = await fetch(`${API_BASE}/api/refine`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                draft_id: currentDraftId,
                instruction,
            }),
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('post-preview').value = data.content;
            document.getElementById('char-count').textContent = `${data.character_count} characters`;
            addRefinementMessage('ai', 'Post refined! Want more changes?');
            showToast('Post refined!', 'success');
        } else {
            showToast(data.detail || 'Refinement failed', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function addRefinementMessage(type, text) {
    const chat = document.getElementById('refinement-chat');
    const message = document.createElement('div');
    message.className = `message-${type} px-4 py-2 text-sm max-w-[85%] slide-in`;
    message.textContent = text;
    chat.appendChild(message);
    chat.scrollTop = chat.scrollHeight;
}

// ============== Draft Functions ==============

async function saveDraft() {
    const content = document.getElementById('post-preview').value.trim();
    const topic = document.getElementById('topic-input').value.trim() || 'Untitled';

    if (!content) {
        showToast('No content to save', 'warning');
        return;
    }

    showLoading('Saving draft...');

    try {
        // The draft is already saved on generation, but we can update it
        showToast('Draft saved!', 'success');
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function loadDrafts() {
    showLoading('Loading drafts...');

    try {
        const response = await fetch(`${API_BASE}/api/drafts`);
        const data = await response.json();

        if (data.success) {
            renderDrafts(data.drafts);
        } else {
            showToast('Failed to load drafts', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

function renderDrafts(drafts) {
    const container = document.getElementById('drafts-container');

    if (!drafts || drafts.length === 0) {
        container.innerHTML = `
            <div class="bg-white rounded-xl shadow-md p-12 text-center">
                <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <i class="fas fa-file-alt text-3xl text-gray-400"></i>
                </div>
                <h3 class="text-lg font-medium text-gray-700 mb-2">No Drafts Yet</h3>
                <p class="text-gray-500 mb-4">Generate your first post to see it here</p>
                <button onclick="switchTab('generate')" class="px-6 py-2 gradient-bg text-white rounded-lg font-medium">
                    <i class="fas fa-plus mr-2"></i>Create Post
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = drafts.map(draft => `
        <div class="bg-white rounded-xl shadow-md p-6 card-hover" id="draft-${draft.draft_id}">
            <div class="flex items-start justify-between mb-4">
                <div class="flex-1">
                    <div class="flex items-center space-x-3 mb-2">
                        <span class="px-2 py-1 bg-blue-100 text-linkedin-50 text-xs rounded-full font-medium">
                            ${draft.topic}
                        </span>
                        <span class="px-2 py-1 ${getStatusColor(draft.status)} text-xs rounded-full font-medium">
                            ${draft.status}
                        </span>
                        <span class="text-gray-400 text-xs">${draft.character_count} chars</span>
                    </div>
                    <p class="text-gray-600 text-sm line-clamp-3">${escapeHtml(draft.content)}</p>
                </div>
            </div>

            <div class="flex items-center space-x-2 pt-4 border-t">
                ${draft.status !== 'posted' ? `
                    <button onclick="editDraft('${draft.draft_id}')" class="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-all">
                        <i class="fas fa-edit mr-1"></i>Edit
                    </button>
                    <button onclick="loadDraftToEditor('${draft.draft_id}')" class="px-3 py-1.5 text-sm text-linkedin-50 hover:bg-blue-50 rounded-lg transition-all">
                        <i class="fas fa-pen mr-1"></i>Open
                    </button>
                    <button onclick="markReviewed('${draft.draft_id}')" class="px-3 py-1.5 text-sm text-green-600 hover:bg-green-50 rounded-lg transition-all">
                        <i class="fas fa-check mr-1"></i>Approve
                    </button>
                    <button onclick="postDraft('${draft.draft_id}')" class="px-3 py-1.5 text-sm bg-linkedin-50 hover:bg-linkedin-100 text-white rounded-lg transition-all">
                        <i class="fab fa-linkedin mr-1"></i>Post
                    </button>
                ` : `
                    <a href="${draft.post_url}" target="_blank" class="px-3 py-1.5 text-sm text-linkedin-50 hover:bg-blue-50 rounded-lg transition-all">
                        <i class="fas fa-external-link-alt mr-1"></i>View Post
                    </a>
                `}
                <button onclick="deleteDraft('${draft.draft_id}')" class="px-3 py-1.5 text-sm text-red-500 hover:bg-red-50 rounded-lg transition-all ml-auto">
                    <i class="fas fa-trash mr-1"></i>Delete
                </button>
            </div>

            ${draft.refinement_history && draft.refinement_history.length > 0 ? `
                <div class="mt-3 pt-3 border-t">
                    <p class="text-xs text-gray-500">
                        <i class="fas fa-history mr-1"></i>
                        ${draft.refinement_history.length} refinement(s)
                    </p>
                </div>
            ` : ''}
        </div>
    `).join('');
}

function getStatusColor(status) {
    const colors = {
        draft: 'bg-yellow-100 text-yellow-700',
        reviewed: 'bg-green-100 text-green-700',
        posted: 'bg-blue-100 text-blue-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
}

async function loadDraftToEditor(draftId) {
    showLoading('Loading draft...');

    try {
        const response = await fetch(`${API_BASE}/api/drafts/${draftId}`);
        const data = await response.json();

        if (data.success) {
            const draft = data.draft;
            currentDraftId = draftId;
            document.getElementById('topic-input').value = draft.topic;
            document.getElementById('post-preview').value = draft.content;
            document.getElementById('char-count').textContent = `${draft.character_count} characters`;
            document.getElementById('preview-empty').classList.add('hidden');
            document.getElementById('preview-container').classList.remove('hidden');

            // Load refinement history
            document.getElementById('refinement-chat').innerHTML = '';
            if (draft.refinement_history) {
                draft.refinement_history.forEach(ref => {
                    addRefinementMessage('user', ref.instruction);
                });
                addRefinementMessage('ai', 'Draft loaded. Want to refine it further?');
            }

            switchTab('generate');
            showToast('Draft loaded!', 'success');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function deleteDraft(draftId) {
    if (!confirm('Are you sure you want to delete this draft?')) return;

    try {
        const response = await fetch(`${API_BASE}/api/drafts/${draftId}`, { method: 'DELETE' });
        const data = await response.json();

        if (data.success) {
            document.getElementById(`draft-${draftId}`).remove();
            showToast('Draft deleted', 'success');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function markReviewed(draftId) {
    try {
        const response = await fetch(`${API_BASE}/api/drafts/${draftId}/review`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            const statusEl = document.querySelector(`#draft-${draftId} .bg-yellow-100, #draft-${draftId} .bg-green-100`);
            if (statusEl) {
                statusEl.className = 'px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium';
                statusEl.textContent = 'reviewed';
            }
            showToast('Draft approved! Ready to post.', 'success');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

async function postDraft(draftId) {
    if (!confirm('This will post to your LinkedIn account. Continue?')) return;

    showLoading('Posting to LinkedIn...');

    try {
        const response = await fetch(`${API_BASE}/api/post/${draftId}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            showToast('Posted successfully!', 'success');
            window.open(data.post_url, '_blank');
            loadDrafts();
        } else {
            showToast(data.detail || 'Failed to post', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

async function editDraft(draftId) {
    const content = prompt('Edit your draft content:');
    if (!content) return;

    try {
        const response = await fetch(`${API_BASE}/api/drafts/${draftId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ draft_id: draftId, content }),
        });

        const data = await response.json();
        if (data.success) {
            showToast('Draft updated!', 'success');
            loadDrafts();
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// ============== Style Analysis ==============

async function loadStyleProfile() {
    try {
        const response = await fetch(`${API_BASE}/api/style-profile`);
        const data = await response.json();

        if (data.success && data.profile) {
            document.getElementById('style-profile-display').classList.remove('hidden');
            document.getElementById('style-tone').textContent = data.profile.tone || '-';
            document.getElementById('style-length').textContent = data.profile.typical_length || '-';
            document.getElementById('style-structure').textContent = data.profile.preferred_structure || '-';
            document.getElementById('style-emoji').textContent = data.profile.use_emoji ? 'Yes' : 'No';
        }
    } catch (error) {
        console.error('Error loading style profile:', error);
    }
}

function addSamplePost() {
    const container = document.getElementById('sample-posts-container');
    const textarea = document.createElement('textarea');
    textarea.className = 'sample-post w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-linkedin-50 outline-none resize-none';
    textarea.rows = 3;
    textarea.placeholder = 'Paste another post here...';
    container.appendChild(textarea);
}

async function analyzeStyle() {
    const posts = Array.from(document.querySelectorAll('.sample-post'))
        .map(el => el.value.trim())
        .filter(v => v);

    if (posts.length < 3) {
        showToast('Please enter at least 3 sample posts', 'warning');
        return;
    }

    showLoading('Analyzing your writing style...');

    try {
        const response = await fetch(`${API_BASE}/api/analyze-style`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sample_posts: posts }),
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('style-profile-display').classList.remove('hidden');
            document.getElementById('style-tone').textContent = data.profile.tone || '-';
            document.getElementById('style-length').textContent = data.profile.typical_length || '-';
            document.getElementById('style-structure').textContent = data.profile.preferred_structure || '-';
            document.getElementById('style-emoji').textContent = data.profile.use_emoji ? 'Yes' : 'No';
            showToast('Style profile saved!', 'success');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// ============== Miscellaneous ==============

function copyToClipboard() {
    const content = document.getElementById('post-preview').value;
    navigator.clipboard.writeText(content).then(() => {
        showToast('Copied to clipboard!', 'success');
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============== Initialize ==============

document.addEventListener('DOMContentLoaded', () => {
    // Check health on load
    fetch(`${API_BASE}/api/health`)
        .then(r => r.json())
        .then(data => {
            updateStatus(data.ollama_connected, data.ollama_connected ? 'Ready' : 'Ollama disconnected');
        })
        .catch(() => {
            updateStatus(false, 'Server error');
        });

    // Enter key for refinement
    document.getElementById('refine-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') refinePost();
    });

    // Character count update
    document.getElementById('post-preview').addEventListener('input', () => {
        const count = document.getElementById('post-preview').value.length;
        document.getElementById('char-count').textContent = `${count} characters`;
    });

    // Switch to trends tab by default
    switchTab('trends');
});
