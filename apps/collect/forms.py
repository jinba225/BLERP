"""
表单模块
"""
from django import forms

from .models import CollectTask, FieldMapRule, Platform, PricingRule, ProductListing, Shop


class CollectTaskForm(forms.ModelForm):
    """采集任务创建表单"""

    # 手动指定平台，仅显示启用的采集平台
    platform = forms.ModelChoiceField(
        queryset=Platform.objects.filter(is_deleted=False, is_active=True, platform_type="collect"),
        label="采集平台",
        error_messages={"required": "请选择采集平台", "does_not_exist": "采集平台不存在或已禁用"},
    )

    collect_urls = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "请输入商品链接，每行一个"}), label="采集商品链接"
    )

    # 可选：同步到跨境平台
    sync_cross = forms.BooleanField(required=False, label="采集落地后自动同步到跨境平台")

    cross_platform = forms.ModelChoiceField(
        queryset=Platform.objects.filter(is_deleted=False, is_active=True, platform_type="cross"),
        required=False,
        label="目标跨境平台",
    )

    cross_shop = forms.ModelChoiceField(
        queryset=Shop.objects.filter(is_deleted=False), required=False, label="目标跨境店铺"
    )

    # 可选：定价规则
    pricing_rule = forms.ModelChoiceField(
        queryset=PricingRule.objects.filter(is_deleted=False, is_active=True),
        required=False,
        label="定价规则",
    )

    # 可选：翻译
    translate = forms.BooleanField(required=False, label="自动翻译为英文")
    target_language = forms.ChoiceField(
        choices=[("en", "英文"), ("ja", "日文"), ("ko", "韩文")],
        required=False,
        initial="en",
        label="目标语言",
    )

    class Meta:
        model = CollectTask
        fields = ["task_name", "platform", "collect_urls"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        # 按跨境平台过滤店铺
        if self.data.get("cross_platform"):
            self.fields["cross_shop"].queryset = Shop.objects.filter(
                platform_id=self.data.get("cross_platform"), is_deleted=False
            )
        else:
            self.fields["cross_shop"].queryset = Shop.objects.none()

    def clean_collect_urls(self):
        """清洗采集链接：去重+非空"""
        collect_urls = self.cleaned_data.get("collect_urls")
        url_list = [url.strip() for url in collect_urls.split("\n") if url.strip()]
        if not url_list:
            raise forms.ValidationError("采集链接不能为空")
        # 去重
        url_list = list(set(url_list))
        return "\n".join(url_list)

    def clean(self):
        """全局校验：选择自动同步则必须选择跨境平台/店铺"""
        cleaned_data = super().clean()
        sync_cross = cleaned_data.get("sync_cross")
        cross_platform = cleaned_data.get("cross_platform")
        cross_shop = cleaned_data.get("cross_shop")

        if sync_cross and (not cross_platform or not cross_shop):
            raise forms.ValidationError("选择自动同步到跨境平台，则必须选择目标跨境平台和店铺")

        return cleaned_data


class FieldMapRuleForm(forms.ModelForm):
    """字段映射规则表单"""

    class Meta:
        model = FieldMapRule
        fields = "__all__"


class PlatformForm(forms.ModelForm):
    """平台配置表单"""

    class Meta:
        model = Platform
        fields = "__all__"

    def clean(self):
        """校验平台配置"""
        cleaned_data = super().clean()
        platform_type = cleaned_data.get("platform_type")

        # 采集平台需要API配置
        if platform_type in ["collect", "both"]:
            api_key = cleaned_data.get("api_key")
            api_secret = cleaned_data.get("api_secret")
            api_url = cleaned_data.get("api_url")

            if not all([api_key, api_secret, api_url]):
                raise forms.ValidationError("采集平台必须配置API Key、API Secret和API URL")

        return cleaned_data


class ShopForm(forms.ModelForm):
    """店铺配置表单"""

    class Meta:
        model = Shop
        fields = "__all__"


class PricingRuleForm(forms.ModelForm):
    """定价规则表单"""

    class Meta:
        model = PricingRule
        fields = "__all__"

    def clean(self):
        """校验定价规则"""
        cleaned_data = super().clean()
        rule_type = cleaned_data.get("rule_type")

        if rule_type == "markup":
            markup_percent = cleaned_data.get("markup_percent")
            if not markup_percent:
                raise forms.ValidationError("加成定价必须设置加成百分比")

        elif rule_type == "fixed":
            fixed_price = cleaned_data.get("fixed_price")
            if not fixed_price:
                raise forms.ValidationError("固定定价必须设置固定价格")

        elif rule_type == "formula":
            formula = cleaned_data.get("formula")
            if not formula:
                raise forms.ValidationError("公式定价必须设置定价公式")

        return cleaned_data


class ProductListingForm(forms.ModelForm):
    """产品Listing表单"""

    class Meta:
        model = ProductListing
        fields = "__all__"
        exclude = ["sync_status", "sync_error", "last_synced_at"]
