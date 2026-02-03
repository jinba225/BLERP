/**
 * HiPrint 自定义元素提供器 - BetterLaser ERP
 * 用于报价单、订单等单据的打印模板设计
 *
 * 版本: v4.0 - 修复字段绑定问题
 * 参考: https://github.com/CcSimple/vue-plugin-hiprint
 */

// ⚠️ tid必须是固定字符串，不能包含时间戳
// 因为HTML中硬编码的tid需要与Provider注册的tid完全匹配
function generateTid(prefix) {
    return prefix;  // 直接返回prefix，不添加时间戳
}

// 定义报价单打印元素提供器
var QuoteElementProvider = function (options) {
    options = options || {};

    // Provider模块名称（用于标识元素来源）
    var providerModule = 'QuoteProvider';

    // addElementTypes方法 - HiPrint官方API要求
    var addElementTypes = function (context) {
        console.log('>>> QuoteProvider.addElementTypes 被调用 [v4.0]');

        // 移除旧的元素类型（如果存在）
        context.removePrintElementTypes(providerModule);

        // ==================== 基础元素组 ====================
        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("📝 基础元素", [
                {
                    tid: generateTid(providerModule + '.text'),
                    title: '文本',
                    data: '普通文本',
                    type: 'text',
                    options: {
                        testData: '普通文本',
                        width: 120,
                        height: 20,
                        fontSize: 12,
                        fontWeight: 'normal',
                        textAlign: 'left',
                        color: '#000000',
                        hideTitle: false
                    },
                    printElementType: {
                        title: '文本',
                        type: 'text'
                    }
                },
                {
                    tid: generateTid(providerModule + '.title'),
                    title: '标题',
                    data: '报价单',
                    type: 'text',
                    options: {
                        testData: '报价单',
                        width: 300,
                        height: 40,
                        fontSize: 24,
                        fontWeight: 'bold',
                        textAlign: 'center',
                        color: '#000000'
                    },
                    printElementType: {
                        title: '标题',
                        type: 'text'
                    }
                },
                {
                    tid: generateTid(providerModule + '.image'),
                    title: '图片',
                    type: 'image',
                    options: {
                        width: 80,
                        height: 80,
                        src: '',
                        fit: 'contain'
                    },
                    printElementType: {
                        title: '图片',
                        type: 'image'
                    }
                }
            ])
        ]);

        // ==================== 线条元素组 ====================
        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("━ 线条元素", [
                {
                    tid: generateTid(providerModule + '.hline'),
                    title: '横线',
                    type: 'hline',
                    options: {
                        width: 550,
                        height: 1,
                        borderWidth: 1,
                        borderColor: '#000000',
                        borderStyle: 'solid'
                    },
                    printElementType: {
                        title: '横线',
                        type: 'hline'
                    }
                },
                {
                    tid: generateTid(providerModule + '.vline'),
                    title: '竖线',
                    type: 'vline',
                    options: {
                        width: 1,
                        height: 100,
                        borderWidth: 1,
                        borderColor: '#000000',
                        borderStyle: 'solid'
                    },
                    printElementType: {
                        title: '竖线',
                        type: 'vline'
                    }
                }
            ])
        ]);

        // ==================== 条码元素组 ====================
        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("▦ 条码元素", [
                {
                    tid: generateTid(providerModule + '.barcode'),
                    title: '条形码',
                    field: 'quote_number',
                    type: 'barcode',
                    options: {
                        field: 'quote_number',
                        testData: 'BL-Q-20250107-001',
                        width: 200,
                        height: 60,
                        barcodeMode: 'CODE128',
                        textType: 'barcode'
                    },
                    printElementType: {
                        title: '条形码',
                        type: 'barcode',
                        field: 'quote_number'
                    }
                },
                {
                    tid: generateTid(providerModule + '.qrcode'),
                    title: '二维码',
                    field: 'quote_number',
                    type: 'qrcode',
                    options: {
                        field: 'quote_number',
                        testData: 'BL-Q-20250107-001',
                        width: 80,
                        height: 80
                    },
                    printElementType: {
                        title: '二维码',
                        type: 'qrcode',
                        field: 'quote_number'
                    }
                }
            ])
        ]);

        // ==================== 创建字段元素的辅助函数 ====================
        var createFieldElement = function(field, title, width, height, testData, align) {
            return {
                tid: generateTid(providerModule + '.field.' + field),
                title: title,
                field: field,
                type: 'text',
                options: {
                    field: field,
                    testData: testData || '示例数据',
                    width: width || 150,
                    height: height || 20,
                    fontSize: 12,
                    fontWeight: 'normal',
                    textAlign: align || 'left',
                    hideTitle: false,
                    title: title
                },
                printElementType: {
                    title: title,
                    type: 'text',
                    field: field  // ⭐ 关键：在 printElementType 中也要定义 field
                }
            };
        };

        // ==================== 报价单基本信息 ====================
        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("🔖 基本信息", [
                createFieldElement('quote_number', '报价单号', 150, 20, 'BL-Q-20250107-001'),
                createFieldElement('quote_date', '报价日期', 120, 20, '2025-01-07'),
                createFieldElement('valid_until', '有效期至', 120, 20, '2025-02-07'),
                createFieldElement('quote_type', '报价类型', 120, 20, '国内报价'),
                createFieldElement('reference_number', '参考编号', 150, 20, 'REF-001'),
                createFieldElement('sales_rep', '销售代表', 120, 20, '张三'),
                createFieldElement('print_date', '打印日期', 150, 20, '2025-01-07')
            ])
        ]);

        // ==================== 客户信息 ====================
        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("👤 客户信息", [
                createFieldElement('customer_name', '客户名称', 200, 20, '示例客户有限公司'),
                createFieldElement('customer_phone', '客户电话', 150, 20, '0755-12345678'),
                createFieldElement('customer_address', '客户地址', 300, 40, '广东省深圳市南山区'),
                createFieldElement('contact_person', '联系人', 120, 20, '李经理'),
                createFieldElement('contact_phone', '联系电话', 150, 20, '13800138000'),
                createFieldElement('contact_email', '联系邮箱', 180, 20, 'contact@example.com')
            ])
        ]);

        // ==================== 金额信息 ====================
        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("💰 金额信息", [
                createFieldElement('currency', '币种', 80, 20, 'CNY', 'center'),
                createFieldElement('exchange_rate', '汇率', 100, 20, '1.0000', 'right'),
                createFieldElement('subtotal', '小计金额', 120, 20, '10000.00', 'right'),
                createFieldElement('discount_amount', '折扣金额', 120, 20, '500.00', 'right'),
                createFieldElement('tax_amount', '税额', 120, 20, '1235.00', 'right'),
                createFieldElement('total_amount', '总金额', 150, 24, '10735.00', 'right')
            ])
        ]);

        // ==================== 条款信息 ====================
        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("📋 条款信息", [
                createFieldElement('payment_terms', '付款条款', 300, 60, '预付30%，发货前付清余款'),
                createFieldElement('delivery_terms', '交付条款', 300, 60, '下单后30-45天内交付'),
                createFieldElement('warranty_terms', '质保条款', 300, 60, '整机质保1年，核心部件质保2年'),
                createFieldElement('notes', '备注', 300, 80, '特殊要求...')
            ])
        ]);

        // ==================== 公司信息 ====================
        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("🏢 公司信息", [
                createFieldElement('company_name', '公司名称', 250, 24, 'BetterLaser科技有限公司'),
                createFieldElement('company_address', '公司地址', 300, 40, '广东省深圳市南山区科技园'),
                createFieldElement('company_phone', '公司电话', 150, 20, '0755-12345678'),
                createFieldElement('company_email', '公司邮箱', 180, 20, 'info@betterlaser.com')
            ])
        ]);

        // ==================== 明细项字段（重要！）====================
        var createItemField = function(field, title, width, height, align, testData) {
            var fullField = 'items.#.' + field;  // 明细项字段格式
            return {
                tid: generateTid(providerModule + '.itemField.' + field),
                title: title,
                field: fullField,
                type: 'text',
                options: {
                    field: fullField,  // ⭐ 明细项字段格式：items.#.field_name
                    testData: testData || '示例',
                    width: width || 80,
                    height: height || 20,
                    fontSize: 11,
                    fontWeight: 'normal',
                    textAlign: align || 'left',
                    hideTitle: true,
                    title: title,
                    borderWidth: 1,
                    borderColor: '#d1d5db',
                    borderStyle: 'solid'
                },
                printElementType: {
                    title: title,
                    type: 'text',
                    field: fullField  // ⭐ 关键：printElementType 中也要定义完整的字段路径
                }
            };
        };

        context.addPrintElementTypes(providerModule, [
            new hiprint.PrintElementTypeGroup("📦 明细项字段", [
                createItemField('index', '序号', 40, 20, 'center', '1'),
                createItemField('product_code', '产品编码', 100, 20, 'left', 'BL-LS-1000'),
                createItemField('product_name', '产品名称', 150, 20, 'left', '光纤激光器'),
                createItemField('specifications', '规格型号', 120, 20, 'left', 'IPG YLR-1000'),
                createItemField('quantity', '数量', 60, 20, 'right', '10'),
                createItemField('unit', '单位', 50, 20, 'center', '台'),
                createItemField('unit_price', '单价', 80, 20, 'right', '35000.00'),
                createItemField('discount_rate', '折扣率', 60, 20, 'center', '5%'),
                createItemField('discount_amount', '折扣金额', 80, 20, 'right', '1750.00'),
                createItemField('tax_rate', '税率', 50, 20, 'center', '13%'),
                createItemField('line_total', '小计', 90, 20, 'right', '70000.00'),
                createItemField('lead_time', '交货期', 80, 20, 'center', '30天'),
                createItemField('notes', '备注', 120, 20, 'left', '定制')
            ])
        ]);

        console.log('✅ QuoteProvider 所有元素类型已注册 [v4.0 - 修复字段绑定]');
    };

    // 返回Provider对象（符合HiPrint官方API）
    return {
        addElementTypes: addElementTypes
    };
};

// 导出到全局作用域
if (typeof window !== 'undefined') {
    window.QuoteElementProvider = QuoteElementProvider;
    console.log('✅ QuoteElementProvider 已加载 [版本: v4.0 - 修复字段绑定问题]');
}
