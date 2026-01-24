// ===== 打印页面明细项诊断脚本 =====
// 复制这个脚本到打印页面的 Console 中运行

(function() {
    console.clear();
    console.log('%c=== 打印页面明细项诊断 ===', 'color: #3b82f6; font-size: 16px; font-weight: bold');

    // 1. 检查数据
    console.log('\n%c1. 检查报价单数据', 'color: #10b981; font-weight: bold');
    if (typeof quoteData === 'undefined') {
        console.error('❌ quoteData 未定义！');
        return;
    }
    console.log('  报价单号:', quoteData.quote_number);
    console.log('  items 是数组:', Array.isArray(quoteData.items));
    console.log('  items 数量:', quoteData.items ? quoteData.items.length : 0);

    if (quoteData.items && quoteData.items.length > 0) {
        console.log('\n  明细项数据:');
        console.table(quoteData.items);
    } else {
        console.error('❌ 没有明细项数据！');
        return;
    }

    // 2. 检查模板
    console.log('\n%c2. 检查模板实例', 'color: #10b981; font-weight: bold');
    if (typeof hiprintTemplate === 'undefined') {
        console.error('❌ hiprintTemplate 未定义！');
        return;
    }
    console.log('  hiprintTemplate:', hiprintTemplate);

    var json = hiprintTemplate.getJson();
    console.log('  模板 panels 数量:', json.panels ? json.panels.length : 0);

    if (json.panels && json.panels[0]) {
        var elements = json.panels[0].printElements || [];
        console.log('  模板元素总数:', elements.length);

        // 找出明细项字段
        var itemFieldConfigs = elements.filter(function(elem) {
            return elem.options && elem.options.field &&
                   (elem.options.field.startsWith('items.#.') || elem.options.field.startsWith('items.'));
        });

        console.log('  明细项字段数量:', itemFieldConfigs.length);

        if (itemFieldConfigs.length > 0) {
            console.log('\n  明细项字段配置:');
            itemFieldConfigs.forEach(function(config, i) {
                console.log('    ' + (i+1) + '. field:', config.options.field);
                console.log('       title:', config.options.title);
                console.log('       top:', config.options.top);
                console.log('       left:', config.options.left);
                console.log('       testData:', config.options.testData);
            });
        } else {
            console.warn('⚠️ 模板中没有明细项字段！');
            console.log('\n💡 解决方法:');
            console.log('   1. 访问模板编辑器');
            console.log('   2. 从左侧元素库拖拽\"📦 明细项字段\"到画布');
            console.log('   3. 保存模板后重新测试');
        }
    }

    // 3. 检查渲染的 DOM
    console.log('\n%c3. 检查渲染的 DOM 元素', 'color: #10b981; font-weight: bold');
    var $allElements = $('.hiprint-printElement');
    console.log('  页面上的 HiPrint 元素总数:', $allElements.length);

    // 检查是否有明细项字段的 DOM 元素
    var $itemFieldElements = $allElements.filter(function() {
        var $elem = $(this);
        var dataField = $elem.attr('data-field');
        var field = $elem.attr('field');
        var options = $elem.data('options');
        var dataFieldProp = $elem.data('field');

        return (dataField && (dataField.startsWith('items.#.') || dataField.startsWith('items.'))) ||
               (field && (field.startsWith('items.#.') || field.startsWith('items.'))) ||
               (options && options.field && (options.field.startsWith('items.#.') || options.field.startsWith('items.'))) ||
               (dataFieldProp && (dataFieldProp.startsWith('items.#.') || dataFieldProp.startsWith('items.')));
    });

    console.log('  明细项字段 DOM 元素数量:', $itemFieldElements.length);

    if ($itemFieldElements.length > 0) {
        console.log('\n  明细项字段 DOM 元素:');
        $itemFieldElements.each(function(i) {
            var $elem = $(this);
            console.log('    ' + (i+1) + '. 内容:', $elem.text().substring(0, 50));
            console.log('       data-field:', $elem.attr('data-field'));
            console.log('       field:', $elem.attr('field'));
            console.log('       位置:', $elem.css('top'), $elem.css('left'));
        });
    } else {
        console.warn('⚠️ 页面上没有明细项字段 DOM 元素！');
    }

    // 4. 检查 processItemFieldsLoop 是否执行
    console.log('\n%c4. 检查循环处理函数', 'color: #10b981; font-weight: bold');
    if (typeof processItemFieldsLoop === 'function') {
        console.log('  ✅ processItemFieldsLoop 函数存在');
        console.log('\n  尝试手动调用 processItemFieldsLoop()...');
        try {
            processItemFieldsLoop();
            console.log('  ✅ 函数执行完成，请查看上面的日志');
        } catch (e) {
            console.error('  ❌ 函数执行失败:', e);
        }
    } else {
        console.error('  ❌ processItemFieldsLoop 函数不存在！');
    }

    // 5. 总结
    console.log('\n%c5. 诊断结果', 'color: #f59e0b; font-weight: bold');

    var hasData = quoteData.items && quoteData.items.length > 0;
    var hasConfig = json.panels && json.panels[0] &&
                    json.panels[0].printElements.some(function(e) {
                        return e.options && e.options.field &&
                               (e.options.field.startsWith('items.#.') || e.options.field.startsWith('items.'));
                    });
    var hasDOM = $itemFieldElements.length > 0;

    if (!hasData) {
        console.log('  ❌ 问题: 没有明细项数据');
    } else if (!hasConfig) {
        console.log('  ❌ 问题: 模板中没有配置明细项字段');
        console.log('  💡 解决: 在模板编辑器中添加明细项字段');
    } else if (!hasDOM) {
        console.log('  ❌ 问题: 明细项字段没有渲染到页面');
        console.log('  💡 可能原因:');
        console.log('     1. getHtml() 方法没有正确处理明细项字段');
        console.log('     2. 模板保存有问题');
        console.log('     3. HiPrint 版本问题');
    } else {
        console.log('  ✅ 基础检查通过');
        console.log('  💡 如果仍然没有显示，请查看上面步骤4的日志');
    }

    console.log('\n%c=== 诊断完成 ===', 'color: #3b82f6; font-size: 16px; font-weight: bold');
})();
