/** Live Search
 * If charachters are more then 2 --> Send request and reload part list
 */
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const resultsContainer = document.getElementById('search-results');

    if (searchInput && resultsContainer) {
        searchInput.addEventListener('input', function() {
            const query = this.value;

            if (query.length > 2) {
                fetch(`/parts/?q=${encodeURIComponent(query)}`, {
                    headers: { 'x-requested-with': 'XMLHttpRequest' }
                })
                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = data.html;
                })
                .catch(error => console.error('Error by searching:', error));
            } else if (query.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="p-10 text-center text-gray-400 italic">
                        Start typing OEM, Name or Brand...
                    </div>`;
            }
        });
    }
});

/** 'Shop-Cart' --> Updates 'badge' with number of parts in nav with anime */
function addToQuote(part_id) {
    fetch(`/add-to-quote/${part_id}/`, {
        headers: { 'x-requested-with': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => {
        const countBadge = document.getElementById('quote-count');
        if (countBadge) {
            countBadge.innerText = data.count; 
            countBadge.classList.add('scale-125');
            setTimeout(() => countBadge.classList.remove('scale-125'), 200);
        }
    })
    .catch(error => console.error('Error:', error));
}

/** Global Input Listener
* Tracks changes in (qty-input) or discount,
* Recalculates totals when the user changes a number
 */
document.addEventListener('input', function(e) {
    if (e.target.classList.contains('qty-input') || e.target.id === 'discount-input') {
        updateQuoteTotals();
    }
});

/** If the user agrees, deletes entire temporary parts list (Shop-Cart) */
function clearQuote() {
    if(confirm("Are you sure you want to delete the offer list?")) {
        window.location.href = "/clear-quote/";
    }
}

/** Remove a specific item,
* Asks for confirmation and sends a request to the server to remove 
* only the selected part by its ID. */
function removeFromQuote(partId) {
    if(confirm("Remove a part from offer?")) {
        window.location.href = `/remove-from-quote/${partId}/`;
    }
}

/** Creates a PDF offer without saving to the database */
function generatePDF() {
    const select = document.getElementById('client-select');
    let clientName = "";

    if (select.tagName === "SELECT") {
       
        clientName = select.options[select.selectedIndex].text.split(' (')[0];
    } else {
       
        clientName = document.getElementById('client-name').value || "Client";
    }

    const discount = document.getElementById('discount-input').value;

    let items = [];
    document.querySelectorAll('.row-part').forEach(row => {
        const partId = row.querySelector('button').getAttribute('onclick').match(/'(\d+)'/)[1];
        const qty = row.querySelector('.qty-input').value;
        items.push(`${partId}:${qty}`);
    });

    const itemsParam = items.join(',');
    window.location.href = `/generate-pdf/?client=${encodeURIComponent(clientName)}&discount=${discount}&items=${itemsParam}`;
}

/** When selecting a client from the list, automatically fills in his personal discount from the database */
function updateClientDiscount() {
    const select = document.getElementById('client-select');
    if (select.tagName === "SELECT") {
        const selectedOption = select.options[select.selectedIndex];
        const discount = selectedOption.getAttribute('data-discount') || 0;
        document.getElementById('discount-input').value = discount;
        updateQuoteTotals();
    }
}

/** Validate Quantity (minimum 1), 
 * Alerts with 'Low Stock', 
 * Calculate sum with discount and total price */
function updateQuoteTotals() {
    document.querySelectorAll('.qty-input').forEach(input => {
        
        if (input.value < 1 || input.value === "") {
            input.value = 1; 
        }
    });

    const discount = parseFloat(document.getElementById('discount-input').value) || 0;
    let subtotal = 0;

    document.querySelectorAll('.row-part').forEach(row => {
        const price = parseFloat(row.getAttribute('data-price'));
        const stock = parseInt(row.getAttribute('data-stock'));
        const qtyInput = row.querySelector('.qty-input');
        const qty = parseInt(qtyInput.value) || 0;
        const warningDiv = row.querySelector('.stock-warning');
        
        if (qty > stock) {
            qtyInput.classList.add('border-red-500', 'bg-red-50', 'text-red-600');
            warningDiv.innerText = "Out of stock! Delivery by tomorrow ?";
            warningDiv.classList.add('text-red-500');
        } else {
            qtyInput.classList.remove('border-red-500', 'bg-red-50', 'text-red-600');
            warningDiv.innerText = "Available: " + stock;
            warningDiv.classList.remove('text-red-500', 'text-red-500');
            warningDiv.classList.add('text-green-600');
        }

        const lineTotal = price * qty;
        row.querySelector('.line-total').innerText = lineTotal.toFixed(2) + ' euro.';
        subtotal += lineTotal;
    });

    const discountAmount = subtotal * (discount / 100);
    const finalTotal = subtotal - discountAmount;
    document.getElementById('final-total').innerText = finalTotal.toFixed(2) + ' euro.';
}

/** Sends data to server for permanent recording in the database and downloading of availability,
 * Checks for selected client and valid quantities one last time. */
function submitFinalize() {
    const clientInput = document.getElementById('client-select');
  
    if (!clientInput) {
        alert("System error: Client reference not found!");
        return;
    }

    const clientId = clientInput.value;
    const discount = document.getElementById('discount-input').value;
    
    if (!clientId || clientId === "" || clientId === "None") { 
        alert("Please select a client from the list!"); 
        return; 
    }

    let itemsData = [];
    let hasError = false; 

    document.querySelectorAll('.row-part').forEach(row => {
        let partBtn = row.querySelector('button[onclick*="removeFromQuote"]');
        let partId = partBtn.getAttribute('onclick').match(/'(\d+)'/)[1];
        
        let qtyInput = row.querySelector('.qty-input');
        let qty = parseInt(qtyInput.value);

        if (isNaN(qty) || qty < 1) {
            alert("Quantity must be at least 1!");
            qtyInput.focus(); 
            qtyInput.classList.add('border-red-500'); 
            hasError = true;
            return;
        }

        itemsData.push(`${partId}:${qty}`);
    });

    if (hasError) return;

    if (itemsData.length === 0) {
        alert("Your cart is empty!");
        return;
    }

    if (confirm("Finalize sale? Stock will be updated!")) {
        window.location.href = `/finalize-quote/?client_id=${clientId}&discount=${discount}&items=${itemsData.join(',')}`;
    }
}

/** Used in dropdown menu or customer list,
* Filters customers in real time as you typing their name */
function filterClients() {
    let input = document.getElementById('client-search').value.toLowerCase();
    let items = document.getElementsByClassName('client-item');
    
    for (let i = 0; i < items.length; i++) {
        if (items[i].innerText.toLowerCase().includes(input)) {
            items[i].style.display = "";
        } else {
            items[i].style.display = "none";
        }
    }
}
