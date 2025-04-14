from django.urls import path
from .views import *

urlpatterns = [
    path("transfers/",transfer_list, name="transfer_list"),
    path("transfers/requests/", request_transfer, name = "request_transfer"),
    path("transfer/<int:transfer_id>/approved", approved_transfer, name= "approved_transfer"),
    path("transfer/<int:transfer_id>/cancelled",cancelled_transfer, name="cancelled_transfer"),
    path("transfer/<int:transfer_id>/rejected",rejected_transfer,name="rejected_transfer"),
    path('transfer/mark-transferred/<int:transfer_id>/', mark_transferred, name='mark_transferred'),
    path('transfer/submitted-for-approval/<int:transfer_id>/', submit_transfer, name='submitted_for_approval'),

]
