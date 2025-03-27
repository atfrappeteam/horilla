from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import EmployeeTransfer
from .forms import EmployeeTransferForm
from employee.models import EmployeeWorkInformation

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
    if request.user.is_superuser:
        transfers = EmployeeTransfer.objects.all()
    else:
        transfers = EmployeeTransfer.objects.filter(employee__user=request.user)
    return render(request, "transfers/request_list.html", {"transfers": transfers})


@login_required
def approved_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if transfer.status != "Pending":
        messages.warning(request, "This transfer request is already processed.")
        return redirect("transfer_list")

    transfer.approve_transfer(request.user)
    messages.success(request, f"The transfer of employee {transfer.employee} has been approved.")
    return redirect("transfer_list")


@login_required
def cancelled_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if transfer.status != "Pending":
        messages.warning(request, "This transfer request is already processed.")
        return redirect("transfer_list")

    transfer.cancel_transfer()  # Remove unnecessary argument
    messages.success(request, f"The transfer of employee {transfer.employee} has been canceled.")
    return redirect("transfer_list")


@login_required
def rejected_transfer(request, transfer_id):
    transfer = get_object_or_404(EmployeeTransfer, id=transfer_id)

    if transfer.status != "Pending":
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