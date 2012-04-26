$(document).ready(function($) {
 $('#loading').hide().ajaxStart(function() {
	$(this).show();
}).ajaxStop(function() {
	$(this).hide();
});

$('#nike_account_sync').click(function() {
	var nike_id = $('#id_nike_id').val();
	var nike_password = $('#id_nike_password').val();
	//var url = 'http://www.allanwhatmough.com/testapp/?callback=?' + '&nike_id=' + nike_id + '&nike_password=' + nike_password; 
        var url = '/runs/my_test/?nike_id=' + nike_id + '&nike_password=' + nike_password; 
        // TODO: handle error case e.g. if it times out trying to fetch URL
	$.getJSON(url, function(data) {
		$('#foo').html(data);
		data += "" // to convert it to a string
		$('#id_nike_user_id').val(data);
	});

});
});

/*$('#nike_account_sync').click(function() {
	$.getJSON('http://www.allanwhatmough.com/testapp/', function(data){
		$('#foo').html(data);
	});
})
});*/

/*(function($) {
  $('#nike_account_sync').live('click', function() {
    $(this).append(' Click!');
  });
})(jQuery);*/

/*$('#nike_account_sync').hide().ajaxStart(function() {
	$(this).show();
}).ajaxStop(function() {
	$(this).hide();
});*/
