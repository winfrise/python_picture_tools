import random
from datetime import datetime, timedelta

def generate_date():
    """
    在指定范围内随机生成一个日期字符串。
    
    :param start: 起始日期字符串 (如 "2026-11-01")，默认为今天。
    :param end:   结束日期字符串 (如 "2026-11-30")，默认为今天。
    :param fmt:   日期格式，默认 YYYY-MM-DD。
    :return:      单个日期字符串 (如 "2026-11-08")。
    """

    start = "2026-11-01"
    end = "2026-11-30"
    fmt="%Y-%m-%d"
    
    # 1. 如果未指定范围，默认返回今天（模拟你图片中的静态赋值效果）
    if start is None and end is None:
        return datetime.now().strftime(fmt)
    
    # 2. 将字符串转换为 datetime 对象
    # 如果只传了 start 没传 end，则 end 默认为 start（即只生成这一天）
    start_dt = datetime.strptime(start, fmt) if start else datetime.now()
    end_dt = datetime.strptime(end, fmt) if end else start_dt
    
    # 确保 start 小于 end，防止报错
    if start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt
        
    # 3. 计算天数差
    delta_days = (end_dt - start_dt).days
    
    # 4. 随机取一个偏移量并生成结果
    random_offset = random.randint(0, delta_days)
    result_dt = start_dt + timedelta(days=random_offset)
    
    return result_dt.strftime(fmt)
