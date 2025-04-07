import sys
import datetime
import pytz
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.models import DjangoJob
# from django_apscheduler.jobstores import DjangoJobStore
from django.core.mail import send_mail
from django.conf import settings
from employee.models import DailyWorkSummary
import holidays
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

jobstores = {
    'default': SQLAlchemyJobStore(url='postgresql://horilla:horilla@localhost:5432/horilla_main', pickle_protocol=4)
}
# Global scheduler
scheduler = BackgroundScheduler(jobstores=jobstores)

# scheduler.add_jobstore(DjangoJobStore(), "default")

def send_daily_work_summary(summary_id):
    """Fetch the specific DailyWorkSummary and send emails to assigned users."""
    today = datetime.date.today()
    holiday_list = holidays.India()

    # if today in holiday_list:
    #     print(f"🚫 Today ({today}) is a holiday. No emails sent.")
    #     return

    try:
        summary = DailyWorkSummary.objects.get(id=summary_id)
        if summary.holiday_list:
            custom_holidays = set(map(str.strip, summary.holiday_list.split(',')))  # Split and clean
            custom_holidays = {datetime.datetime.strptime(date, "%Y-%m-%d").date() for date in custom_holidays}
        else:
            custom_holidays = set()

        # Check if today is a holiday
        if today in holiday_list or today in custom_holidays:
            print(f"🚫 Today ({today}) is a holiday. No emails sent.")
            return
        user_emails = [user.email for user in summary.users.all() if user.email]

        if user_emails:
            try:
                send_mail(
                    subject=summary.subject,
                    message=summary.message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=user_emails,
                    fail_silently=False
                )
                print(f"✅ Email sent to {user_emails} for summary: {summary.name}")
            except Exception as e:
                print(f"❌ Failed to send email: {e}")
    except DailyWorkSummary.DoesNotExist:
        print(f"❌ Summary with ID {summary_id} not found.")
    except Exception as e:
        print(f"❌ Unexpected error in send_daily_work_summary: {e}")

def schedule_daily_work_summaries():
    """Schedules jobs dynamically based on user-defined send_email_at times."""
    if not settings.SCHEDULER_AUTOSTART:
        print("🚫 Scheduler is disabled in settings.")
        return

    try:
        DjangoJob.objects.all().delete()  # Clear old job data
        scheduler.remove_all_jobs()
        print("🗑️ Cleared existing jobs from APScheduler.")

        timezone = pytz.timezone("Asia/Kolkata")
        summaries = DailyWorkSummary.objects.all()
        
        for summary in summaries:
            send_time = summary.send_email_at
            if send_time:
                scheduler.add_job(
                    send_daily_work_summary,
                    trigger=CronTrigger(
                        hour=send_time.hour, 
                        minute=send_time.minute,
                        timezone=timezone
                    ),
                    id=f"daily_work_summary_{summary.id}",
                    replace_existing=True,
                    args=[summary.id]
                )
                print(f"📅 Scheduled {summary.name} at {send_time.hour}:{send_time.minute}")

        if not scheduler.running:
            scheduler.start()
            print("🚀 APScheduler started successfully.")
        else:
            print("⚠️ Scheduler is already running. Skipping restart.")
    except Exception as e:
        print(f"❌ Error while scheduling daily work summaries: {e}")

def update_experience():
    """Update employee work experience every 4 hours."""
    try:
        from employee.models import EmployeeWorkInformation
        queryset = EmployeeWorkInformation.objects.filter(employee_id__is_active=True)
        for instance in queryset:
            instance.experience_calculator()
        print("✅ Employee experience updated successfully.")
    except Exception as e:
        print(f"❌ Error in updating experience: {e}")

def block_unblock_disciplinary():
    """Handle disciplinary actions (suspension, dismissal)."""
    try:
        from base.models import EmployeeShiftSchedule
        from employee.models import DisciplinaryAction
        from employee.policies import employee_account_block_unblock

        dis_action = DisciplinaryAction.objects.all()
        for dis in dis_action:
            if dis.action.block_option:
                if dis.action.action_type == "suspension":
                    if dis.days:
                        end_date = dis.start_date + timedelta(days=dis.days)
                        if datetime.date.today() >= dis.start_date or datetime.date.today() >= end_date:
                            r = datetime.date.today() >= end_date
                            for emp in dis.employee_id.all():
                                employee_account_block_unblock(emp_id=emp.id, result=r)

                if dis.action.action_type == "dismissal" and datetime.date.today() >= dis.start_date:
                    for emp in dis.employee_id.all():
                        employee_account_block_unblock(emp_id=emp.id, result=False)
        print("✅ Disciplinary actions processed successfully.")
    except Exception as e:
        print(f"❌ Error in processing disciplinary actions: {e}")

# Start scheduler only if not running system commands
if not any(cmd in sys.argv for cmd in ["makemigrations", "migrate", "compilemessages", "flush", "shell"]):
    print("🚀 Initializing APScheduler background jobs...")

    try:
        DjangoJob.objects.all().delete()  # Clear old scheduler jobs
        print("✅ Cleared old scheduler jobs.")

        if not scheduler.running:
            scheduler.add_job(update_experience, "interval", hours=4, replace_existing=True)
            scheduler.add_job(block_unblock_disciplinary, "interval", minutes=1, replace_existing=True)
            scheduler.start()
            print("🚀 APScheduler started successfully.")
        else:
            print("⚠️ Scheduler is already running. Skipping restart.")
    except Exception as e:
        print(f"❌ Error in initializing scheduler: {e}")
