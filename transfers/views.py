from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EmployeeTransfer
from .forms import EmployeeTransferForm
from employee.models import EmployeeWorkInformation
from django.db.models import Q, Count
from base.models import Department

@login_required
def request_transfer(request):
    if request.method == "POST":
        form = EmployeeTransferForm(request.POST)
        if form.is_valid():
            transfer_request = form.save(commit=False)
            transfer_request.requests_by = request.user  # Fixing 'requested_by'
            transfer_request.save()
            messages.success(request, "Transfer request submitted successfully.")
            return redirect("transfer_list")
    else:
        form = EmployeeTransferForm()
    return render(request, "transfers/request_transfer.html", {"form": form})


@login_required
def transfer_list(request):
    transfers = EmployeeTransfer.objects.all()

    employee_filter = request.GET.get('employee')
    status_filter = request.GET.get('status')
    department_filter = request.GET.get('department')

    if employee_filter:
        transfers = transfers.filter(employee__employee_first_name__icontains=employee_filter) | transfers.filter(employee__employee_last_name__icontains=employee_filter)

    if status_filter:
        transfers = transfers.filter(status=status_filter)

    # Apply department filter to the 'department' field of the related Department model
    if department_filter:
        transfers = transfers.filter(new_department__department__icontains=department_filter)

    if not request.user.is_superuser:
        transfers = transfers.filter(employee__employee_user_id=request.user)

    # Fetch all unique department names (considering both current and new for the dropdown)
    current_departments = EmployeeTransfer.objects.values_list('current_department', flat=True).distinct()
    new_departments = Department.objects.values_list('department', flat=True).distinct()  # Fetch from Department model

    # Ensure all current departments are treated as strings and filter out non-string values
    string_current_departments = [str(dept).strip() for dept in current_departments if isinstance(dept, str) and dept and not str(dept).isdigit()]

    # Ensure all new departments are treated as strings and filter out non-string values
    string_new_departments = [str(dept).strip() for dept in new_departments if isinstance(dept, str) and dept and not str(dept).isdigit()]

    # Combine and get unique departments using a set
    all_departments = set(string_current_departments) | set(string_new_departments)

    # Filter out empty strings and None values and then sort
    valid_departments = sorted([dept for dept in all_departments if dept and dept.strip()])

    departments = valid_departments

    return render(request, "transfers/request_list.html", {"transfers": transfers, "request": request, "departments": departments})


@login_required
def approved_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if transfer.status in ["Approve", "Reject", "Cancelled"]:
        messages.warning(request, "This request is already processed.")
        return redirect("transfer_list")

    transfer.approve_transfer(request.user)
    messages.success(request, f"The transfer of employee {transfer.employee} has been approved.")
    return redirect("transfer_list")


@login_required
def cancelled_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if transfer.status in ["Cancelled"]:
        messages.warning(request, "This request is already cancelled.")
        return redirect("transfer_list")

    transfer.cancel_transfer(request.user)  # Remove unnecessary argument
    messages.success(request, f"The transfer of employee {transfer.employee} has been canceled.")
    return redirect("transfer_list")


@login_required
def rejected_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if transfer.status in ["Approve", "Reject", "Cancelled"]:
        messages.warning(request, "This transfer request is already processed.")
        return redirect("transfer_list")

    transfer.reject_transfer(request.user)
    messages.success(request, f"The transfer of employee {transfer.employee} has been rejected.")
    return redirect("transfer_list")


@login_required
def process_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if transfer.status != "Requested":
        messages.warning(request, "This transfer is already processed.")
        return redirect("transfer_list")

    transfer.status = "Processed"
    transfer.save()
    messages.success(request, f"The transfer request for {transfer.employee} has been processed.")
    return redirect("transfer_list")