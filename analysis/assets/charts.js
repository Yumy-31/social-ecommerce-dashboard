(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var success = style.getPropertyValue('--success').trim();
  var danger = style.getPropertyValue('--danger').trim();
  var warning = style.getPropertyValue('--warning').trim();

  // --- Chart 1: 7 Paths Final Conversion Rate ---
  var chart1 = echarts.init(document.getElementById('chart-paths'), null, { renderer: 'svg' });
  chart1.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      formatter: function(params) {
        var p = params[0];
        return p.name + '<br/>购买人数: ' + p.value + ' 人<br/>总转化率: ' + (p.value / 1000).toFixed(2) + '%';
      }
    },
    grid: { left: '45%', right: '12%', top: '5%', bottom: '5%' },
    xAxis: {
      type: 'value',
      axisLabel: { color: muted, fontSize: 11, formatter: '{value}人' },
      splitLine: { lineStyle: { color: rule } },
      axisLine: { show: false }
    },
    yAxis: {
      type: 'category',
      data: [
        '路径1 完整六步',
        '路径4 加购→领券→用券→购买',
        '路径7 互动→领券→用券→购买',
        '路径3 领券→用券→购买',
        '路径6 互动→加购→购买',
        '路径2 加购→购买',
        '路径5 互动→购买'
      ],
      axisLabel: { color: ink, fontSize: 11 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: [
        { value: 2473, itemStyle: { color: muted } },
        { value: 2621, itemStyle: { color: muted } },
        { value: 7890, itemStyle: { color: accent2 } },
        { value: 8388, itemStyle: { color: accent2 } },
        { value: 17052, itemStyle: { color: accent2 } },
        { value: 18090, itemStyle: { color: accent2 } },
        { value: 42575, itemStyle: { color: accent } }
      ],
      barWidth: '55%',
      label: {
        show: true,
        position: 'right',
        color: ink,
        fontSize: 11,
        fontWeight: 600,
        formatter: function(params) {
          return params.value.toLocaleString() + '人';
        }
      }
    }]
  });
  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: 6 Dimensions Impact Ranking ---
  var chart2 = echarts.init(document.getElementById('chart-lift'), null, { renderer: 'svg' });
  chart2.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      formatter: function(params) {
        var p = params[0];
        var ranges = [
          ['+7.2%', '-4.6%', '11.8pp'],
          ['+6.7%', '-2.7%', '9.4pp'],
          ['+1.7%', '-2.8%', '4.5pp'],
          ['+0.6%', '-1.1%', '1.7pp'],
          ['+0.3%', '-0.6%', '0.9pp'],
          ['+0.2%', '-0.1%', '0.3pp']
        ];
        var r = ranges[p.dataIndex];
        return p.name + '<br/>最高: ' + r[0] + ' · 最低: ' + r[1] + '<br/>极差: ' + r[2];
      }
    },
    grid: { left: '22%', right: '12%', top: '5%', bottom: '5%' },
    xAxis: {
      type: 'value',
      axisLabel: { color: muted, fontSize: 11, formatter: '{value}pp' },
      splitLine: { lineStyle: { color: rule } },
      axisLine: { show: false },
      max: 13
    },
    yAxis: {
      type: 'category',
      data: ['有无视频', '商品品类', '标题长度', '浏览次数', '折扣率', '点击时隔'],
      axisLabel: { color: ink, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false },
      inverse: false
    },
    series: [{
      type: 'bar',
      data: [
        { value: 0.3, itemStyle: { color: muted, opacity: 0.5 } },
        { value: 0.9, itemStyle: { color: muted, opacity: 0.6 } },
        { value: 1.7, itemStyle: { color: accent2, opacity: 0.7 } },
        { value: 4.5, itemStyle: { color: accent2 } },
        { value: 9.4, itemStyle: { color: accent } },
        { value: 11.8, itemStyle: { color: accent } }
      ],
      barWidth: '55%',
      label: {
        show: true,
        position: 'right',
        color: ink,
        fontSize: 12,
        fontWeight: 600,
        formatter: '{c}pp'
      }
    }]
  });
  window.addEventListener('resize', function() { chart2.resize(); });

  // --- Chart 3: >50% Discount by Category ---
  var chart3 = echarts.init(document.getElementById('chart-discount'), null, { renderer: 'svg' });
  chart3.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      appendToBody: true,
      formatter: function(params) {
        var p = params[0];
        var color = p.value >= 0 ? success : danger;
        return p.name + '<br/>>50%折扣偏离度: <span style="color:' + color + ';font-weight:600">' + p.value + '%</span>';
      }
    },
    grid: { left: '15%', right: '10%', top: '12%', bottom: '5%' },
    xAxis: {
      type: 'value',
      axisLabel: { color: muted, fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: rule } },
      axisLine: { show: false },
      min: -16,
      max: 6
    },
    yAxis: {
      type: 'category',
      data: ['家居日用', '美妆个护', '其他', '食品生鲜', '数码家电', '服饰鞋包', '大盘聚合'],
      axisLabel: { color: ink, fontSize: 12 },
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false }
    },
    series: [{
      type: 'bar',
      data: [
        { value: -14.3, itemStyle: { color: danger } },
        { value: -10.0, itemStyle: { color: danger } },
        { value: -6.9, itemStyle: { color: danger, opacity: 0.7 } },
        { value: -1.2, itemStyle: { color: warning, opacity: 0.6 } },
        { value: 3.2, itemStyle: { color: success, opacity: 0.7 } },
        { value: 4.7, itemStyle: { color: success } },
        { value: -1.1, itemStyle: { color: muted } }
      ],
      barWidth: '55%',
      markLine: {
        symbol: 'none',
        data: [{ xAxis: 0 }],
        lineStyle: { color: ink, type: 'dashed', width: 1.5 },
        label: { show: false }
      },
      label: {
        show: true,
        position: function(params) {
          return params.value >= 0 ? 'right' : 'left';
        },
        color: ink,
        fontSize: 11,
        fontWeight: 600,
        formatter: function(params) {
          return (params.value >= 0 ? '+' : '') + params.value + '%';
        }
      }
    }]
  });
  window.addEventListener('resize', function() { chart3.resize(); });
})();
