function changeBrightness(js_path, brightness) {
    const element = document.querySelector(js_path);
    if (element) {
        // Apply the new brightness value to the element
        element.style.filter = `brightness(${brightness}%)`;
    }
}