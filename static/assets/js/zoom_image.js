document.addEventListener("DOMContentLoaded", function () {
    const zoomableMedia = document.querySelectorAll(".zoomable-media");

    zoomableMedia.forEach(mediaContainer => {
        let currentScale = 1;
        let isDragging = false;
        let startX;
        let startY;
        let translateX = 0;
        let translateY = 0;

        const media = mediaContainer.querySelector("img, video");
        const zoomInButton = mediaContainer.querySelector(".zoom-in-button");
        const zoomOutButton = mediaContainer.querySelector(".zoom-out-button");
        const resetButton = mediaContainer.querySelector(".reset-button");

        zoomInButton.addEventListener("click", function () {
            currentScale += 0.1;
            applyZoom();
        });

        zoomOutButton.addEventListener("click", function () {
            currentScale = Math.max(0.1, currentScale - 0.1);
            applyZoom();
        });

        resetButton.addEventListener("click", function () {
            currentScale = 1;
            translateX = 0;
            translateY = 0;
            applyZoom();
        });

        mediaContainer.addEventListener("mousedown", e => {
            if (currentScale > 1) {
                isDragging = true;
                startX = e.clientX - mediaContainer.getBoundingClientRect().left;
                startY = e.clientY - mediaContainer.getBoundingClientRect().top;
            }
        });

        document.addEventListener("mousemove", e => {
            if (isDragging) {
                const newX = e.clientX - mediaContainer.getBoundingClientRect().left;
                const newY = e.clientY - mediaContainer.getBoundingClientRect().top;
                translateX += newX - startX;
                translateY += newY - startY;
                applyZoom();
                startX = newX;
                startY = newY;
            }
        });

        document.addEventListener("mouseup", () => {
            isDragging = false;
        });

        function applyZoom() {
            media.style.transform = `scale(${currentScale}) translate(${translateX}px, ${translateY}px)`;
        }
    });
});

