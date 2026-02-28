"""
示例任务 - 展示如何使用任务优化器
"""

from apps.core.services.task_optimizer import task_with_priority, task_with_retry


@task_with_retry(max_retries=3, retry_backoff=2, retry_jitter=True)
def example_task_with_retry(task_id):
    """
    示例任务 - 带重试机制

    Args:
        task_id: 任务ID

    Returns:
        str: 任务结果
    """
    import random
    import time

    print(f"执行任务 {task_id}")
    time.sleep(1)

    # 模拟随机失败
    if random.random() < 0.5:
        raise Exception(f"任务 {task_id} 模拟失败")

    return f"任务 {task_id} 执行成功"


@task_with_priority(priority=3)
def high_priority_task(data):
    """
    高优先级任务示例

    Args:
        data: 任务数据

    Returns:
        dict: 任务结果
    """
    import time

    print(f"执行高优先级任务: {data}")
    time.sleep(2)

    return {"status": "success", "data": data, "message": "高优先级任务执行完成"}


@task_with_priority(priority=7)
def low_priority_task(data):
    """
    低优先级任务示例

    Args:
        data: 任务数据

    Returns:
        dict: 任务结果
    """
    import time

    print(f"执行低优先级任务: {data}")
    time.sleep(5)

    return {"status": "success", "data": data, "message": "低优先级任务执行完成"}
