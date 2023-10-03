function changeFilters(js_path, brightness, contrast) {
    const element = document.querySelector(js_path);
    if (element) {
        // Apply the new brightness value to the element
        element.style.filter = `brightness(${brightness}%) contrast(${contrast}%)`;
        element.style.webkitFilter = `brightness(${brightness}%) contrast(${contrast}%)`;
    }
}



window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        get_container_size: function(url) {
            let W = window.innerWidth;
            let H = window.innerHeight;
            if(W == 0 || H == 0){
                return dash_clientside.no_update
            }
            // keep `remove_focus()` here or add it to a separate callback if necessary
            // so that it executes ONCE at when the app loads
            remove_focus();
            return {'W': W, 'H':H}
        }

    }
});

/**
 * Removes focus from the "image-selection-slider" container and its children.
 * This is necessary to prevent the slider from moving by "two steps" when
 * the user clicks on the slider, and then immediately uses the arrow keys.
 */
function remove_focus() {
    const sliderContainer = document.getElementById('image-selection-slider');
    
    sliderContainer.addEventListener('focus', () => {
        sliderContainer.blur();
    });
    
    sliderContainer.addEventListener('blur', () => {
        sliderContainer.blur();
    });
}