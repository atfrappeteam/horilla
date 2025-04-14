from django.contrib.auth.models import User, Group
from employee.models import Employee, EmployeeWorkInformation
from base.models import Designation
from django.utils import timezone

demo_data = [
    {
        "badge_id": "E001",
        "name": "Aarya Sharma",
        "email": "aarya.sharma@example.com",
        "job_position": "Software Developer",
        "role": "Employee"
    },
    {
        "badge_id": "E002",
        "name": "Karan Patel",
        "email": "karan.patel@example.com",
        "job_position": "Team Lead - Backend",
        "role": "Reporting Manager"
    },
    {
        "badge_id": "E003",
        "name": "Sneha Deshmukh",
        "email": "sneha.deshmukh@example.com",
        "job_position": "Head of Engineering",
        "role": "From Dept Head"
    },
    {
        "badge_id": "E004",
        "name": "Ravi Nair",
        "email": "ravi.nair@example.com",
        "job_position": "Head of Data Science",
        "role": "To Dept Head"
    },
    {
        "badge_id": "E005",
        "name": "Priya Mehta",
        "email": "priya.mehta@example.com",
        "job_position": "Senior HR Executive",
        "role": "HR Manager"
    },
    {
        "badge_id": "E006",
        "name": "Arvind Iyer",
        "email": "arvind.iyer@example.com",
        "job_position": "System Admin",
        "role": "System Admin"
    },
    {
        "badge_id": "E007",
        "name": "Deepak Kulkarni",
        "email": "deepak.kulkarni@example.com",
        "job_position": "Payroll Officer",
        "role": "Finance/Payroll"
    },
    {
        "badge_id": "E008",
        "name": "Tanvi Joshi",
        "email": "tanvi.joshi@example.com",
        "job_position": "IT Support Executive",
        "role": "IT/Admin Support"
    }
]

for user_data in demo_data:
    email = user_data["email"].strip()
    if not email:
        print(f"⚠️ Skipping user with empty email: {user_data}")
        continue

    first_name, last_name = user_data["name"].split(" ", 1)
    user, created = User.objects.get_or_create(
        username=email,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "is_active": True,
        }
    )
    if created:
        user.set_password("test1234")
        user.save()
        print(f"✅ Created user: {user.username}")
    else:
        print(f"ℹ️ User already exists: {user.username}")

    group, _ = Group.objects.get_or_create(name=user_data["role"])
    user.groups.add(group)

    designation, _ = Designation.objects.get_or_create(
        designation=user_data["job_position"]
    )

    employee, emp_created = Employee.objects.get_or_create(
        employee_user_id=user,
        defaults={
            "is_active": True,
            "badge_id": user_data.get("employee_code", f"EMP{user.id:04d}")
        }
    )
    if not emp_created:
        # Update fields if needed
        employee.employee_code = user_data.get("badge_id", employee.badge_id)
        employee.is_active = True
        employee.save()

    work_info, _ = EmployeeWorkInformation.objects.get_or_create(
        employee_id=employee,
        defaults={
            "date_of_joining": timezone.now().date(),
            "job_position_id": designation,
            "employment_type": "intern",
            "employment_status": "active",
        }
    )

    print(f"👔 Linked profile for: {user.username}")
