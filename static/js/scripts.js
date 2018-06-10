// function sellShare(pk, companyname)
// {
//     $('#id_companyPk_sell').val(pk);
//     $('#CNSBSBSell').html('How many shares of the company "'+companyname+'" you want to sell?');
//     // $('#sellShares form').attr('action', $('#id_sellUrl').val());
//     $('#sellShares').modal('show');
// }
// $(document).ready(function () {
//
//   $('button').click(function () {
//     var id = $(this).data('id');
//     var company = $(this).data('company');
//     sellShare(id, company);
//   });
//   $("#error").hide();
//     var buy_order = $("#buy_form");
//     var sell_order = $("#sell_form");
//      buy_order.submit(function (event) {
//
//          $.ajax({
//            type: "POST",
//            url: "{% url 'cab:buyShares' %}",
//            data: buy_order.serialize(),
//            success: function (data) {
//              if (data['error'] == undefined) {
//                $('#buyShares').modal('toggle');
//                $("#error").hide();
//              } else {
//              $("#error").show();
//              $("#error").html(data['error']);
//            }
//
//            }
//
//          });
//          event.preventDefault();
//          return false;
//
//      });
//      sell_order.submit(function (event) {
//
//          $.ajax({
//            type: "POST",
//            url: "{% url 'cab:sellShares' %}",
//            data: sell_order.serialize(),
//            success: function (data) {
//              if (data['error'] == undefined) {
//                console.log(data)
//                $('#sellShares').modal('toggle');
//              } else {
//              $("#error").show();
//              $("#error").html(data['error']);
//               }
//            }
//
//          });
//          event.preventDefault();
//          return false;
//
//      });
//  });
