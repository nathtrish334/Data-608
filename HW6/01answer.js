d3.csv('ue_industry.csv', data => {

    console.log(data);
              
    const xScale = d3.scaleLinear()
        .domain(d3.extent(data, d => +d.index))
        .range([20, 1180]);

                  
    const yScale = d3.scaleLinear()
        .domain(d3.extent(data, d => +d.Agriculture))
        .range([580, 20]);   

                
                   
        var line = d3.line()
            .x(d => xScale(+d.index))
            .y(d => yScale(+d.Agriculture))
            .curve(d3.curveCardinal);
        
        d3.select('#answer1')
            .append('path')
            .attr('d', line(data))
            .attr('stroke', 'black')
    
});