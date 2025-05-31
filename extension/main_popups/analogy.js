$(document).ready(function() {
    $('.show_ana').click(function(){
        $('.analogy_box').removeClass("hide");
        $('.analogy_box').addClass("show");
    });
    $('.cross').click(function(){
        $('.analogy_box').addClass("hide");
        $('.analogy_box').removeClass("show");
    });
});