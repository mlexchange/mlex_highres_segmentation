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
        resize_canvas: function(metadata, figure) {
            let h = metadata.size[0];
            let w = metadata.size[1];
            let W = window.innerWidth;
            let H = window.innerHeight;
            let screen_ratio = W/H;  
            let img_ratio = w/h;
            if (w<=W && h<=H){
                figure.layout.xaxis.range[1] = W-(W-w)/2;
                figure.layout.xaxis.range[0] = -(W-w)/2;
                figure.layout.yaxis.range[1] = H-(H-h)/2;
                figure.layout.yaxis.range[0] = -(H-h)/2;
            }else if(w>W){
                if(img_ratio<=screen_ratio){

                    figure.layout.xaxis.range[1] = h*screen_ratio - h*(screen_ratio-img_ratio)/2;
                    figure.layout.xaxis.range[0] = - h*(screen_ratio-img_ratio)/2;
                    figure.layout.yaxis.range[1] = h;
                    figure.layout.yaxis.range[0] = 0;
                }else{
                    figure.layout.xaxis.range[1] = w;
                    figure.layout.xaxis.range[0] = 0;
                    figure.layout.yaxis.range[1] = w/screen_ratio - w*(1/screen_ratio-1/img_ratio)/2;
                    figure.layout.yaxis.range[0] = - w*(1/screen_ratio-1/img_ratio)/2;
                }
            }else if (w<W && h>H){   
                if(w>=h){
                    figure.layout.xaxis.range[1] = w*(screen_ratio/img_ratio) - h*(screen_ratio-img_ratio)/2;
                    figure.layout.xaxis.range[0] = 0 - h*(screen_ratio-img_ratio)/2;
                    figure.layout.yaxis.range[1] = h;
                    figure.layout.yaxis.range[0] = 0;
                }else{
                    figure.layout.xaxis.range[1] = w*(screen_ratio/img_ratio) - h*(screen_ratio-img_ratio)/2;
                    figure.layout.xaxis.range[0] = 0 - h*(screen_ratio-img_ratio)/2;
                    figure.layout.yaxis.range[1] = h;
                    figure.layout.yaxis.range[0] = 0;
                }
            }
            return figure;
        },
    }
});