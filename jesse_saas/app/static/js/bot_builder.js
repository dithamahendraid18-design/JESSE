/**
 * Bot Builder Logic
 * Handles the state management for conversation starters, menu flow, and preview rendering.
 */

const BotBuilder = (function () {
    // State
    let startersData = [];
    let menuBtnData = null; // Legacy support if needed, otherwise simplified

    // DOM Elements (Cached lazily)

    function init(initialStarters, initialMenuFlow) {
        startersData = initialStarters || [];

        // Initialize hidden inputs
        updateHiddenInput();

        // Initial Render
        renderAccordions();

        // Initialize Preview if data exists
        if (startersData.length > 0) {
            updatePreview();
        }
    }

    // === UI RENDERING ===

    function renderAccordions() {
        const container = document.getElementById('accordions-container');
        if (!container) return;

        container.innerHTML = '';

        startersData.forEach((btn, index) => {
            const id = btn.id || 'btn_' + Math.random().toString(36).substr(2, 9);
            btn.id = id;

            const div = document.createElement('div');
            div.className = 'glass-card border border-white rounded-[2rem] overflow-hidden shadow-sm hover:shadow-md transition-all duration-500';
            div.innerHTML = `
                <div class="flex justify-between items-center p-6 bg-white/50 cursor-pointer hover:bg-blue-50/50 transition-colors group" onclick="BotBuilder.toggleAccordion('${id}')">
                    <span class="font-black text-gray-900 text-xs flex items-center uppercase tracking-widest">
                         <span class="w-8 h-8 rounded-xl bg-blue-600 text-white flex items-center justify-center text-[10px] mr-4 shadow-lg shadow-blue-500/30">${index + 1}</span>
                         ${btn.label || 'New Message Path'}
                    </span>
                    <div class="flex items-center gap-3">
                         <div class="flex items-center gap-1.5 mr-3 border-r pr-4 border-gray-200/50">
                             <button type="button" onclick="BotBuilder.moveMainButton(event, ${index}, -1)" class="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-white transition-all ${index === 0 ? 'opacity-30 cursor-not-allowed' : ''}" ${index === 0 ? 'disabled' : ''}>
                                 <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 15l7-7 7 7"></path></svg>
                             </button>
                             <button type="button" onclick="BotBuilder.moveMainButton(event, ${index}, 1)" class="p-2 text-gray-400 hover:text-blue-600 rounded-lg hover:bg-white transition-all ${index === startersData.length - 1 ? 'opacity-30 cursor-not-allowed' : ''}" ${index === startersData.length - 1 ? 'disabled' : ''}>
                                 <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7"></path></svg>
                             </button>
                         </div>
                         <button type="button" onclick="BotBuilder.deleteMainButton(event, ${index})" class="text-gray-400 hover:text-red-500 p-2 rounded-lg hover:bg-red-50 transition-all">
                             <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                         </button>
                         <svg class="w-4 h-4 text-blue-600 transform transition-transform duration-500 ${btn._expanded ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M19 9l-7 7-7-7"></path></svg>
                    </div>
                </div>
                
                <div class="${btn._expanded ? '' : 'hidden'} p-8 bg-white/30 border-t border-white/50 space-y-8 animate-fade-in">
                    
                    <!-- Row 1: Label & Action -->
                    <div class="grid grid-cols-2 gap-8">
                        <div>
                            <label class="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Button Label</label>
                            <input type="text" value="${btn.label || ''}" oninput="BotBuilder.updateMainLabel(${index}, this.value)" class="w-full bg-white border border-gray-100 rounded-2xl px-5 py-3.5 text-sm font-bold text-gray-900 focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:outline-none transition-all" placeholder="e.g. Reservation Inquiry">
                        </div>
                        <div>
                            <label class="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">Action Type</label>
                            <select onchange="BotBuilder.updateMainAction(${index}, this.value)" class="w-full bg-white border border-gray-100 rounded-2xl px-5 py-3.5 text-sm font-bold text-gray-900 focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:outline-none transition-all cursor-pointer">
                                <option value="message" ${!btn.action || btn.action === 'message' ? 'selected' : ''}>Message Flow</option>
                                <option value="link" ${btn.action === 'link' ? 'selected' : ''}>Link URL</option>
                                <option value="open_menu" ${btn.action === 'open_menu' ? 'selected' : ''}>Open Menu (Dynamic)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Row 2 (Link Config) -->
                    <div class="${btn.action === 'link' ? '' : 'hidden'} bg-blue-50/50 p-6 rounded-[1.5rem] border border-blue-100 shadow-inner">
                        <label class="block text-[10px] font-black text-blue-600 uppercase tracking-widest mb-3 italic">Destination Payload</label>
                        <input type="text" value="${btn.payload || ''}" oninput="BotBuilder.updateMainPayload(${index}, this.value)" class="w-full bg-white border border-blue-200 rounded-2xl px-5 py-3.5 text-sm font-medium mb-4 focus:ring-4 focus:ring-blue-500/10 focus:outline-none" placeholder="https://reservation.link">
                        
                        <label class="flex items-center gap-3 cursor-pointer group/label">
                             <div class="relative w-10 h-6 bg-gray-200 rounded-full transition-colors group-hover/label:bg-gray-300 peer-checked:bg-blue-600">
                                <input type="checkbox" id="overlay-${index}" ${btn.open_in_overlay ? 'checked' : ''} onchange="BotBuilder.updateMainOverlay(${index}, this.checked)" class="sr-only peer">
                                <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-4 shadow-sm"></div>
                             </div>
                             <span class="text-xs font-black text-gray-700 uppercase tracking-tight">Open in Webview Overlay</span>
                        </label>
                    </div>

                    <!-- Row 3 (Message Config - Gallery/Text/Chips) -->
                    <div class="${(!btn.action || btn.action === 'message') ? '' : 'hidden'} space-y-8">
                        <!-- Block 1: Image Gallery -->
                        <div>
                             <div class="flex justify-between items-center mb-4">
                                <label class="text-[10px] font-black text-gray-400 uppercase tracking-widest">Bot Response Gallery</label>
                                <span class="text-[9px] font-bold text-blue-500 uppercase tracking-tighter">Visual Assets</span>
                             </div>
                             
                             <div class="flex flex-wrap gap-4 mb-4">
                                ${(btn.blocks || []).filter(b => b.url).map((imgBlock, i) => `
                                    <div class="relative group w-24 h-24 bg-gray-100 rounded-2xl overflow-hidden border border-gray-200 shadow-sm transition-transform hover:scale-105">
                                        <img src="${imgBlock.url}" class="w-full h-full object-cover">
                                        <button onclick="BotBuilder.deleteGalleryImage(${index}, '${imgBlock.url}')" class="absolute inset-0 bg-red-600/80 text-white opacity-0 group-hover:opacity-100 flex items-center justify-center transition-all">
                                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"></path></svg>
                                        </button>
                                    </div>
                                `).join('')}
                                
                                <!-- Upload Button -->
                                <label class="w-24 h-24 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200 hover:border-blue-400 hover:bg-blue-50 transition-all cursor-pointer flex flex-col items-center justify-center text-gray-300 hover:text-blue-500 group/upload">
                                    <svg class="w-6 h-6 mb-1 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M12 4v16m8-8H4"></path></svg>
                                    <span class="text-[9px] font-black uppercase tracking-tighter">Upload</span>
                                    <input type="file" multiple accept="image/*" class="absolute inset-0 opacity-0 cursor-pointer" onchange="BotBuilder.uploadGalleryImages(this, ${index})">
                                </label>
                             </div>
                        </div>

                        <!-- Block 2: Text Description -->
                        <div>
                             <label class="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-3">Bot Response Narrative</label>
                             <textarea rows="3" oninput="BotBuilder.updateDescription(${index}, this.value)" class="w-full bg-white border border-gray-100 rounded-2xl px-5 py-4 text-sm font-medium text-gray-800 focus:ring-4 focus:ring-blue-500/10 focus:border-blue-500 focus:outline-none transition-all shadow-inner" placeholder="Type the automated response here...">${(btn.blocks || []).find(b => b.text && !b.url)?.text || ''}</textarea>
                        </div>

                         <!-- Auto-Show Menu Checkbox -->
                         <div class="flex items-center gap-3 pt-4 border-t border-gray-100">
                             <div class="relative w-8 h-4 bg-gray-200 rounded-full cursor-pointer hover:bg-gray-300 transition-colors">
                                 <input type="checkbox" id="include_kb-${index}" ${btn.include_main_menu ? 'checked' : ''} onchange="BotBuilder.updateIncludeMenu(${index}, this.checked)" class="sr-only peer">
                                 <div class="absolute left-0.5 top-0.5 w-3 h-3 bg-white rounded-full transition-transform peer-checked:translate-x-4"></div>
                             </div>
                             <label for="include_kb-${index}" class="text-[10px] font-black text-gray-500 uppercase tracking-tight cursor-pointer select-none">Append Navigation Menu to this Response</label>
                         </div>

                        <!-- Sub-Buttons (Chips) -->
                        <div class="bg-gray-50/50 rounded-[2rem] border border-gray-100 p-6 shadow-inner">
                            <div class="flex justify-between items-center mb-6">
                                <label class="text-[10px] font-black text-blue-600 uppercase tracking-[0.1em] italic">Intelligence Nodes (Chips)</label>
                                <span class="text-[9px] font-bold text-gray-400 uppercase tracking-tighter italic">Small Actionable Prompts</span>
                            </div>
                            
                             <div id="subs-container-${index}" class="space-y-4">
                                 ${(btn.sub_buttons || []).map((sub, subIndex) => `
                                    <div class="flex gap-4 items-center bg-white p-4 rounded-2xl shadow-sm border border-gray-100 group/sub">
                                        <div class="flex-1">
                                            <input type="text" value="${sub.label || ''}" oninput="BotBuilder.updateSubBtn(${index}, ${subIndex}, 'label', this.value)" placeholder="Label (acts as user message)" class="w-full text-xs font-bold bg-transparent focus:outline-none text-gray-900">
                                        </div>
                                        
                                        <div class="flex items-center gap-3">
                                            <select onchange="BotBuilder.updateSubBtnType(${index}, ${subIndex}, this.value)" class="text-[9px] font-black border border-gray-100 rounded-lg px-2 py-1.5 bg-gray-50 focus:border-blue-500 text-gray-500 uppercase tracking-widest cursor-pointer">
                                                <option value="message" ${!sub.action || sub.action === 'message' ? 'selected' : ''}>Message</option>
                                                <option value="main_menu" ${sub.action === 'main_menu' ? 'selected' : ''}>Restart</option>
                                            </select>

                                            <!-- Actions -->
                                            <div class="flex items-center gap-1 border-l pl-3 border-gray-100">
                                                <div class="flex flex-col">
                                                    <button type="button" onclick="BotBuilder.moveSubBtn(${index}, ${subIndex}, -1)" class="text-gray-300 hover:text-blue-600 transition-colors ${subIndex === 0 ? 'opacity-30 cursor-not-allowed' : ''}" ${subIndex === 0 ? 'disabled' : ''}>
                                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M5 15l7-7 7 7"></path></svg>
                                                    </button>
                                                    <button type="button" onclick="BotBuilder.moveSubBtn(${index}, ${subIndex}, 1)" class="text-gray-300 hover:text-blue-600 transition-colors ${subIndex === btn.sub_buttons.length - 1 ? 'opacity-30 cursor-not-allowed' : ''}" ${subIndex === btn.sub_buttons.length - 1 ? 'disabled' : ''}>
                                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="4" d="M19 9l-7 7-7-7"></path></svg>
                                                    </button>
                                                </div>
                                                <button type="button" onclick="BotBuilder.deleteSubBtn(${index}, ${subIndex})" class="text-gray-300 hover:text-red-500 p-2 rounded-lg hover:bg-red-50 transition-all ml-1">
                                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M6 18L18 6M6 6l12 12"></path></svg>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                 `).join('')}
                             </div>
                             <button type="button" onclick="BotBuilder.addSubBtn(${index})" class="mt-6 w-full py-4 text-[10px] font-black uppercase tracking-[0.1em] text-blue-600 border-2 border-dashed border-blue-200 rounded-2xl hover:bg-blue-50 hover:border-blue-400 transition-all">+ Add Child Path</button>
                        </div>
                    </div>
                </div>
            `;
            container.appendChild(div);
        });

        updateHiddenInput();
        updatePreview();
    }

    // === DATA MANIPULATION ===

    function addNewButton() {
        if (startersData.length >= 5) {
            alert('Max 5 main buttons allowed.');
            return;
        }

        const newId = 'btn_' + Date.now();
        startersData.push({ id: newId, label: 'New Button', action: 'message', payload: '', response_text: '', sub_buttons: [], include_main_menu: false, _expanded: true });

        renderAccordions();
        // Scroll to bottom
        setTimeout(() => {
            const c = document.getElementById('accordions-container');
            if (c && c.lastElementChild) c.lastElementChild.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    }

    function deleteMainButton(e, index) {
        e.stopPropagation();
        if (confirm('Delete this button group?')) {
            startersData.splice(index, 1);
            renderAccordions();
        }
    }

    function toggleAccordion(id) {
        const item = startersData.find(b => b.id === id);
        if (item) {
            item._expanded = !item._expanded;
            renderAccordions();
        }
    }

    function updateMainLabel(index, val) {
        startersData[index].label = val;
        updateHiddenInput();
        updatePreview();
    }

    function updateMainAction(index, action) {
        startersData[index].action = action;

        // Auto-configure for Dynamic Menu
        if (action === 'open_menu') {
            startersData[index].open_in_overlay = true;
            startersData[index].payload = '_DYNAMIC_MENU_LINK_';
        }

        renderAccordions();
        updateHiddenInput();
    }

    function updateMainPayload(index, payload) {
        startersData[index].payload = payload;
        updateHiddenInput();
    }

    function updateMainOverlay(index, checked) {
        startersData[index].open_in_overlay = checked;
        updateHiddenInput();
    }

    function updateDescription(index, val) {
        let blocks = startersData[index].blocks || [];
        const imgBlocks = blocks.filter(b => b.url);

        startersData[index].blocks = [...imgBlocks];
        if (val) {
            startersData[index].blocks.push({ type: 'text', text: val });
        }
        updateHiddenInput();
        // Don't re-render for text inputs to keep focus
    }

    function updateIncludeMenu(index, val) {
        startersData[index].include_main_menu = val;
        updateHiddenInput();
    }

    // === SUB BUTTONS ===

    function addSubBtn(index) {
        if (!startersData[index].sub_buttons) startersData[index].sub_buttons = [];
        startersData[index].sub_buttons.push({ label: 'Next', action: 'message', payload: '' });
        renderAccordions();
    }

    function deleteSubBtn(index, subIndex) {
        startersData[index].sub_buttons.splice(subIndex, 1);
        renderAccordions();
    }

    function moveSubBtn(index, subIndex, direction) {
        const subButtons = startersData[index].sub_buttons;
        const newIndex = subIndex + direction;
        if (newIndex < 0 || newIndex >= subButtons.length) return;

        // Swap
        [subButtons[subIndex], subButtons[newIndex]] = [subButtons[newIndex], subButtons[subIndex]];
        renderAccordions();
    }

    function updateSubBtn(index, subIndex, field, val) {
        const sub = startersData[index].sub_buttons[subIndex];
        sub[field] = val;
        if (field === 'label' && (!sub.action || sub.action === 'message')) {
            sub.payload = val;
        }
        updateHiddenInput();
        updatePreview();
    }

    function updateSubBtnType(index, subIndex, type) {
        if (!startersData[index].sub_buttons[subIndex]) return;
        const sub = startersData[index].sub_buttons[subIndex];
        sub.action = type;

        if (type === 'main_menu') {
            if (!sub.label || sub.label === sub.payload) sub.label = "⬅ Back";
            sub.payload = '';
        } else {
            sub.payload = sub.label;
        }
        renderAccordions();
        updateHiddenInput();
    }

    function moveMainButton(e, index, direction) {
        e.stopPropagation();
        const newIndex = index + direction;
        if (newIndex < 0 || newIndex >= startersData.length) return;

        [startersData[index], startersData[newIndex]] = [startersData[newIndex], startersData[index]];

        renderAccordions();
        updateHiddenInput();
        updatePreview();
    }

    // === HELPERS ===

    function updateHiddenInput() {
        const cleanStarters = startersData.map(({ _expanded, ...rest }) => rest);
        const input = document.getElementById('conversation-starters-json');
        if (input) input.value = JSON.stringify(cleanStarters);
    }

    function updatePreview() {
        const previewButtons = document.getElementById('preview-buttons');
        if (window.renderPreviewButtons) {
            window.renderPreviewButtons(startersData, previewButtons);
        }
    }

    // === IMAGE UPLOADER ===
    async function uploadGalleryImages(input, index) {
        if (!input.files || input.files.length === 0) return;

        const files = Array.from(input.files);
        // Assuming single upload for simplicity for now, or loop
        const file = files[0];

        const formData = new FormData();
        formData.append('image', file);

        try {
            const res = await fetch('/admin/upload/bot-image', { method: 'POST', body: formData });
            const data = await res.json();
            if (data.url) {
                if (!startersData[index].blocks) startersData[index].blocks = [];
                // Add before text
                const textBlock = startersData[index].blocks.find(b => b.text && !b.url);
                const newImg = { type: 'image', url: data.url };

                // Reconstruct blocks: Images first, then text
                const existingImgs = startersData[index].blocks.filter(b => b.url);
                existingImgs.push(newImg);

                startersData[index].blocks = [...existingImgs];
                if (textBlock) startersData[index].blocks.push(textBlock);

                updateHiddenInput();
                renderAccordions();
            } else {
                alert('Upload failed: ' + (data.error || 'Unknown error'));
            }
        } catch (e) {
            console.error(e);
            alert('Upload error');
        }
    }

    function deleteGalleryImage(index, url) {
        if (!startersData[index].blocks) return;
        startersData[index].blocks = startersData[index].blocks.filter(b => b.url !== url);
        updateHiddenInput();
        renderAccordions();
    }

    // Public API
    return {
        init,
        addNewButton,
        deleteMainButton,
        toggleAccordion,
        updateMainLabel,
        updateMainAction,
        updateMainPayload,
        updateMainOverlay,
        updateDescription,
        updateIncludeMenu,
        addSubBtn,
        deleteSubBtn,
        moveSubBtn,
        updateSubBtn,
        updateSubBtnType,
        moveMainButton,
        uploadGalleryImages,
        deleteGalleryImage
    };
})();
