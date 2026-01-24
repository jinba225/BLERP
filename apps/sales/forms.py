"""
Sales forms for the ERP system.
"""
from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone
from datetime import timedelta
from datetime import timedelta
from .models import Quote, QuoteItem, SalesOrder


class QuoteForm(forms.ModelForm):
    """
    Quote form for creating and editing quotes.
    """

    class Meta:
        model = Quote
        fields = [
            'quote_type',
            'customer',
            'contact_person',
            'quote_date',
            'valid_until',
            'sales_rep',
            'currency',
            'exchange_rate',
            'tax_rate',
            'discount_amount',
            'payment_terms',
            'delivery_terms',
            'warranty_terms',
            'reference_number',
            'notes',
        ]
        widgets = {
            'quote_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            }),
            'customer': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'required': True,
            }),
            'contact_person': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            }),
            'quote_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                }
            ),
            'valid_until': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                }
            ),
            'sales_rep': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            }),
            'currency': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            }, choices=[
                ('CNY', '人民币 (CNY)'),
                ('USD', '美元 (USD)'),
                ('EUR', '欧元 (EUR)'),
                ('GBP', '英镑 (GBP)'),
                ('JPY', '日元 (JPY)'),
                ('HKD', '港币 (HKD)'),
            ]),
            'exchange_rate': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'step': '0.0001',
                'min': '0',
            }),
            'tax_rate': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            }, choices=[
                ('13', '13% (标准税率)'),
                ('0', '0% (免税)'),
                ('1', '1%'),
                ('3', '3%'),
                ('6', '6%'),
                ('9', '9%'),
            ]),
            'discount_amount': forms.HiddenInput(attrs={
                'id': 'discount_amount_hidden',
            }),
            'payment_terms': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 transition-colors',
                'readonly': 'readonly',
                'placeholder': '选择客户后自动带出',
            }),
            'delivery_terms': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'placeholder': '例如：收到订单后15个工作日内交货',
            }),
            'warranty_terms': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'rows': 3,
                'placeholder': '保修条款...',
            }),
            'reference_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'placeholder': '客户询价号',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'rows': 3,
                'placeholder': '备注信息...',
            }),
        }

    def __init__(self, *args, **kwargs):
        # Extract request object
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Filter customer queryset to only show active, non-deleted customers
        from apps.customers.models import Customer, CustomerContact
        self.fields['customer'].queryset = Customer.objects.filter(
            is_deleted=False,
            status='active'
        ).order_by('name')

        # Set default values for new quotes
        if not self.instance.pk:
            self.initial['quote_date'] = timezone.now().date()
            self.initial['valid_until'] = timezone.now().date() + timedelta(days=30)
            self.initial['currency'] = 'CNY'
            self.initial['exchange_rate'] = 1.0000
            self.initial['tax_rate'] = 13.00  # Default VAT rate in China

            # Set sales_rep to current user if request is available
            if self.request and self.request.user:
                self.initial['sales_rep'] = self.request.user.id

        # Update contact person choices based on customer
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['contact_person'].queryset = CustomerContact.objects.filter(
                    customer_id=customer_id,
                    is_deleted=False
                )
            except (ValueError, TypeError):
                self.fields['contact_person'].queryset = CustomerContact.objects.none()
        elif self.instance.pk and self.instance.customer:
            self.fields['contact_person'].queryset = CustomerContact.objects.filter(
                customer=self.instance.customer,
                is_deleted=False
            )
        else:
            # For new quotes without customer selected, show no contacts
            self.fields['contact_person'].queryset = CustomerContact.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        quote_date = cleaned_data.get('quote_date')
        valid_until = cleaned_data.get('valid_until')

        # Validate dates
        if quote_date and valid_until:
            if valid_until < quote_date:
                raise forms.ValidationError('有效期至日期不能早于报价日期')

        # Validate exchange rate for foreign currency
        currency = cleaned_data.get('currency')
        exchange_rate = cleaned_data.get('exchange_rate')
        if currency and currency != 'CNY' and (not exchange_rate or exchange_rate <= 0):
            raise forms.ValidationError('外币报价必须设置有效的汇率')

        return cleaned_data


class QuoteItemForm(forms.ModelForm):
    """
    Quote item form for adding products to a quote.
    """

    class Meta:
        model = QuoteItem
        fields = [
            'product',
            'specifications',
            'unit',
            'quantity',
            'unit_price',
            'discount_rate',
            'line_total',
            'lead_time',
            'notes',
        ]
        widgets = {
            'product': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            }),
            'specifications': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'placeholder': '产品规格',
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-100 transition-colors text-center',
                'readonly': 'readonly',
                'placeholder': '单位',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'step': '1',
                'min': '0',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'step': '0.01',
                'min': '0',
            }),
            'discount_rate': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'step': '0.01',
                'min': '0',
                'max': '100',
            }),
            'line_total': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'step': '0.01',
                'min': '0',
            }),
            'lead_time': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'min': '0',
            }),
            'notes': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
                'placeholder': '备注',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter product queryset to only show active, non-deleted products
        from apps.products.models import Product
        self.fields['product'].queryset = Product.objects.filter(
            is_deleted=False,
            status='active'
        ).select_related('unit').order_by('code')

        # Set default values for new items
        if not self.instance.pk:
            self.initial['discount_rate'] = 0
            self.initial['lead_time'] = 15


# Formset for quote items
QuoteItemFormSet = inlineformset_factory(
    Quote,
    QuoteItem,
    form=QuoteItemForm,
    extra=0,  # Number of empty forms to display - 0 so users manually add rows
    can_delete=True,
    min_num=1,  # Minimum number of items required
    validate_min=True,
)


class QuoteSearchForm(forms.Form):
    """
    Form for searching and filtering quotes.
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            'placeholder': '搜索报价单号、客户名称...',
        })
    )

    quote_type = forms.ChoiceField(
        required=False,
        choices=[('', '全部类型')] + Quote.QUOTE_TYPES,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
        })
    )

    status = forms.ChoiceField(
        required=False,
        choices=[('', '全部状态')] + Quote.QUOTE_STATUS,
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
        })
    )

    customer = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            'placeholder': '客户名称',
        })
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
        })
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
        })
    )


class ConvertToOrderForm(forms.Form):
    """
    Form for converting a quote to a sales order.
    """
    order_date = forms.DateField(
        label='订单日期',
        initial=timezone.now().date(),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
        })
    )

    required_date = forms.DateField(
        label='要求交期',
        required=False,
        initial=timezone.now().date() + timedelta(days=15),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
        })
    )

    notes = forms.CharField(
        label='订单备注',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-theme-500 focus:border-theme-500 transition-colors',
            'rows': 3,
            'placeholder': '订单相关备注...',
        })
    )

    confirm = forms.BooleanField(
        label='我确认要将此报价单转换为销售订单',
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )
