// Get all submit buttons with the common class
const submitButtons = document.querySelectorAll('.js-submit-btn');

// Function to handle form submission
function handleFormSubmission(event) {
  const submitBtn = event.target;

  // Get the parent form of the clicked button
  const form = submitBtn.closest('form');

  // Check if the form is valid
  if (form && form.checkValidity()) {
    // If the form is valid, disable the button and submit the form
    submitBtn.disabled = true;
    form.submit();

    // Enable the button after 5 seconds
    setTimeout(() => {
      submitBtn.disabled = false;
    }, 5000); // 5000 milliseconds = 5 seconds
  } else {
    // If the form is not valid, prevent form submission
    event.preventDefault();
    event.stopPropagation();
  }
}

// Attach event listeners to all the submit buttons
submitButtons.forEach((button) => {
  button.addEventListener('click', handleFormSubmission);
});
