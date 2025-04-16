from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from transfers.models import EmployeeTransfer

class Command(BaseCommand):
    help = "Assigns custom employee transfer permissions to groups"

    def handle(self, *args, **kwargs):
        ct = ContentType.objects.get_for_model(EmployeeTransfer)

        approve = Permission.objects.get(codename='can_approve_transfer', content_type=ct)
        reject = Permission.objects.get(codename='can_reject_transfer', content_type=ct)
        cancel = Permission.objects.get(codename='can_cancel_transfer', content_type=ct)

        rm_group, _ = Group.objects.get_or_create(name='Reporting Manager')
        rm_group.permissions.add(approve, reject)

        hrm_group, _ = Group.objects.get_or_create(name='HR Manager')
        hrm_group.permissions.add(cancel)

        self.stdout.write(self.style.SUCCESS("Permissions assigned to groups successfully."))

