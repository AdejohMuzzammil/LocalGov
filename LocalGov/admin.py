from django.contrib import admin
from . models import *

# Register your models here.
admin.site.register(ChairmanProfile)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Reply)
admin.site.register(ReplyToReply)
admin.site.register(State)
admin.site.register(LocalGovernment)
admin.site.register(UserProfile)
admin.site.register(StaffProfile)
admin.site.register(Subscription)
admin.site.register(SubscriptionPlan)
admin.site.register(StaffPost)
admin.site.register(StaffPostComment)
admin.site.register(StaffPostReply)
admin.site.register(StaffPostNestedReply)