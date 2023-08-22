// function validateAndUpload(selectedFile, validFormats) {
//     const fileExtension = selectedFile.name.split('.').pop().toLowerCase();
    
//     if (!validFormats.includes('.' + fileExtension)) {
//         alert('Invalid file format. Please select a valid file format.');
//         return false;
//     }

//     // The file format is valid, proceed with uploading
//     // Implement your upload logic here
//     return true;
// }
// document.getElementById('uploadButton').addEventListener('click', function() {
//     const validFormats = [];

//     // Get all file inputs on the page
//     const fileInputs = document.querySelectorAll('input[type="file"]');
    
//     // Loop through each file input and extract its accepted formats
//     fileInputs.forEach(input => {
//         const acceptedFormats = input.accept.split(',').map(format => format.trim());
//         validFormats.push(...acceptedFormats);
//     });
  
//     const selectedFile = event.target.files[0];
    
//     if (validateAndUpload(selectedFile, validFormats)) {
//         // Handle valid file upload
//     }
// });
