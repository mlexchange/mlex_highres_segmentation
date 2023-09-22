function changeFilters(js_path, brightness, contrast) {
    const element = document.querySelector(js_path);
    if (element) {
        // Apply the new brightness value to the element
        element.style.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
        element.style.webkitFilter = `brightness(${brightness}%) contrast(${contrast}%)`;
    }
}



