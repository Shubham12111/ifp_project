function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}
const csrfToken = getCookie('csrftoken');
console.log('CSRF Token:', csrfToken);


function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function confirmDelete(itemId, confirmMessage, successMessage, deleteUrl) {
    const csrfToken = getCookie('csrftoken');

    Swal.fire({
        title: 'Confirm Delete',
        text: confirmMessage,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        cancelButtonColor: '#d33',
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
            .then(response => {
                if (response.ok) {
                    // If the delete operation is successful, show success message and reload the page
                    Swal.fire({
                        title: 'Deleted!',
                        text: successMessage,
                        icon: 'success',
                    }).then(() => {
                        window.location.reload();
                    });
                } else {
                    // If the delete operation fails, show an error message
                    Swal.fire({
                        title: 'Error',
                        text: 'Failed to delete.',
                        icon: 'error',
                    });
                }
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

