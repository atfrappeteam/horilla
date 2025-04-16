from django import forms
from .models import EmployeeTransfer, Employee
from base.models import Designation, Department  # Import Department model
from django.utils.translation import gettext_lazy as trans
from django.contrib.auth.models import Group, User

class ReportingManagerChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        try:
            employee = Employee.objects.get(employee_user_id=obj)
            return f"{employee.employee_first_name} {employee.employee_last_name}".strip()
        except Employee.DoesNotExist:
            return obj.get_full_name() or obj.username





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

    new_reporting_manager = ReportingManagerChoiceField(
        queryset=User.objects.filter(groups__name="Reporting Manager"),
        label="Reporting Manager",
        widget=forms.Select(attrs={"class": "oh-select oh-select-2 select2-hidden-accessible"})
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
            "new_reporting_manager",
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)
        # cleaned_data already contains the Employee instance
        instance.new_reporting_manager = self.cleaned_data.get('new_reporting_manager')
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["new_department"].required = False
        self.fields["new_designation"].required = False
        self.fields["new_location"].required = False
        try:
            group = Group.objects.get(name="Reporting Manager")
            reporting_users = group.user_set.all()
        except Group.DoesNotExist:
            reporting_users = User.objects.none()

        self.fields['new_reporting_manager'].queryset = reporting_users

        for field_name, field in self.fields.items():
            label = trans(field.label.title()) if field.label else ""
            if isinstance(field.widget, forms.TextInput):
                field.widget.attrs.update({"class": "oh-input w-100", "placeholder": label})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({"class": "oh-select oh-select-2 select2-hidden-accessible"})
                if hasattr(field, "empty_label"):
                    field.empty_label = trans(f"---Choose {label}---")
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": "oh-input w-100", "placeholder": label, "rows": 2, "cols": 40})

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('new_reporting_manager')
        if user:
            try:
                employee = Employee.objects.get(employee_user_id=user)
                cleaned_data['new_reporting_manager'] = employee
            except Employee.DoesNotExist:
                self.add_error('new_reporting_manager', "Selected user does not have an employee profile.")
        return cleaned_data