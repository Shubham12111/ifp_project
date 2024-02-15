function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function CustomconfirmDelete(itemId, confirmMessage, successMessage, deleteUrl) {
    const csrfToken = getCookie('csrftoken');

    Swal.fire({
        title: '<h4 class="mb-0">Confirm Delete</h4>',
        html: '<div class="custom-content text-sm">' + confirmMessage + '</div>', // Use a custom class for the content
        showCancelButton: true,
        showCloseButton: true,
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        cancelButtonColor: '#6c757d',
        confirmButtonColor: '#d73632',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(deleteUrl, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json',
                },
            })
            .then(data => {
                window.location.reload();
                
            })
            .catch(error => {
                console.error("Error occurred during the delete operation:", error);
                // If an error occurs during the delete operation, show an error message
                Swal.fire({
                    title: 'Error',
                    text: 'An error occurred while deleting.',
                    icon: 'error',
                });
            });
        }
    });
}

