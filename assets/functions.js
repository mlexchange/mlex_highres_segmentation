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
            return {'W': W, 'H':H}
        },
        delete_active_shape: function(_, pressed_key) {
            console.log(pressed_key)
            console.log(_)
            if (_["key"] == "Backspace") {
                console.log("Deleting!")
                var gd = document.getElementsByClassName('js-plotly-plot')[0];
                Plotly.deleteActiveShape(gd);
                
            }
            return dash_clientside.no_update
        }
    }
});