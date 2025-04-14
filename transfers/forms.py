from django import forms
from .models import EmployeeTransfer, Employee
from base.models import Designation, Department  # Import Department model
from django.utils.translation import gettext_lazy as trans

class EmployeeTransferForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        empty_label="---Choose Employee---",
        widget=forms.Select(attrs={"class": "oh-select oh-select-2 select2-hidden-accessible"})
    )
    new_department = forms.ModelChoiceField(
        queryset=Department.objects.all(),  # Use Department model
        empty_label="---Choose New Department---",
        widget=forms.Select(attrs={"class": "oh-select oh-select-2 select2-hidden-accessible"})
    )
    new_designation = forms.ModelChoiceField(
        queryset=Designation.objects.all(),
        empty_label="---Choose New Designation---",
        widget=forms.Select(attrs={"class": "oh-select oh-select-2 select2-hidden-accessible"})
    )
    new_location = forms.CharField(
        label="New Location",
        widget=forms.TextInput(attrs={"class": "oh-input w-100", "placeholder": "New Location"})
    )
    reason = forms.CharField(
        label="Reason",
        widget=forms.Textarea(attrs={"class": "oh-input w-100", "placeholder": "Enter Reason for Transfer", "rows": 2, "cols": 40})
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            label = trans(field.label.title()) if field.label else ""
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({"class": "oh-input w-100", "placeholder": label})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "oh-select oh-select-2 select2-hidden-accessible"})
                field.empty_label = trans("---Choose {label}---").format(label=label)
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": "oh-input w-100", "placeholder": label, "rows": 2, "cols": 40})
