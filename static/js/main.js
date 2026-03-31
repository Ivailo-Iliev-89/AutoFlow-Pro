
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
                .catch(error => console.error('Грешка при търсене:', error));
            } else if (query.length === 0) {
                resultsContainer.innerHTML = `
                    <div class="p-10 text-center text-gray-400 italic">
                        Start typing OEM, Name or Brand...
                    </div>`;
            }
        });
    }
});

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

document.addEventListener('input', function(e) {
    if (e.target.classList.contains('qty-input') || e.target.id === 'discount-input') {
        updateQuoteTotals();
    }
});

function clearQuote() {
    if(confirm("Are you sure you want to delete the offer list?")) {
        window.location.href = "/clear-quote/";
    }
}

function removeFromQuote(partId) {
    if(confirm("Remove a part from offer?")) {
        window.location.href = `/remove-from-quote/${partId}/`;
    }
}

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

function updateClientDiscount() {
    const select = document.getElementById('client-select');
    if (select.tagName === "SELECT") {
        const selectedOption = select.options[select.selectedIndex];
        const discount = selectedOption.getAttribute('data-discount') || 0;
        document.getElementById('discount-input').value = discount;
        updateQuoteTotals();
    }
}

function updateQuoteTotals() {
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
    document.querySelectorAll('.row-part').forEach(row => {
        let partBtn = row.querySelector('button[onclick*="removeFromQuote"]');
        let partId = partBtn.getAttribute('onclick').match(/'(\d+)'/)[1];
        let qty = row.querySelector('.qty-input').value;
        itemsData.push(`${partId}:${qty}`);
    });

    if (itemsData.length === 0) {
        alert("Your cart is empty!");
        return;
    }

    if (confirm("Finalize sale? Stock will be updated!")) {
        window.location.href = `/finalize-quote/?client_id=${clientId}&discount=${discount}&items=${itemsData.join(',')}`;
    }
}
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
