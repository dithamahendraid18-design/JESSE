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
            div.className = 'border border-gray-200 rounded-lg overflow-hidden bg-gray-50';
            div.innerHTML = `
                <div class="flex justify-between items-center p-3 bg-white border-b border-gray-100 cursor-pointer hover:bg-gray-50 transition-colors" onclick="BotBuilder.toggleAccordion('${id}')">
                    <span class="font-medium text-gray-700 text-sm flex items-center">
                         <span class="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs mr-2 font-bold">${index + 1}</span>
                         ${btn.label || 'New Button'}
                    </span>
                    <div class="flex items-center gap-2">
                         <div class="flex items-center gap-1 mr-2 border-r pr-2 border-gray-200">
                             <button type="button" onclick="BotBuilder.moveMainButton(event, ${index}, -1)" class="p-1 text-gray-400 hover:text-blue-600 ${index === 0 ? 'opacity-30 cursor-not-allowed' : ''}" ${index === 0 ? 'disabled' : ''}>
                                 <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
                             </button>
                             <button type="button" onclick="BotBuilder.moveMainButton(event, ${index}, 1)" class="p-1 text-gray-400 hover:text-blue-600 ${index === startersData.length - 1 ? 'opacity-30 cursor-not-allowed' : ''}" ${index === startersData.length - 1 ? 'disabled' : ''}>
                                 <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                             </button>
                         </div>
                         <button type="button" onclick="BotBuilder.deleteMainButton(event, ${index})" class="text-gray-400 hover:text-red-500 p-1">
                             <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                         </button>
                         <svg class="w-4 h-4 text-gray-400 transform transition-transform ${btn._expanded ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                    </div>
                </div>
                
                <div class="${btn._expanded ? '' : 'hidden'} p-4 bg-white border-t border-gray-100 space-y-4">
                    
                    <!-- Row 1: Label & Action -->
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Button Label</label>
                            <input type="text" value="${btn.label || ''}" oninput="BotBuilder.updateMainLabel(${index}, this.value)" class="w-full border rounded px-3 py-2 text-sm focus:ring-1 focus:ring-blue-500" placeholder="e.g. Nasi Goreng">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Action Type</label>
                            <select onchange="BotBuilder.updateMainAction(${index}, this.value)" class="w-full border rounded px-3 py-2 text-sm bg-white focus:ring-1 focus:ring-blue-500">
                                <option value="message" ${!btn.action || btn.action === 'message' ? 'selected' : ''}>Message Flow</option>
                                <option value="link" ${btn.action === 'link' ? 'selected' : ''}>Link URL</option>
                                <option value="open_menu" ${btn.action === 'open_menu' ? 'selected' : ''}>Open Menu (Dynamic)</option>
                            </select>
                        </div>
                    </div>

                    <!-- Row 2 (Link Config) -->
                    <div class="${btn.action === 'link' ? '' : 'hidden'} mt-4 bg-blue-50 p-4 rounded-lg border border-blue-100">
                        <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Target URL</label>
                        <input type="text" value="${btn.payload || ''}" oninput="BotBuilder.updateMainPayload(${index}, this.value)" class="w-full border rounded px-3 py-2 text-sm mb-3" placeholder="https://example.com">
                        
                        <div class="flex items-center gap-2">
                             <input type="checkbox" id="overlay-${index}" ${btn.open_in_overlay ? 'checked' : ''} onchange="BotBuilder.updateMainOverlay(${index}, this.checked)" class="rounded text-blue-600 focus:ring-blue-500 border-gray-300 w-4 h-4">
                             <label for="overlay-${index}" class="text-sm text-gray-700 select-none cursor-pointer">Open inside Overlay (Webview)</label>
                        </div>
                    </div>

                    <!-- Row 3 (Message Config - Gallery/Text/Chips) -->
                    <div class="${(!btn.action || btn.action === 'message') ? '' : 'hidden'} mt-4 space-y-4">
                        <!-- Block 1: Image Gallery -->
                        <div>
                             <div class="flex justify-between items-center mb-2">
                                <label class="text-xs font-semibold text-gray-500 uppercase tracking-wide">Block 1: Images (Gallery)</label>
                                <span class="text-[10px] text-gray-400">Multiple images allowed</span>
                             </div>
                             
                             <div class="grid grid-cols-4 gap-2 mb-2">
                                ${(btn.blocks || []).filter(b => b.url).map((imgBlock, i) => `
                                    <div class="relative group aspect-square bg-gray-100 rounded-lg overflow-hidden border border-gray-200">
                                        <img src="${imgBlock.url}" class="w-full h-full object-cover">
                                        <button onclick="BotBuilder.deleteGalleryImage(${index}, '${imgBlock.url}')" class="absolute inset-0 bg-black/50 text-white opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity text-xs">&times;</button>
                                    </div>
                                `).join('')}
                                
                                <!-- Upload Button -->
                                <label class="relative aspect-square bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 hover:border-blue-400 hover:bg-blue-50 transition-colors cursor-pointer flex flex-col items-center justify-center text-gray-400 hover:text-blue-500">
                                    <svg class="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                                    <span class="text-[10px] font-medium">Add Img</span>
                                    <input type="file" multiple accept="image/*" class="absolute inset-0 opacity-0 cursor-pointer" onchange="BotBuilder.uploadGalleryImages(this, ${index})">
                                </label>
                             </div>
                        </div>

                        <!-- Block 2: Text Description -->
                        <div>
                             <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Block 2: Text Description</label>
                             <textarea rows="3" oninput="BotBuilder.updateDescription(${index}, this.value)" class="w-full border rounded px-3 py-2 text-sm focus:ring-1 focus:ring-blue-500 bg-white" placeholder="Type your message here...">${(btn.blocks || []).find(b => b.text && !b.url)?.text || ''}</textarea>
                        </div>

                         <!-- Auto-Show Menu Checkbox -->
                         <div class="flex items-center gap-2 pt-2 border-t border-gray-100">
                             <input type="checkbox" id="include_kb-${index}" ${btn.include_main_menu ? 'checked' : ''} onchange="BotBuilder.updateIncludeMenu(${index}, this.checked)" class="rounded text-blue-600 focus:ring-blue-500 border-gray-300">
                             <label for="include_kb-${index}" class="text-xs text-gray-600 cursor-pointer select-none">Show Main Menu options after this response?</label>
                         </div>

                        <!-- Sub-Buttons (Chips) -->
                        <div class="bg-gray-50 rounded-lg border border-gray-200 p-3">
                            <div class="flex justify-between items-center mb-2">
                                <label class="text-xs font-bold text-gray-500 uppercase tracking-wide">Sub-Buttons (Chips)</label>
                                <span class="text-[10px] text-gray-400">Optional small buttons below response</span>
                            </div>
                            
                             <div id="subs-container-${index}" class="space-y-2">
                                 ${(btn.sub_buttons || []).map((sub, subIndex) => `
                                    <div class="flex gap-2 items-center bg-white p-2 rounded shadow-sm border border-gray-200">
                                        <div class="flex-1">
                                            <input type="text" value="${sub.label || ''}" oninput="BotBuilder.updateSubBtn(${index}, ${subIndex}, 'label', this.value)" placeholder="Label (acts as text sent)" class="w-full text-xs border rounded px-2 py-1 focus:outline-none focus:border-blue-500">
                                        </div>
                                        
                                        <select onchange="BotBuilder.updateSubBtnType(${index}, ${subIndex}, this.value)" class="text-[10px] border border-gray-200 rounded px-1 py-1 bg-gray-50 focus:border-blue-500 text-gray-600 w-20 cursor-pointer">
                                            <option value="message" ${!sub.action || sub.action === 'message' ? 'selected' : ''}>Message</option>
                                            <option value="main_menu" ${sub.action === 'main_menu' ? 'selected' : ''}>Back Btn</option>
                                        </select>

                                        <!-- Actions -->
                                        <div class="flex items-center gap-1 border-l pl-2 border-gray-100">
                                            <div class="flex flex-col">
                                                <button type="button" onclick="BotBuilder.moveSubBtn(${index}, ${subIndex}, -1)" class="text-gray-400 hover:text-blue-600 ${subIndex === 0 ? 'opacity-30 cursor-not-allowed' : ''}" ${subIndex === 0 ? 'disabled' : ''}>
                                                    <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path></svg>
                                                </button>
                                                <button type="button" onclick="BotBuilder.moveSubBtn(${index}, ${subIndex}, 1)" class="text-gray-400 hover:text-blue-600 ${subIndex === btn.sub_buttons.length - 1 ? 'opacity-30 cursor-not-allowed' : ''}" ${subIndex === btn.sub_buttons.length - 1 ? 'disabled' : ''}>
                                                    <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                                </button>
                                            </div>
                                            <button type="button" onclick="BotBuilder.deleteSubBtn(${index}, ${subIndex})" class="text-gray-400 hover:text-red-500 p-1 ml-1">
                                                &times;
                                            </button>
                                        </div>
                                    </div>
                                 `).join('')}
                            </div>
                            <button type="button" onclick="BotBuilder.addSubBtn(${index})" class="mt-3 w-full py-1.5 text-xs text-blue-600 font-medium border border-dashed border-blue-300 rounded hover:bg-blue-50 transition-colors">+ Add Child Button</button>
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
