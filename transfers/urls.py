from django.urls import path
from .views import approved_transfer,rejected_transfer,cancelled_transfer,request_transfer,transfer_list,process_transfer

urlpatterns = [
    path("transfers/",transfer_list, name="transfer_list"),
    path("transfers/requests/", request_transfer, name = "request_transfer"),
    path("transfer/<int:transfer_id>/approved", approved_transfer, name= "approved_transfer"),
    path("transfer/<int:transfer_id>/cancelled",cancelled_transfer, name="cancelled_transfer"),
    path("transfer/<int:transfer_id>/rejected",rejected_transfer,name="rejected_transfer"),
    path("transfer/<int:transfer_id>/process",process_transfer,name="process_transfer"),
]
