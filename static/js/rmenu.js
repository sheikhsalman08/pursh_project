var dataChartCurrent = -9999;


function toogleOverride()   //меняем состояние визуального загрузчика
{
    if($('.loadFade').css('display') == 'none'){
        $('.loadFade').css('display','block');
        $('.circleLoad').css('display','block');
        $('.circleLoad1').css('display','block');
    }
    else{
        $('.loadFade').css('display','none');
        $('.circleLoad').css('display','none');
        $('.circleLoad1').css('display','none');
    }
}

//общая функция ajax запроса
function ajax_post(url, //URL куда
                   type, //Тип запроса
                   succ, //Функция при успехе
                   eror, //Функция при неудаче
                   data, //Данные
                   dataType //Тип возвращаемого значения
                   )
{
    //Сам код
    $.ajax({
        url: url,
        type: type,
        data: data,
        dataType:dataType,
        success: function(data){    succ(data);     },
        error: function(data) {     eror(data);     },
        // CSRF механизм защиты Django
        beforeSend: function(xhr, settings) {
            console.log('-------------before send--');
            function getCookie(name) {
                var cookieValue = null;
                if (document.cookie && document.cookie != '') {
                    var cookies = document.cookie.split(';');
                    for (var i = 0; i < cookies.length; i++) {
                        var cookie = jQuery.trim(cookies[i]);
                        // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
            }
            if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
                // Only send the token to relative URLs i.e. locally.
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });// ajax
}//КОнец общего AJAX


function buyShowBox(pk, companyname)
{
    $('#id_companyPk_buy').val(pk);
    $('#CNSBSB').html('How many shares of the company "'+companyname+'" you want to buy?');
    $('#buyShares form').attr('action', $('#id_buyUrl').val());
    $('#buyShares').modal('show');
}

function sellShowBox(pk, companyname)
{
    $('#id_companyPk_sell').val(pk);
    $('#CNSBSB').html('How many shares of the company "'+companyname+'" you want to sell?');
    $('#sellShares form').attr('action', $('#id_sellUrl').val());
    $('#sellShares').modal('show');
}




function reprintNews(data, companyname)
{
    $('div.news-body').empty();
    $('h3.news-title').text('Market News "' + companyname + '"');
    for(var i in data.news)
    {
        $('div.news-body').append("<p>"+data.news[i][0]+" : "+data.news[i][1]+"</p>");
    }
}




function viewCompany(pk, companyname)
{
    toogleOverride();
    ajax_post("/cab/dataNews/",
              "POST",
              function(data){toogleOverride(); if(data.result == 'success') reprintNews(data, companyname);},
              function(data){toogleOverride();},
              {pk: pk},
              "json"
    );//END AJAX
}


function reprintInf(data)
{
    $('.CompanyPortfolioTable p[data-id="1"]').text('Company Name: ' + data.name);
    $('.CompanyPortfolioTable p[data-id="2"]').text('Current Share Price: ' + data.CSP);
    $('.CompanyPortfolioTable p[data-id="3"]').text('Total Shares Amount: ' + data.TSA);
    $('.CompanyPortfolioTable p[data-id="4"]').text('Total Shares Sold: ' + data.TSS);
    $('.CompanyPortfolioTable p[data-id="5"]').text('Total Shares Value: ' + data.TSV);
    $('.CompanyPortfolioTable p[data-id="6"]').text('Share Price: ' + data.SH);
    $('.CompanyPortfolioTable p[data-id="8"]').text('Current Share Profit (%): ' + data.CSPM);
    $('.CompanyPortfolioTable p[data-id="7"]').text('Available Shares Amount: ' + data.ASA);
}

function informationAjax(pk)
{
    toogleOverride();
    ajax_post("/cab/dataInformations/",
              "POST",
              function(data){toogleOverride(); if(data.result == 'success') reprintInf(data.inf);},
              function(data){toogleOverride();},
              {pk: pk},
              "json"
    );//END AJAX
}


$(function () {
        $('#companyTable').bootstrapTable({
            contextMenu: '#companytable-context-menu',
            onContextMenuItem: function(row, $el){

                // $('#myModal').on('hidden', function() {
                //     $(this).removeData('modal');
                // });
                if($el.data("item") == "buy"){
                    //alert("Edit: " + row.companyname + ' ' + row.bid + ' ' + row.ask);
                    buyShowBox(row.pk, row.companyname);
                }
                else if($el.data("item") == "sell"){
                    sellShowBox(row.pk, row.companyname);
                }
                else if($el.data("item") == "chart"){
                    window.flagAjaxChart = true;
                    window.dataChartCurrent = -9999;
                    window.chartAjax(row.pk);
                    window.AjaxColumnRange(row.pk);
                }
                else if($el.data("item") == "news"){
                    //alert("Action1: " + row.itemid + ' ' + row.name + ' ' + row.price);
                    viewCompany(row.pk, row.companyname);
                }
                else if($el.data("item") == "information"){
                    informationAjax(row.pk);
                }
            }
        });

    $('.HistoryTable').bootstrapTable({
        "oLanguage": { 
            "sZeroRecords":  "No Active Trades", 
        }
    });
    
    
    $('.comps div.search').removeClass('pull-right');
    
    
});