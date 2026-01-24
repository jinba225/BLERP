// ===== 复制这个脚本到 Console 运行 =====
// HiPrint 明细项循环诊断

(function() {
    console.clear();
    console.log('%c=== HiPrint 明细项循环诊断 ===', 'color: #3b82f6; font-size: 16px; font-weight: bold');

    // 1. 检查模板配置
    console.log('\n%c1. 检查模板配置', 'color: #10b981; font-weight: bold');
    var json = hiprintTemplate.getJson();
    var elements = json.panels[0].printElements;

    var itemFields = elements.filter(function(e) {
        return e.options && e.options.field && e.options.field.indexOf('items.#.') === 0;
    });

    console.log('  明细项字段数量:', itemFields.length);

    if (itemFields.length === 0) {
        console.error('❌ 画布中没有明细项字段！');
        console.log('解决方法: 从左侧拖拽"📦 明细项字段"到画布');
        return;
    }

    console.log('  明细项字段详情:');
    itemFields.forEach(function(f, i) {
        console.log('    ' + (i+1) + '.', {
            field: f.options.field,
            type: f.printElementType ? f.printElementType.type : 'unknown',
            testData: f.options.testData,
            title: f.options.title
        });
    });

    // 2. 检查 HiPrint 版本和能力
    console.log('\n%c2. 检查 HiPrint 能力', 'color: #10b981; font-weight: bold');
    console.log('  HiPrint 版本:', hiprint.version || '未知');
    console.log('  PrintTemplate 方法:', Object.keys(hiprintTemplate).slice(0, 10));

    // 3. 测试明细项循环
    console.log('\n%c3. 测试明细项循环渲染', 'color: #10b981; font-weight: bold');

    var testData = getSampleData();
    console.log('  测试数据包含 ' + testData.items.length + ' 条明细');

    // 获取预览 HTML
    try {
        var htmlContent = hiprintTemplate.getHtml(testData);
        console.log('  生成的 HTML 长度:', htmlContent.length);

        // 检查 HTML 中是否包含明细数据
        var hasItem1 = htmlContent.indexOf('光纤激光器') > -1;
        var hasItem2 = htmlContent.indexOf('激光切割机') > -1;
        var hasItem3 = htmlContent.indexOf('防护眼镜') > -1;
        var hasItem4 = htmlContent.indexOf('安装调试') > -1;

        console.log('  HTML 中包含的明细数据:');
        console.log('    光纤激光器:', hasItem1 ? '✅' : '❌');
        console.log('    激光切割机:', hasItem2 ? '✅' : '❌');
        console.log('    防护眼镜:', hasItem3 ? '✅' : '❌');
        console.log('    安装调试:', hasItem4 ? '✅' : '❌');

        if (!hasItem1 && !hasItem2 && !hasItem3 && !hasItem4) {
            console.error('\n%c❌ 问题发现：HTML 中没有任何明细数据！', 'color: #ef4444; font-weight: bold');
            console.log('这说明 HiPrint 没有正确处理 items.#. 字段');
            console.log('\n可能的原因:');
            console.log('  1. HiPrint 版本不支持 items.#. 语法');
            console.log('  2. 需要使用表格类型而不是文本类型');
            console.log('  3. 需要特殊配置启用循环功能');
        } else if (hasItem1 && !hasItem2) {
            console.warn('\n%c⚠️ 问题发现：只显示第一条明细！', 'color: #f59e0b; font-weight: bold');
            console.log('这说明循环功能没有启用，只渲染了第一条数据');
        } else if (hasItem1 && hasItem2 && hasItem3 && hasItem4) {
            console.log('\n%c✅ HTML 包含所有明细数据！', 'color: #10b981; font-weight: bold');
            console.log('问题可能在打印窗口的渲染');
        }

        // 显示 HTML 片段
        console.log('\n生成的 HTML 片段（前 500 字符）:');
        console.log(htmlContent.substring(0, 500));

    } catch (e) {
        console.error('获取 HTML 失败:', e);
    }

    // 4. 输出完整模板 JSON
    console.log('\n%c4. 完整模板 JSON', 'color: #10b981; font-weight: bold');
    console.log('复制以下 JSON 并保存，以便分析:');
    console.log(JSON.stringify(json, null, 2));

    console.log('\n%c=== 诊断完成 ===', 'color: #3b82f6; font-size: 16px; font-weight: bold');
})();
