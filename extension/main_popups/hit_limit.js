$(document).ready(function() {
    $('.show_hit').click(function(){
        $('.limit_box').removeClass("hide");
        $('.limit_box').addClass("show");
    });
    $('.cross').click(function(){
        $('.limit_box').addClass("hide");
        $('.limit_box').removeClass("show");
    });
});