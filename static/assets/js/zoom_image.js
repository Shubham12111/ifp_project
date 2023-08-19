function openModal(url, type) {
    var modal = document.getElementById("fra-image-view-modal");
    var modalContent = document.getElementById("modal-content-inner");
    debugger;
    if (type === 'video') {
        modalContent.innerHTML = '<video controls class="rounded-3" for="video-for-fra-video-view-modal"><source src="' + url + '" type="video/mp4"></video>';
    } else {
        modalContent.innerHTML = '<img src="' + url + '" class="rounded-3" for="image-for-fra-image-view-modal" alt="Image">';
    }

    modal.style.display = "block";
}

function closeModal() {
    var modal = document.getElementById("fra-image-view-modal");
    modal.style.display = "none";
}