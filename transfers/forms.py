from django import forms
from .models import EmployeeTransfer, Employee
from base.models import Designation

class EmployeeTransferForm(forms.ModelForm):
    new_designation = forms.ModelChoiceField(
        queryset=Designation.objects.all(),
        empty_label="Select Designation",
        widget=forms.Select(attrs={"class": "form-control"})
    )
    class Meta:
        model = EmployeeTransfer
        fields = [
            "employee",
            "new_department",
            "new_designation",
            "new_location",
            "reason",
        ]