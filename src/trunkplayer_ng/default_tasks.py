# """
#  _________________ 
# < Multitasking yo >
#  ----------------- 
#         \   ^__^
#          \  (oo)\_______
#             (__)\       )\/\
#                 ||----w |
#                 ||     ||
# """

# from django_celery_beat.models import CrontabSchedule, PeriodicTask

# def create_schedules() -> None:
#     """
#     Creates default schedules
#     """

#     daily, _ = CrontabSchedule.objects.get_or_create(
#         minute='0',
#         hour='0',
#         day_of_week='*',
#         day_of_month='*',
#         month_of_year='*',
#     )

#     hourly, _ = CrontabSchedule.objects.get_or_create(
#         minute='0',
#         hour='*',
#         day_of_week='*',
#         day_of_month='*',
#         month_of_year='*',
#     )

#     PeriodicTask.objects.create(
#         crontab=hourly,
#         name='Prune',
#         task='sigint.tasks.prune',
#     )

#     PeriodicTask.objects.create(
#         crontab=daily,
#         name='Maxmind GeoIP Lite Update Check',
#         task='sigint.tasks.sync_maxmind_database',
#     )

#     PeriodicTask.objects.create(
#         crontab=daily,
#         name='List Generation',
#         task='sigint.tasks.generate_lists',
#     )