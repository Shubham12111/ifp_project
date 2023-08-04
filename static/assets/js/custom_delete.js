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
        title: 'Confirm Delete',
        text: confirmMessage,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        cancelButtonColor: '#6c757d',
        confirmButtonColor: '#6c757d',
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

