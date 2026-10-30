import random
from datetime import datetime, timedelta

# 中文星期映射：weekday() 返回 0=周一, 1=周二 ... 6=周日
WEEKDAY_CN = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

def generate_random_time_str(
    start_date_str: str, 
    end_date_str: str, 
    start_hour: int = 0, 
    end_hour: int = 24,
    date_format: str = "%Y.%m.%d",
    time_format: str = "%H:%M"
) -> str:
    """
    生成指定日期范围和小时范围内的随机时间字符串。
    
    :param start_date_str: 开始日期，格式如 "2026-01-01"
    :param end_date_str: 结束日期，格式如 "2026-12-31"
    :param start_hour: 随机时间的起始小时 (0-23)
    :param end_hour: 随机时间的结束小时 (1-24)
    :param date_format: 日期部分的格式化字符串
    :param time_format: 时间部分的格式化字符串
    :return: 格式化后的时间字符串，星期部分显示为"星期一/星期二/.../星期日"
    """
    # 1. 解析日期字符串
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    # 确保结束日期大于等于开始日期
    if end_date < start_date:
        raise ValueError("结束日期必须大于或等于开始日期！")
        
    # 2. 随机生成日期部分
    # 计算两个日期之间的总秒数
    time_diff = int((end_date - start_date).total_seconds())
    # 随机生成秒数偏移量
    random_seconds = random.randint(0, time_diff)
    random_date = start_date + timedelta(seconds=random_seconds)
    
    # 3. 随机生成时间部分（时和分）
    random_hour = random.randint(start_hour, end_hour - 1)  # end_hour 是不包含的
    random_minute = random.randint(0, 59)
    
    # 4. 将随机时间替换到随机日期上
    final_datetime = random_date.replace(hour=random_hour, minute=random_minute)
    
    # 5. 格式化输出（星期显示为"星期一/星期二/.../星期日"形式）
    #    不再依赖系统 locale 的 %A，改用固定的中文星期映射，跨平台稳定
    weekday_cn = WEEKDAY_CN[final_datetime.weekday()]
    result = final_datetime.strftime(date_format) + " " + weekday_cn + " " + final_datetime.strftime(time_format)
    return result

# ================= 测试代码 =================
# if __name__ == "__main__":
#     # 设置日期范围：2026年1月1日 到 2026年12月31日
#     # 设置时间范围：早上 8点 到 晚上 20点
#     random_time = generate_random_time_str(
#         start_date_str="2026-01-01",
#         end_date_str="2026-12-31",
#         start_hour=8,
#         end_hour=20
#     )
#     print(random_time)
    
#     # 再运行一次看看不同的结果
#     print(generate_random_time_str("2026-10-01", "2026-10-31", 9, 18))