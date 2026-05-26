document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const previewArea = document.getElementById('previewArea');
    const imagePreview = document.getElementById('imagePreview');
    const btnRemoveImage = document.getElementById('btnRemoveImage');
    const actionFooter = document.getElementById('actionFooter');
    
    const btnExtract = document.getElementById('btnExtract');
    const btnText = document.getElementById('btnText');
    const btnSpinner = document.getElementById('btnSpinner');
    
    const resultsIdle = document.getElementById('resultsIdle');
    const resultsContent = document.getElementById('resultsContent');
    const qaCard = document.getElementById('qaCard');
    const backendStatus = document.getElementById('backendStatus');
    const statusText = document.getElementById('statusText');
    
    // Result display fields
    const resVendor = document.getElementById('resVendor');
    const resInvoiceNum = document.getElementById('resInvoiceNum');
    const resDate = document.getElementById('resDate');
    const resTime = document.getElementById('resTime');
    const resSubtotal = document.getElementById('resSubtotal');
    const resDiscount = document.getElementById('resDiscount');
    const resTax = document.getElementById('resTax');
    const resTotal = document.getElementById('resTotal');
    const rawJsonCode = document.getElementById('rawJsonCode');
    
    // Items Section
    const itemsSection = document.getElementById('itemsSection');
    const itemsTableBody = document.getElementById('itemsTableBody');
    
    // Accordion
    const accordionTrigger = document.getElementById('accordionTrigger');
    const accordionContent = document.getElementById('accordionContent');
    
    // Chat Q&A Elements
    const chatInput = document.getElementById('chatInput');
    const btnSendChat = document.getElementById('btnSendChat');
    const chatMessages = document.getElementById('chatMessages');
    
    // Export and Copy Elements
    const btnExportExcel = document.getElementById('btnExportExcel');
    const toast = document.getElementById('toast');
    
    // App State Variables
    let selectedFile = null;
    let extractedData = null;

    // Detect Initial Status on Load (by triggering a light endpoint or default status)
    // For simplicity, we show "Awaiting File Upload" then update upon analysis
    updateStatusLabel(null);

    // Drag and Drop Events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Remove Selected Image
    btnRemoveImage.addEventListener('click', resetUploadState);

    // Handle File Selection
    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            showToast("Error: Selected file is not an image!", true);
            return;
        }
        selectedFile = file;
        
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            dropZone.classList.add('hidden');
            previewArea.classList.remove('hidden');
            actionFooter.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }

    // Reset Upload State
    function resetUploadState() {
        selectedFile = null;
        extractedData = null;
        fileInput.value = '';
        imagePreview.src = '';
        dropZone.classList.remove('hidden');
        previewArea.classList.add('hidden');
        actionFooter.classList.add('hidden');
        
        // Hide Results and Chat
        resultsIdle.classList.remove('hidden');
        resultsContent.classList.add('hidden');
        qaCard.classList.add('hidden');
        btnExportExcel.classList.add('disabled');
        btnExportExcel.disabled = true;
        
        // Reset Accordion
        accordionTrigger.classList.remove('active');
        accordionContent.classList.add('hidden');
        
        // Reset values
        resVendor.textContent = 'Not extracted';
        resInvoiceNum.textContent = 'Not extracted';
        resDate.textContent = 'Not extracted';
        resTime.textContent = 'Not extracted';
        resSubtotal.textContent = 'Not extracted';
        resDiscount.textContent = 'Not extracted';
        resTax.textContent = 'Not extracted';
        resTotal.textContent = 'Not extracted';
        
        // Clear items table
        itemsTableBody.innerHTML = '';
        itemsSection.classList.add('hidden');
        
        // Clear chat history
        chatMessages.innerHTML = `
            <div class="chat-message system">
                <p>Extraction complete! Ask me any specific details about this invoice (e.g. GST registration, payment terms, list of items, etc.).</p>
            </div>
        `;
    }

    // Extract Invoice Data via API
    btnExtract.addEventListener('click', async () => {
        if (!selectedFile) return;
        
        setLoadingState(true);
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        try {
            const response = await fetch('/extract', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP Error! Status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.status === 'success') {
                extractedData = result.data;
                populateResults(extractedData);
                updateStatusLabel(result.mock_mode);
                showToast("Invoice processed successfully!");
            } else {
                throw new Error(result.error || "Unknown extraction error");
            }
        } catch (error) {
            console.error("Extraction error:", error);
            showToast("Failed to extract invoice data. Check console logs.", true);
        } finally {
            setLoadingState(false);
        }
    });

    // Populate Results Dashboard
    function populateResults(data) {
        // Display values or fallbacks
        resVendor.textContent = data.vendor_name || 'Not found';
        resInvoiceNum.textContent = data.invoice_number || 'Not found';
        resDate.textContent = data.invoice_date || 'Not found';
        resTime.textContent = data.invoice_time || 'Not found';
        
        resSubtotal.textContent = data.subtotal !== null ? data.subtotal.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'Not found';
        resDiscount.textContent = data.discount !== null ? data.discount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'Not found';
        resTax.textContent = data.tax !== null ? data.tax.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'Not found';
        resTotal.textContent = data.total_amount !== null ? data.total_amount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : 'Not found';
        
        // Populating items table
        if (data.items && data.items.length > 0) {
            let html = '';
            data.items.forEach(item => {
                const priceFormatted = typeof item.price === 'number' ? item.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : item.price;
                html += `<tr>
                    <td>${item.name}</td>
                    <td style="text-align: right;">${item.qty}</td>
                    <td style="text-align: right;">${priceFormatted}</td>
                </tr>`;
            });
            itemsTableBody.innerHTML = html;
            itemsSection.classList.remove('hidden');
        } else {
            itemsTableBody.innerHTML = '';
            itemsSection.classList.add('hidden');
        }
        
        // Code pre block
        rawJsonCode.textContent = JSON.stringify(data, null, 2);
        
        // Adjust Panel views
        resultsIdle.classList.add('hidden');
        resultsContent.classList.remove('hidden');
        qaCard.classList.remove('hidden');
        
        // Enable export
        btnExportExcel.classList.remove('disabled');
        btnExportExcel.disabled = false;
    }

    // Interactive QA chat handler
    btnSendChat.addEventListener('click', sendQuestion);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendQuestion();
        }
    });

    async function sendQuestion() {
        const text = chatInput.value.trim();
        if (!text || !extractedData) return;
        
        // Append user question
        appendChatMessage(text, 'user');
        chatInput.value = '';
        
        // Append Loading message
        const loadingMessageId = appendChatMessage("Analyzing question...", 'assistant', true);
        
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: text,
                    invoice_data: extractedData
                })
            });
            
            if (!response.ok) {
                throw new Error("Chat request failed");
            }
            
            const result = await response.json();
            
            // Remove loading indicator
            const loadingMsgElement = document.getElementById(loadingMessageId);
            if (loadingMsgElement) {
                loadingMsgElement.remove();
            }
            
            // Append assistant answer
            appendChatMessage(result.answer, 'assistant');
            
        } catch (error) {
            console.error(error);
            const loadingMsgElement = document.getElementById(loadingMessageId);
            if (loadingMsgElement) {
                loadingMsgElement.remove();
            }
            appendChatMessage("Sorry, an error occurred while retrieving the answer. Please try again.", 'assistant');
        }
    }

    // Helper to append message bubbles
    function appendChatMessage(text, sender, isLoading = false) {
        const messageId = 'chat-msg-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message ${sender}`;
        msgDiv.id = messageId;
        
        if (isLoading) {
            msgDiv.innerHTML = `<p>${text} <i class="fa-solid fa-ellipsis-stroke fa-beat"></i></p>`;
        } else {
            msgDiv.innerHTML = `<p>${text}</p>`;
        }
        
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return messageId;
    }

    // Toggle raw JSON accordion
    accordionTrigger.addEventListener('click', () => {
        accordionTrigger.classList.toggle('active');
        accordionContent.classList.toggle('hidden');
    });

    // Copy to clipboard actions
    document.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-target');
            const targetEl = document.getElementById(targetId);
            if (targetEl) {
                const valToCopy = targetEl.textContent;
                if (valToCopy && valToCopy !== 'Not extracted') {
                    navigator.clipboard.writeText(valToCopy).then(() => {
                        showToast("Value copied to clipboard!");
                    }).catch(err => {
                        console.error("Copy error:", err);
                    });
                } else {
                    showToast("No data available to copy!", true);
                }
            }
        });
    });

    // SheetJS Export to Excel
    btnExportExcel.addEventListener('click', () => {
        if (!extractedData) return;
        
        try {
            const rows = [];
            if (extractedData.items && extractedData.items.length > 0) {
                extractedData.items.forEach(item => {
                    rows.push({
                        "Vendor Name": extractedData.vendor_name || 'N/A',
                        "Invoice Number": extractedData.invoice_number || 'N/A',
                        "Invoice Date": extractedData.invoice_date || 'N/A',
                        "Invoice Time": extractedData.invoice_time || 'N/A',
                        "Item Description": item.name,
                        "Quantity": item.qty,
                        "Item Price": item.price,
                        "Subtotal": extractedData.subtotal || 0.00,
                        "Discount": extractedData.discount || 0.00,
                        "Tax (GST)": extractedData.tax || 0.00,
                        "Total Amount": extractedData.total_amount || 0.00
                    });
                });
            } else {
                rows.push({
                    "Vendor Name": extractedData.vendor_name || 'N/A',
                    "Invoice Number": extractedData.invoice_number || 'N/A',
                    "Invoice Date": extractedData.invoice_date || 'N/A',
                    "Invoice Time": extractedData.invoice_time || 'N/A',
                    "Item Description": 'N/A',
                    "Quantity": 'N/A',
                    "Item Price": 'N/A',
                    "Subtotal": extractedData.subtotal || 0.00,
                    "Discount": extractedData.discount || 0.00,
                    "Tax (GST)": extractedData.tax || 0.00,
                    "Total Amount": extractedData.total_amount || 0.00
                });
            }
            
            // Create SheetJS Worksheet
            const worksheet = XLSX.utils.json_to_sheet(rows);
            
            // Auto size columns for readability
            worksheet['!cols'] = [
                { wch: 25 },
                { wch: 15 },
                { wch: 15 },
                { wch: 15 },
                { wch: 30 },
                { wch: 10 },
                { wch: 15 },
                { wch: 15 },
                { wch: 15 },
                { wch: 15 },
                { wch: 15 }
            ];
            
            // Create Workbook and append sheet
            const workbook = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(workbook, worksheet, "Invoice Details");
            
            // Trigger browser download of Excel spreadsheet
            const filename = `invoice_extract_${extractedData.invoice_number || 'data'}.xlsx`;
            XLSX.writeFile(workbook, filename);
            showToast("Excel spreadsheet exported successfully!");
        } catch (error) {
            console.error("Export error:", error);
            showToast("Failed to export Excel file.", true);
        }
    });

    // UI Loading state manager
    function setLoadingState(loading) {
        if (loading) {
            btnExtract.disabled = true;
            btnText.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing Image...`;
            btnSpinner.classList.remove('hidden');
        } else {
            btnExtract.disabled = false;
            btnText.innerHTML = `<i class="fa-solid fa-microchip"></i> Analyze Invoice`;
            btnSpinner.classList.add('hidden');
        }
    }

    // Status indicator modifier
    function updateStatusLabel(isMockMode) {
        backendStatus.className = "backend-status-badge";
        if (isMockMode === null) {
            backendStatus.classList.add('hidden');
        } else if (isMockMode) {
            backendStatus.classList.add('mock-mode');
            statusText.textContent = "Mock Inference Mode";
        } else {
            backendStatus.classList.add('real-mode');
            statusText.textContent = "HuggingFace LLaVA Mode";
        }
    }

    // Toast manager
    function showToast(message, isError = false) {
        toast.textContent = message;
        toast.className = "toast";
        if (isError) {
            toast.style.borderColor = "var(--color-accent-rose)";
        } else {
            toast.style.borderColor = "var(--color-accent-blue)";
        }
        toast.classList.remove('hidden');
        
        // Fade out
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 3000);
    }
});
