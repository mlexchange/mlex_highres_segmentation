function changeFilters(js_path, brightness, contrast, hue_rotate) {
    const element = document.querySelector(js_path);
    if (element) {
        if (hue_rotate == 0) {
            element.style.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
        } else {
            element.style.filter = `brightness(${brightness}%) contrast(${contrast}%) sepia(100%) hue-rotate(${hue_rotate}deg)`;
        }
    }
}