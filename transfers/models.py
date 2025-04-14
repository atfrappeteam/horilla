"""transfers.models.py"""

from django.db import models
from employee.models import Employee, Department, User, EmployeeWorkInformation
from base.models import Designation


# Create your models here.
class EmployeeTransfer(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('transferred', 'Transferred'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    current_department = models.ForeignKey(Department, on_delete=models.SET_NULL, null= True, related_name="current_department")
    new_department = models.ForeignKey(Department, on_delete=models.SET_NULL,null=True, related_name="new_department")
    current_designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null= True, related_name="current_designation")
    new_designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, related_name="new_designation")
    current_location = models.CharField(max_length=255, blank=True, null =True)
    new_location = models.CharField(max_length=255, blank=True, null = True)
    date_transfer = models.DateField(auto_now_add=True)
    reason = models.TextField()
    requests_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True, blank=True, related_name="requests_by")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null =True, blank = True, related_name="approved_by")
    rejected_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="rejected_by")
    cancelled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="cancelled_by")
    status = models.CharField( max_length = 255, choices=STATUS_CHOICES, default="draft")

    class Meta:
        permissions = [
            ("can_approve_transfer", "Can approve employee transfer"),
            ("can_reject_transfer", "Can reject employee transfer"),
            ("can_cancel_transfer", "Can cancel employee transfer"),
            ("can_submit_for_approval", "Can submit transfer request for approval")
        ]

    def save(self, *args, **kwargs):
        """Automatically fetch the current department and designation from EmployeeWorkInformation"""
        if self.employee:
            work_info = EmployeeWorkInformation.objects.filter(employee_id=self.employee).first()
            if work_info:
                self.current_department = work_info.department_id
                self.current_designation = work_info.designation_id
                self.current_location = work_info.location

        if not self.requests_by and self.employee:
            self.requests_by = self.employee.user

        super().save(*args, **kwargs)

    def approve_transfer(self, user):
        """Approve transfer and update Employee and EmployeeWorkInformation"""
        self.status = "approved"
        self.approved_by = user
        self.save()

        employee = self.employee
        if self.new_designation:
            employee.designation_id = self.new_designation
        employee.save()

        work_info = EmployeeWorkInformation.objects.filter(employee_id=self.employee).first()
        if work_info:
            work_info.department_id = self.new_department
            work_info.designation_id = self.new_designation
            work_info.location = self.new_location
            work_info.save()

    def reject_transfer(self, user):
        """Reject the transfer request"""
        self.status = "rejected"
        self.rejected_by = user
        self.save()

    def cancel_transfer(self, user):
        """Cancel the transfer request"""
        self.status = "cancelled"  # Or use a separate 'cancelled' state if you define one
        self.cancelled_by = user
        self.save()

    def mark_transferred(self):
        """Mark the request as successfully transferred"""
        self.status = "transferred"
        self.save()

    def mark_pending_approval(self):
        """Mark the request as pending transfer"""
        self.status = "pending_approval"
        self.save()

    def __str__(self):
        return f"{self.employee.badge_id} Transfer ({self.current_department} → {self.new_department})"
