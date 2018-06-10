var datasChart = [];
var timeT = (new Date()).getTime();
var Handler = null;
var twoCHartData = [];
var twoCHartDataTwo = [];
//var seriesChartOne = null;
var testXren = null;


for (var i = -10; i <= 0; i += 1) {
    datasChart.push([
        timeT + i * 1000,
        Math.random()
    ]);
}

var optionsChart = {
        chart: {
            type: 'area',
            animation: Highcharts.svg, // don't animate in old IE
            marginRight: 25,
            selectionMarkerFill: '#000',
            height: 500,
            events: {
                load: function(){
                    // set up the updating of the chart each second
                    var seriesChartOne = this.series[0];
                    var yAxis = this.yAxis[0];
                    setInterval(function () {
                        var x=null, y=null;
                        if (window.dataChartCurrent == -9999) {
                            x = (new Date()).getTime();
                            y = Math.random();
                        }
                        else{
                            x = (new Date()).getTime();
                            y = window.dataChartCurrent;
                        }
                        yAxis.removePlotLine('lineHoverChartOne');
                        yAxis.addPlotLine({
                            color: '#000',
                            id: 'lineHoverChartOne',
                            value: y,
                            width: 1,
                            label: {style: {'color': 'red'}}
                        });
                        seriesChartOne.addPoint([x, y], true, true);
                        
                    }, 1000);
                }
            }
        },
        title: {
            text: 'All Flot'
        },
        xAxis: {
            type: 'datetime',
            tickPixelInterval: 50,
            gridLineWidth: 0,
            offset:1,
            maxPadding: 30,
            crosshair: {
                color: "#2196F3"
            }
        },
        yAxis: [{ // left y axis
                tickAmount: 10,
                title: {
                    text: null
                },
                labels: {
                    useHTML: false,
                    x: 20
                },
                gridLineWidth: 0,
                offset:1,
                showFirstLabel: true,
                showLastLabel: true,
                crosshair: {
                    color: "#2196F3"
                },
                minorGridLineColor: "#000",
                minorGridLineDashStyle: "Solid",
                minorGridLineWidth: 1,
                
                
            }, { // right y axis
                labels: {x: -30000},
            }],
        tooltip: {
            formatter: function () {
                return Highcharts.dateFormat('%Y-%m-%d %H:%M:%S', this.x) + ' (<b>' + Highcharts.numberFormat(this.y, 2) + ')</b>';
            },
        },
        legend: {
            enabled: false
        },
        exporting: {
            enabled: false
        },
        series: [{
            name: 'Price on time',
            lineColor: "#135990",
            lineWidth: 1,
            fillColor: "rgba(181, 217, 255, 0.498039)",
            marker: {enabled: false},
            
            states:{
                hover: {
                    enabled: true,
                    lineWidth: 1,
                    lineWidthPlus: 1,
                    marker: {
                        enabled: false,
                        height: 0,
                        lineWidth: 0,
                        radius: 0,
                        width: 0,
                        symbol: ""
                    }
                }
            },
            point: {
                events: {
                    // on mouseOver make the xaxis label red
                    /*mouseOver: function(){
                        var xAxis = this.series.chart.yAxis[0];
                        $(xAxis.ticks[this.y].label.element).css('fill','red');
                    },
                    // on mouseOut make it gray again
                    mouseOut: function(){
                        var xAxis = this.series.chart.yAxis[0];
                        $(xAxis.ticks[this.y])
                        $(xAxis.ticks[this.y].label.element).css('fill','#606060');
                    }*/
                }  
            },
            
            data: (function () {
                // generate an array of random data
                return window.datasChart;
            }())
        }],
        rangeSelector : {
            enabled: false
        },
        navigator: {
            enabled: false
        }
        
    };

$(function () {
    $(document).ready(function () {
        $('#companyChartContainer').highcharts('StockChart', optionsChart);
        
        // Load the fonts
		Highcharts.createElement('link', {
		   href: 'https://fonts.googleapis.com/css?family=Signika:400,700',
		   rel: 'stylesheet',
		   type: 'text/css'
		}, null, document.getElementsByTagName('head')[0]);
		Highcharts.theme = {
           colors: ["#f45b5b", "#8085e9", "#8d4654", "#7798BF", "#aaeeee", "#ff0066", "#eeaaee",
              "#55BF3B", "#DF5353", "#7798BF", "#aaeeee"],
           chart: {
              backgroundColor: null,
              style: {
                 fontFamily: "Signika, serif"
              }
           },
           title: {
              style: {
                 color: 'black',
                 fontSize: '16px',
                 fontWeight: 'bold'
              }
           },
           subtitle: {
              style: {
                 color: 'black'
              }
           },
           tooltip: {
              borderWidth: 0
           },
           legend: {
              itemStyle: {
                 fontWeight: 'bold',
                 fontSize: '13px'
              }
           },
           xAxis: {
              labels: {
                 style: {
                    color: '#6e6e70'
                 }
              }
           },
           yAxis: {
              labels: {
                 style: {
                    color: '#6e6e70'
                 }
              }
           },
           plotOptions: {
              series: {
                 shadow: true
              },
              candlestick: {
                 lineColor: '#404048'
              },
              map: {
                 shadow: false
              }
           },
        
           // Highstock specific
           navigator: {
              xAxis: {
                 gridLineColor: '#D0D0D8'
              }
           },
           rangeSelector: {
              buttonTheme: {
                 fill: 'white',
                 stroke: '#C0C0C8',
                 'stroke-width': 1,
                 states: {
                    select: {
                       fill: '#D0D0D8'
                    }
                 }
              }
           },
           scrollbar: {
              trackBorderColor: '#C0C0C8'
           },
        
           // General
           background2: '#E0E0E8'
        
        };

		// Apply the theme
		//Highcharts.setOptions(Highcharts.theme);

        
        $('#companyChartContainer2').highcharts('StockChart', optionsChart);
    });
});


