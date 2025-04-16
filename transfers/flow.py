from django.core.exceptions import PermissionDenied
from employee.models import EmployeeWorkInformation

def get_reporting_manager(employee):
    """Fetch reporting manager for an employee from the EmployeeWorkInformation model."""
    info = EmployeeWorkInformation.objects.filter(employee_id=employee).first()
    reporting_manager = info.reporting_manager_id if info else None
    print(f"[get_reporting_manager] Employee: {employee} ({employee.badge_id}), Reporting Manager: {reporting_manager}")
    return reporting_manager

def can_submit_transfer(user, transfer):
    reporting_manager = get_reporting_manager(transfer.employee)

    manager_user = getattr(reporting_manager, 'employee_user_id', None)

    result = user.is_superuser or (
        user.groups.filter(name="Reporting Manager").exists()
        and reporting_manager and manager_user == user
    )

    print(
        f"[can_submit_transfer] User: {user.username}, Is Superuser: {user.is_superuser}, "
        f"Is Reporting Manager Group: {user.groups.filter(name='Reporting Manager').exists()}, "
        f"Reporting Manager: {reporting_manager}, Manager User: {manager_user}, Match: {manager_user == user}, "
        f"Result: {result}"
    )
    return result

def can_submit_for_approval(user, transfer):
    """
    Only HR User and Admin can submit a transfer request when it's in draft status.
    """
    group_names = list(user.groups.values_list("name", flat=True))
    is_hr_user = "HR User" in group_names or user.has_perm("transfers.can_submit_for_approval")
    is_admin = user.is_superuser
    result = (is_hr_user or is_admin) and transfer.status.lower() == "draft"

    print(f"[can_submit_for_approval] User: {user.username}, Groups: {group_names}, "
          f"Status: {transfer.status}, Is HR User: {is_hr_user}, Is Admin: {is_admin}, Result: {result}")
    return result


def can_approve_transfer(user, transfer):
    result = user.is_superuser or user.groups.filter(name="HR Manager").exists()
    print(f"[can_approve_transfer] User: {user.username}, Groups: {list(user.groups.values_list('name', flat=True))}, Result: {result}")
    return result

def can_reject_transfer(user, transfer):
    result = can_approve_transfer(user, transfer)
    print(f"[can_reject_transfer] User: {user.username}, Result: {result}")
    return result

def can_cancel_transfer(user, transfer):
    result = False
    group_names = list(user.groups.values_list("name", flat=True))
    if user.is_superuser:
        result = True
    elif "HR Manager" in group_names:
        result = True
    elif "Reporting Manager" in group_names:
        reporting_manager = get_reporting_manager(transfer.employee)
        result = (
            reporting_manager
            and reporting_manager.employee_user_id == user
            and transfer.status.lower() in ["draft"]
        )
    elif "HR User" in group_names:
        result = transfer.status.lower() in ["draft"]
    print(f"[can_cancel_transfer] User: {user.username}, Groups: {group_names}, Status: {transfer.status}, Result: {result}")
    return result

def can_transfer(user, transfer):
    """
    A Reporting Manager can mark a transfer as 'transferred' if:
    - They are in the 'Reporting Manager' group or have the specific permission
    - They are the actual reporting manager of the employee
    - The current status is 'approved_by_hr_manager'
    """
    group_names = list(user.groups.values_list("name", flat=True))
    reporting_manager = get_reporting_manager(transfer.employee)
    is_actual_rm = reporting_manager and reporting_manager.employee_user_id == user

    result = (
        user.is_superuser or (
            ("Reporting Manager" in group_names or user.has_perm("transfers.can_transfer"))
            and is_actual_rm
            and transfer.status.lower() == "approved_by_hr_manager"
        )
    )

    print(f"[can_transfer] User: {user.username}, Groups: {group_names}, "
          f"Is Actual RM: {is_actual_rm}, Status: {transfer.status}, Result: {result}")
    return result


def can_approve_by_reporting_manager(user, transfer):
    """
    A Reporting Manager can approve a transfer if:
    - They are the current RM and status is 'submitted'
    """
    group_names = list(user.groups.values_list("name", flat=True))
    is_reporting_manager = "Reporting Manager" in group_names or user.has_perm("transfers.can_approve_by_reporting_manager")


    status = transfer.status.lower()

    print(f"[can_approve_by_reporting_manager] User: {user.username}, Groups: {group_names}")
    print(f"[can_approve_by_reporting_manager] Status: {status}")
    print(f"[can_approve_by_reporting_manager] Current user: {user}")
    print(f"[can_approve_by_reporting_manager] is_reporting_manager: {is_reporting_manager}")

    result = user.is_superuser or (
        is_reporting_manager and status in ["submitted","approved_by_hr_manager"]
    )

    print(f"[can_approve_by_reporting_manager] Final Result: {result}")
    return result


def can_approve_by_hr_manager(user, transfer):
    """
    An HR Manager can approve a transfer if:
    - They belong to the "HR Manager" group or have specific permission
    - The transfer status is 'approved_by_reporting_manager'
    """
    group_names = list(user.groups.values_list("name", flat=True))
    result = (
            user.is_superuser or ("HR Manager" in group_names or user.has_perm("transfers.can_approve_by_hr_manager"))
        and transfer.status.lower() == "approved_by_reporting_manager"
    )

    print(f"[can_approve_by_hr_manager] User: {user.username}, Groups: {group_names}, "
          f"Status: {transfer.status}, Result: {result}")
    return result

STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', "Submitted"),
        ('canceled', 'Canceled'),
        ('approved_by_reporting_manager', 'Approved by Reporting Manager'),
        ('approved_by_hr_manager', 'Approved by HR Manager'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('transferred', 'Transferred'),
    ]

def get_allowed_actions(user, transfer):
    actions = []
    status = transfer.status.lower()
    group_names = list(user.groups.values_list("name", flat=True))
    is_superuser = user.is_superuser

    print("\n--- Checking allowed actions for user:", user.username, "---")
    print("User Groups:", group_names)
    print("Transfer Status:", transfer.status)

    # HR User Permissions
    if "HR User" in group_names:
        if status == "draft":
            actions += ["submit_for_approval", "cancel"]
        elif status == "submitted":
            actions += []

    # Reporting Manager Permissions (No future reporting manager check)
    if "Reporting Manager" in group_names:
        if status == "submitted":
            actions += ["approve", "reject"]
        elif status == "approved_by_hr_manager":
            actions += ["approve", "reject"]  # Final approval from RM

    # HR Manager Permissions
    if "HR Manager" in group_names:
        if status == "approved_by_reporting_manager":
            actions += ["approve", "reject"]

    # Superuser Permissions (Override)
    if is_superuser:
        print(f"-> Superuser override for status: {status}")
        if status == "draft":
            actions = ["submit_for_approval", "cancel"]
        elif status == "submitted":
            actions = ["approve", "reject"]
        elif status == "approved_by_reporting_manager":
            actions = ["approve", "reject"]
        elif status == "approved_by_hr_manager":
            actions = ["approve", "reject"]
        elif status in ["approved", "rejected", "cancelled", "transferred"]:
            actions = []
        print(f"-> Superuser override actions: {actions}")

    print(f"Final Allowed Actions: {actions}")
    return actions
