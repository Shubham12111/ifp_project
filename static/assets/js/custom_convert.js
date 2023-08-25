function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function Customconfirm(itemId, confirmMessage, yesRedirectUrl, noStayUrl) {
    const csrfToken = getCookie('csrftoken');

    Swal.fire({
        title: '<h4 class="mb-0">Confirmation</h4>',
        html: '<div class="custom-content text-sm">' + confirmMessage + '</div>', // Use a custom class for the content
        showCancelButton: true,
        confirmButtonText: 'Yes',
        cancelButtonText: 'No',
        cancelButtonColor: '#6c757d',
        confirmButtonColor: '#6c757d',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(yesRedirectUrl, {
                method: 'POST', // You can change this to the appropriate HTTP method
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ contact_id: itemId }), // Pass any necessary data for the conversion
            })
            .then(data => {
                window.location.href = yesRedirectUrl; // Redirect to the customer listing page
            })
            .catch(error => {
                console.error("Error occurred during the conversion:", error);
                // If an error occurs during the conversion, show an error message
                Swal.fire({
                    title: 'Error',
                    text: 'An error occurred during the conversion.',
                    icon: 'error',
                });
            });
        } else {
            window.location.href = noStayUrl; // Stay on the same page
        }
    });
}

function showPopupAndRedirect(url) {
    Swal.fire({
        title: '<h4 class="mb-0">Confirmation</h4>',
        text: 'Are you sure you want to convert this contact into customer?',
        showCancelButton: true,
        confirmButtonText: 'Yes',
        cancelButtonText: 'No',
        cancelButtonColor: '#6c757d',
        confirmButtonColor: '#6c757d',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = url;
        }
    });
}