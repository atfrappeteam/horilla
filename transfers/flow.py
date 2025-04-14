from django.core.exceptions import PermissionDenied

def get_reporting_manager(employee):
    """Fetch reporting manager for an employee from the EmployeeWorkInformation model."""
    from employee.models import EmployeeWorkInformation
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
    is_reporting_manager = can_submit_transfer(user, transfer)
    is_admin = user.is_superuser
    result = (is_reporting_manager or is_admin) and transfer.status.lower() == "draft"
    print(f"[can_submit_for_approval] User: {user.username}, Status: {transfer.status}, Is Reporting Manager: {is_reporting_manager}, Is Admin: {is_admin}, Result: {result}")
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
            and transfer.status.lower() in ["draft", "submitted"]
        )
    elif "HR User" in group_names:
        result = transfer.status.lower() in ["draft", "submitted"]
    print(f"[can_cancel_transfer] User: {user.username}, Groups: {group_names}, Status: {transfer.status}, Result: {result}")
    return result

def can_mark_transferred(user, transfer):
    result = (user.is_superuser or user.groups.filter(name="HR Manager").exists()) and transfer.status == "Approved"
    print(f"[can_mark_transferred] User: {user.username}, Groups: {list(user.groups.values_list('name', flat=True))}, Status: {transfer.status}, Result: {result}")
    return result

def get_allowed_actions(user, transfer):
    actions = []
    status = transfer.status.lower()
    group_names = list(user.groups.values_list("name", flat=True))
    is_superuser = user.is_superuser

    print("\n--- Checking allowed actions for user:", user.username, "---")
    print("User Groups:", group_names)
    print("Transfer Status:", transfer.status)

    if "HR Manager" in group_names:
        if status == "submitted":
            actions += ["approve", "reject"]
        if status in ["draft", "submitted",]:
            if can_cancel_transfer(user, transfer):
                actions.append("cancel")
        if status == "approved":
            actions.append("mark_transferred")


    elif "Reporting Manager" in group_names:
        reporting_manager = get_reporting_manager(transfer.employee)
        print(f"[get_allowed_actions] Reporting Manager: {reporting_manager}, Current User: {user}")
        if can_submit_for_approval(user, transfer):
            actions.append("submit_for_approval")
        if can_cancel_transfer(user, transfer):
            actions.append("cancel")

    elif "HR User" in group_names:
        if status == "approved":
            if can_cancel_transfer(user, transfer):
                actions.append("cancel")

    elif "Employee" in group_names:
        if can_cancel_transfer(user, transfer):
            actions.append("cancel")

    if is_superuser:
        print(f"-> Superuser override for status: {status}")
        if status == "draft":
            actions = ["submit", "cancel"]
        elif status == "submitted":
            actions = ["approve", "reject", "cancel"]
        elif status == "approved":
            actions = ["mark_transferred"]
        print(f"-> Superuser override actions: {actions}")

    print("Final Allowed Actions:", actions)
    return actions

