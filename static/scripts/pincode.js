$(document).on('keyup', '#pincode', function () {
    let pincode = $(this).val();
    $("#district").html("");
    var str = '';
    console.log('A');
    if (pincode.length >= 6) {
        console.log('B');
        $.get(`https://api.postalpincode.in/pincode/${pincode}`, function (res) {
            console.log(res);
            const { Message, PostOffice, Status } = res[0];
            
            PostOffice.forEach(function (item) {
                str += `<option value="${item.Name}">${item.Name}</option>`               
            })
            $("#district").html(str);
        });
    }else{
        console.log('C');
        $("#district").html("");
    }
    // x.add(option);
})

