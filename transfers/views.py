from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db.models import Q

from employee.models import EmployeeWorkInformation
from .forms import EmployeeTransferForm
from .models import EmployeeTransfer, Department, Employee
from .flow import (
    can_submit_for_approval, can_reject_transfer,
    can_cancel_transfer, get_allowed_actions, can_approve_by_hr_manager,
    can_approve_by_reporting_manager, #can_transfer
)

@login_required
def request_transfer(request):
    if request.method == "POST":
        form = EmployeeTransferForm(request.POST)
        if form.is_valid():
            transfer_request = form.save(commit=False)
            transfer_request.requests_by = request.user
            transfer_request.status = 'draft'
            # Ensure new_reporting_manager is an Employee instance
            selected_manager = form.cleaned_data.get("new_reporting_manager")
            if selected_manager and not isinstance(selected_manager, Employee):
                try:
                    selected_manager = Employee.objects.get(employee_user_id=selected_manager)
                except Employee.DoesNotExist:
                    selected_manager = None

            transfer_request.new_reporting_manager = selected_manager
            transfer_request.save()

            messages.success(request, "Transfer request created successfully.")
            return redirect("transfer_list")
    else:
        form = EmployeeTransferForm()

    return render(request, "transfers/request_transfer.html", {"form": form})


@login_required
def transfer_list(request):
    user = request.user
    employee_filter = request.GET.get('employee')
    status_filter = request.GET.get('status')
    status_filter = request.GET.get('status')
    department_filter = request.GET.get('department')

    is_superuser = user.is_superuser
    is_hr_user = user.groups.filter(name="HR User").exists()
    is_hr_manager = user.groups.filter(name="HR Manager").exists()
    is_reporting_manager = user.groups.filter(name="Reporting Manager").exists()
    is_employee = user.groups.filter(name="Employee").exists()

    if is_superuser or is_hr_user or is_hr_manager:
        transfers = EmployeeTransfer.objects.all()

    elif is_reporting_manager:
        # Get the reporting manager's employee profile
        reporting_info = EmployeeWorkInformation.objects.filter(
            employee_id__employee_user_id=user
        ).first()

        if reporting_info:
            current_rm_employee_id = reporting_info.employee_id

            # Find employees who currently report to this manager (From Manager)
            from_employee_ids = EmployeeWorkInformation.objects.filter(
                reporting_manager_id=current_rm_employee_id
            ).values_list("employee_id", flat=True)

            # Transfers where this manager is the TO manager
            to_transfers_ids = EmployeeTransfer.objects.filter(
                new_reporting_manager_id=current_rm_employee_id
            ).values_list("id", flat=True)

            transfers = EmployeeTransfer.objects.filter(
                Q(employee_id__in=from_employee_ids) | Q(id__in=to_transfers_ids)
            ).distinct()
        else:
            transfers = EmployeeTransfer.objects.none()

    elif is_employee:
        transfers = EmployeeTransfer.objects.filter(employee__employee_user_id=user)

    else:
        transfers = EmployeeTransfer.objects.none()

    # Apply additional filters
    if employee_filter:
        transfers = transfers.filter(
            Q(employee__employee_first_name__icontains=employee_filter) |
            Q(employee__employee_last_name__icontains=employee_filter)
        )
    if status_filter:
        transfers = transfers.filter(status=status_filter)
    if department_filter:
        transfers = transfers.filter(new_department__department__icontains=department_filter)

    # Annotate allowed actions
    for transfer in transfers:
        transfer.allowed_actions = get_allowed_actions(user, transfer)

    # Department dropdowns
    current_departments = EmployeeTransfer.objects.values_list('current_department', flat=True).distinct()
    new_departments = Department.objects.values_list('department', flat=True).distinct()

    string_current_departments = [
        str(dept).strip()
        for dept in current_departments
        if isinstance(dept, str) and dept and not str(dept).isdigit()
    ]
    string_new_departments = [
        str(dept).strip()
        for dept in new_departments
        if isinstance(dept, str) and dept and not str(dept).isdigit()
    ]

    all_departments = set(string_current_departments) | set(string_new_departments)
    departments = sorted([dept for dept in all_departments if dept.strip()])

    return render(request, "transfers/request_list.html", {
        "transfers": transfers,
        "departments": departments,
        "is_employee": is_employee,
        "is_hr_or_manager": is_hr_user or is_hr_manager or is_reporting_manager,
        "is_superuser": is_superuser
    })


@login_required
def submit_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if not can_submit_for_approval(request.user, transfer):
        messages.warning(request, "You do not have permission to submit this request.")
        return redirect("transfer_list")

    if transfer.status != "draft":
        messages.warning(request, "Only draft requests can be submitted.")
        return redirect("transfer_list")

    transfer.status = "Submitted"
    transfer.save()
    messages.success(request, f"The transfer request for {transfer.employee} has been submitted.")
    return redirect("transfer_list")


def approved_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)
    user = request.user
    status = transfer.status.lower()

    # First approval by current Reporting Manager
    if status == "submitted" and can_approve_by_reporting_manager(user, transfer):
        transfer.status = "approved_by_reporting_manager"
        transfer.save()
        messages.success(request, f"Transfer approved by Reporting Manager for employee {transfer.employee}.")
        return redirect("transfer_list")

    # Approval by HR Manager after Reporting Manager
    if status == "approved_by_reporting_manager" and can_approve_by_hr_manager(user, transfer):
        transfer.status = "approved_by_hr_manager"
        transfer.save()
        messages.success(request, f"Transfer approved by HR Manager for employee {transfer.employee}.")
        return redirect("transfer_list")

    # Final approval by future Reporting Manager after HR Manager
    if status == "approved_by_hr_manager" and can_approve_by_reporting_manager(user, transfer):
        transfer.status = "transferred"
        transfer.save()
        messages.success(request, f"Transfer fully approved by Reporting Manager for employee {transfer.employee}.")
        return redirect("transfer_list")

    messages.warning(request, "You do not have permission to approve this transfer at the current stage.")
    return redirect("transfer_list")



@login_required
def rejected_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if not can_reject_transfer(request.user, transfer):
        messages.warning(request, "You do not have permission to reject this request.")
        return redirect("transfer_list")

    if transfer.status not in ["Submitted","approved_by_hr_manager", "approved_by_reporting_manager"]:
        messages.warning(request, "Only submitted requests can be rejected.")
        return redirect("transfer_list")

    transfer.reject_transfer(request.user)
    messages.success(request, f"The transfer of employee {transfer.employee} has been rejected.")
    return redirect("transfer_list")


@login_required
def cancelled_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if not can_cancel_transfer(request.user, transfer):
        messages.warning(request, "You do not have permission to cancel this request.")
        return redirect("transfer_list")

    if transfer.status in ["rejected","approved","cancelled", "transferred"]:
        messages.warning(request, "This request is already cancelled or completed.")
        return redirect("transfer_list")

    transfer.mark_pending_approval(request.user)
    messages.success(request, f"The transfer of employee {transfer.employee} has been cancelled.")
    return redirect("transfer_list")

# def mark_transferred(request, transfer_id):
#     transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)
#
#     if not can_transfer(request.user, transfer):
#         messages.warning(request, "You do not have permission to mark this request as transferred.")
#         return redirect("transfer_list")
#
#     if transfer.status != "approved_by_hr_manager":
#         messages.warning(request, "Only approved requests can be marked as transferred.")
#         return redirect("transfer_list")
#
#     transfer.mark_transferred()
#     messages.success(request, f"The employee {transfer.employee} has been marked as transferred.")
#     return redirect("transfer_list")
