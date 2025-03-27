"""transfers/sidebar.py"""

from django.contrib.auth.context_processors import PermWrapper
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.templatetags.basefilters import is_reportingmanager
from project.methods import (has_subordinates)

MENU = _("Transfer")
IMG_SRC = "images/ui/transfers.png"
ACCESSIBILITY = "transfers.sidebar.menu_accessibility"

SUBMENUS = [

    {
        "menu" : _("Transfer List"),
        "redirect": reverse("transfer_list"),
        "accessibility":"transfers.sidebar.menu_transfer_list"
    },
    {
        "menu": _("Transfer request"),
        "redirect": reverse("request_transfer"),
        "accessibility": "transfers.sidebar.menu_request_transfer"
    },
]


def menu_accessibility(request, _menu: str = "", user_perms: PermWrapper = [], *args, **kwargs) -> bool:
    user = request.user
    return (
        "transfers" in user_perms
        or user.has_perm("transfers.transfer_list")
        or has_subordinates(request)
        or is_reportingmanager(user)
    )


def menu_request_transfer(request, submenu, user_perms, *args, **kwargs):
    user = request.user
    return user.has_perm("transfers.transfer_list")


def menu_transfer_list(request, submenu, user_perms, *args, **kwargs):
    """Allows all employees to view their own transfer history"""
    return request.user.is_authenticated