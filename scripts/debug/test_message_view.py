"""
临时测试视图 - 用于调试messages框架
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


@login_required
def test_messages_page(request):
    """测试messages框架的页面"""
    return render(request, "test_messages.html")


@login_required
def test_add_message(request):
    """添加测试消息"""
    msg_type = request.POST.get("type", "success")
    if msg_type == "success":
        messages.success(request, "这是一条测试成功消息")
    elif msg_type == "error":
        messages.error(request, "这是一条测试错误消息")
    elif msg_type == "warning":
        messages.warning(request, "这是一条测试警告消息")

    return redirect("/test/messages/")
