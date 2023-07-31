// form-handler.js

function handleFormSubmit(event) {
    event.preventDefault(); // Prevent the default form submission

    const formData = new FormData(this);
    const url = this.getAttribute("data-url");


    fetch(url, {
        method: 'PUT',
        headers: {
            "X-CSRFToken": formData.get("csrfmiddlewaretoken"), // Add CSRF token manually
        },
        body: formData
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        // Handle the successful response from the server
        console.log(data);
        if (data.status == 'error')
        {
            displayFormErrors(data.data);
        }
        else
        {
            window.location.reload();
        }
        // Show a success message or update the page accordingly
        // For example, you could display a success message on the page
        // or update specific parts of the page with the updated data

        // Optionally, you can reload the page after showing the success message
        // 
    })
    .catch(error => {
        // Handle any errors that occurred during the fetch
        // Show the error messages on the form
        displayFormErrors(error);
    });
}

function displayFormErrors(errors) {
    // Clear previous error messages
    const errorElements = document.querySelectorAll(".help-block");
    errorElements.forEach(element => element.remove());

    // Display new error messages
    for (const field in errors) {
        const fieldErrors = errors[field];
        // Display the error messages for each field on the form
        const fieldElement = document.querySelector(`[name="${field}"]`);
        if (fieldElement) {
            const errorElement = document.createElement("span");
            errorElement.className = "help-block";
            errorElement.textContent = fieldErrors.join(", ");
            fieldElement.parentElement.appendChild(errorElement);
        }
    }
}


// Attach the form handling function to the form submit event
document.querySelectorAll("#form-handler").forEach(form => {
    form.addEventListener("submit", handleFormSubmit);
});