function chartAjax(pk)
{
    if (window.flagAjaxChart == true) {
        toogleOverride();
        window.ajax_post("/cab/dataChart/",
            "POST",
            function (data) {
                toogleOverride();
                clearInterval(window.headler);
                reprintChart(data);
                window.pkChart = pk;
                window.headler = setInterval(function () {
                        chartAjax(window.pkChart);
                    }, 1000);
                window.flagAjaxChart = false;
            },
            function (data) {
                if (window.flagAjaxChart == true) toogleOverride();
            },
            {pk: pk, flag: true},
            "json"
        );//END AJAX
    }
    else
    {
        ajax_post("/cab/dataChart/",
            "POST",
            function (data) {
                window.dataChartCurrent = Number(data.price);
                elemet = $('#company-tr-' + pk);
                oldPrice = Number($('#company-tr-' + pk + ' td.sharePrice').text()
                    .replace('<i class="fa fa-arrow-up color-green"></i>', '')
                    .replace('<i class="fa fa-arrow-down color-red"></i>', ''));
                result = Math.round((Number(data.price) + Number(data.price)*0.01) * 100) / 100;
                //result = Math.round((result + result*0.01)*100) / 100;
                if(oldPrice > Number(window.dataChartCurrent))
                {
                    $('#company-tr-' + pk + ' td.sharePrice').html('<i class="fa fa-arrow-down color-red"></i> ' + data.price);
                    $('#company-tr-' + pk + ' td.askSharePrice').removeClass('color-red').removeClass('color-green')
                        .addClass('color-green').text(result);
                }
                
                else if(oldPrice < Number(window.dataChartCurrent))
                {
                    $('#company-tr-' + pk + ' td.sharePrice').html('<i class="fa fa-arrow-up color-green"></i> ' + data.price);
                    $('#company-tr-' + pk + ' td.askSharePrice').removeClass('color-red').removeClass('color-green')
                        .addClass('color-red').text(result);
                }
            },
            function (data) {

            },
            {pk: pk, flag: false},
            "json"
        );//END AJAX
    }
}


var pkChart = 0;
var headler = null;
var flagAjaxChart = false;

function reprintChart(datas)
{
   //$('#companyChartContainer').highcharts().destroy();

    window.datasChart = [];
    var timeTT = (new Date()).getTime();

    var qq = 0;
    for(var ii in datas.datas)
    {
        window.datasChart.push({
            x: timeTT + qq * 1000,
            y: Number(datas.datas[ii])
        });
        qq++;
    }

    $('#companyChartContainer').highcharts().setTitle({text: datas.name}, {}, false);
    //$('#companyChartContainer').highcharts().setName('Price ' + datas.name);

    $('#companyChartContainer').highcharts().redraw();
    //$('#companyChartContainer').highcharts(optionsChart);
}



function newDatasCompany()
{
    window.ajax_post("/cab/dataCompanyPrice/",
            "POST",
            function (data) {
                rePrintNewDatasCompany(data.data);
            },
            function (data) {},
            {},
            "json"
        );//END AJAX
}


function rePrintNewDatasCompany(data)
{
    for(var i in data)
    {
        oldPrice = Number($('#company-tr-' + data[i][0] + ' td.sharePrice').text()
            .replace('<i class="fa fa-arrow-up color-green"></i>', '')
            .replace('<i class="fa fa-arrow-down color-red"></i>', ''));
        result = Math.round((Number(data[i][1]) + Number(data[i][1])*0.01) * 100) / 100;
        //result = Math.round((result + result*0.01)*100) / 100;
        if(oldPrice > Number(data[i][1]))
        {
            $('#company-tr-' + data[i][0] + ' td.sharePrice').html('<i class="fa fa-arrow-down color-red"></i> ' + data[i][1]);
            $('#company-tr-' + data[i][0] + ' td.askSharePrice').removeClass('color-red').removeClass('color-green')
                .addClass('color-green').text(result);
        }
        
        else if(oldPrice < Number(data[i][1]))
        {
            $('#company-tr-' + data[i][0] + ' td.sharePrice').html('<i class="fa fa-arrow-up color-green"></i> ' + data[i][1]);
            $('#company-tr-' + data[i][0] + ' td.askSharePrice').removeClass('color-red').removeClass('color-green')
                .addClass('color-red').text(result);
        }
    }
}


