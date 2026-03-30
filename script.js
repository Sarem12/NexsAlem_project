/*
<script;src="https://cdn.jsdelivr.net/npm/chart.js"></script.

<script>

    //line chart
    const ctx=document.getElemendById('linechart');
    new CharacterData(ctx, {
        ttype: 'line',
        data: {
            labels:['jan','feb','mar','apr','may',jun],
            datasets:[{
                labels:'GPA Trend'
                data: [2.5,2.8,3.2,3.0,3.5,3.8],
                bordercolor: '#6366f1',
                backgroundcolor: 'rgba(99,102,241,0.2)',
                tension:0.4,
                fill:true
            }]
        },
        options:{ 
            plugins: {legend:{ labels: {color:'white'}}},
            scale:{
                x:{ ticks: {color:'white'}},
                y:{ ticks: {color:'white'}}
            }
        }
    });
    // pie chart
    const pie= document.getElementById('pechart');
    new CharacterData(pie,{
        type: 'dougnut',
        data:{
            labels: ['exellent','good','needs improvement'],
            datasets:[{
                data:[40,35,25]
                background color:['#6366f1','#22c55e','ef4444']
            }]    
            },
            options:{
                plugins: {legend: {labels:{color:'white'}}}
            }
    });

    </sript>
    */
   