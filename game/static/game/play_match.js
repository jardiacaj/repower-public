var map_click_callback = null;

$(function () {
    $("#map_image").click(function (e) {

        var offset = $(this).offset();
        var X = (e.pageX - offset.left);
        var Y = (e.pageY - offset.top);

        for (var i = 0; i < regions.length; i++) {
            var region = regions[i];
            if (X >= region.position[0] &&
                X <= region.position[0] + region.size[0] &&
                Y >= region.position[1] &&
                Y <= region.position[1] + region.size[1]) {
                if (map_click_callback != null) map_click_callback(region);
                break;
            }
        }
        ;
        map_click_callback = null;
    });
});

function enter_command_mode() {
    $('#command_type_chooser').slideUp();
    $('#command_cancel').slideDown();
}

function add_movement_click() {
    enter_command_mode();
    $('#move_token_type_chooser_step1').slideDown();
    $('#command_type').val("move");
}

function add_movement_command_step1(token_type_id) {
    $('#move_token_type_chooser_step1').slideUp();
    $('#move_token_type_chooser_step2').slideDown();
    $('#move_token_type').val(token_type_id);
    map_click_callback = add_movement_command_step2;
}

function add_movement_command_step2(region_from) {
    $('#move_token_type_chooser_step2').slideUp();
    $('#move_token_type_chooser_step3').slideDown();
    $('#move_region_from').val(region_from.id);
    map_click_callback = add_movement_command;
}

function add_movement_command(region_to) {
    $('#move_region_to').val(region_to.id);
    post_command();
}

function add_purchase_click() {
    enter_command_mode();
    $('#buy_token_type_chooser').slideDown();
    $('#command_type').val("buy");
}

function add_purchase_command(token_type_id) {
    $('#buy_token_type').val(token_type_id);
    post_command();
}

function add_conversion_click() {
    enter_command_mode();
    $('#convert_conversion_chooser_step1').slideDown();
    $('#command_type').val("convert");
}

function add_conversion_command_step1(convert_id) {
    $('#convert_conversion_chooser_step1').slideUp();
    $('#convert_conversion_chooser_step2').slideDown();
    $('#convert_id').val(convert_id);
    map_click_callback = add_conversion_command;
}

function add_conversion_command(region) {
    $('#convert_region').val(region.id);
    post_command();
}

function post_command() {
    $('#command_form').submit();
}

function command_cancel() {
    $(".chooser").slideUp();
    $('#command_type_chooser').slideDown();
}