$(document).ready(function() {
    setInterval(newDatasCompany, 5000);
});


function PrintColumnRange()
{   
    var options = {
        chart: {
            
            animation: Highcharts.svg, // don't animate in old IE
            height: 500,
            events: {
                load: function(){
                    //var seriesChartTwo = this.series[0];
                    //setInterval(function () {seriesChartTwo.addPoint(window.twoCHartData, true, true);}, 5000);
                    var yAxis = this.yAxis[0];
                    yAxis.removePlotLine('lineHoverChartTwo');
                    var minmin = -1000;
                    if(window.twoCHartData[1] > window.twoCHartData[3])minmin = window.twoCHartData[3];
                    else minmin = window.twoCHartData[1];
                    yAxis.addPlotLine({
                        color: '#000',
                        id: 'lineHoverChartTwo',
                        value: minmin,
                        width: 1
                    });
                    
                }
            }
        },
        navigator: {
            enabled: false
        },
        rangeSelector: {
            selected: 2,
            enabled: false
        },
        title: {
            text: ""
        },
        xAxis: {
        	type: 'datetime',
        	tickPixelInterval: 10,
        	maxPadding: 0.05,
        	gridLineWidth: 0,
        	offset:1,
        	crosshair: {
                color: "#2196F3"
            }
        },
        yAxis: [{ // left y axis
                title: {
                    text: null
                },
                labels: {
                    align: 'left',
                    x: 10,
                    y: 16,
                    format: '{value:.,0f}'
                },
                crosshair: {
                    color: "#2196F3"
                },
                showFirstLabel: false,
                gridLineWidth: 0,
                offset:1
            }, {labels: {x: -3000}}],
            legend: {
		        enabled: false
		    },
		    exporting: {
		        enabled: false
		    },
        series: [{
            name: 'Shares',
            type: 'candlestick',
            data: window.twoCHartDataTwo
        }],
        plotOptions:{
            candlestick:{
                color: "#fe3232",
                upColor:"#32ea32"
            }
        }
    };
    
    //$('#companyChartContainer').highcharts().destroy();
    //try{$('#companyChartContainer2').highcharts().setTitle({text: 'Company ' + company}, {}, false);}
    //catch(e){};
    //try{$('#companyChartContainer2').highcharts('StockChart', options).redraw();}
    $('#companyChartContainer2').highcharts('StockChart', options);
}


function lastShapePrice(pk)
{
    window.ajax_post("/cab/dataChartTwoOneLement/",
        "POST",
        function (data) {
            _exp = new Date();
            _date = _exp.getHours() + ':' + _exp.getMinutes() + ':' + _exp.getSeconds();
            window.twoCHartData = [_exp.getTime(), Number(data.data[0]), Number(data.data[1]), Number(data.data[2]), Number(data.data[3])];
            window.twoCHartDataTwo.unshift([_exp.getTime(), Number(data.data[0]), Number(data.data[1]), Number(data.data[2]), Number(data.data[3])]);
            //$('#companyChartContainer2').highcharts().series.data = window.twoCHartDataTwo;
            //$('#companyChartContainer2').highcharts().redraw();
            //$('#companyChartContainer2').highcharts('StockChart', options);
            $('#companyChartContainer2').highcharts().destroy();
            PrintColumnRange();
            console.log('asdsa');
        },
        function (data) {
        },
        {pk: pk},
        "json"
    );//END AJAX
}


function AjaxColumnRange(pk) 
{
    window.ajax_post("/cab/dataChartTwo/",
        "POST",
        function (data) {
            $('.company-chart .nav-tabs').css('display', 'block');
            window.twoCHartDataTwo = [];
            for(var i in data.data){
                _exp = data.data[i][0].split(':');
                _date = new Date(_exp[0], _exp[1], _exp[2], _exp[3], _exp[4], _exp[5], 0);
                window.twoCHartDataTwo.push([_date.getTime(), Number(data.data[i][1]), Number(data.data[i][2]), Number(data.data[i][3]), Number(data.data[i][4])]);
                window.twoCHartData = [_date.getTime(), Number(data.data[i][1]), Number(data.data[i][2]), Number(data.data[i][3]), Number(data.data[i][4])];
            }
            $('#companyChartContainer2').highcharts().destroy();
            clearInterval(window.Handler);
            window.Handler = setInterval(function() {lastShapePrice(pk);}, 5000);
            PrintColumnRange();//data.data, data.company);
        },
        function (data) {
        },
        {pk: pk},
        "json"
    );//END AJAX
}

$(document).ready(function() {
    //AjaxColumnRange(window.pkChartTwo);
});