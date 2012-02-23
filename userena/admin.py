from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from guardian.admin import GuardedModelAdmin

from userena.models import UserenaSignup
from userena.utils import get_profile_model
from userena import settings as userena_settings


class UserenaSignupInline(admin.StackedInline):
    model = UserenaSignup
    max_num = 1

class UserenaAdmin(UserAdmin, GuardedModelAdmin):
    inlines = [UserenaSignupInline, ]
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'is_active', 'date_joined', )
    actions = ['accept_signup', 'reject_signup']
    
    def _loop_signup(self, request, queryset, action_func, action_string):
        """Performs the base operations for accepting or rejecting a user via the actions 
            selected in the change_list view. It counts the number users affected, calls passed in action_func, and posts
            a helpful message to user of admin."""
        count = 0
        for obj in queryset:
            
            #Getting userena_signup this way this prevents an exception from being raised if admin checks all users.
            #AnonymousUser, and the first superuser don't have the userena_signup property.
            try:
                userena_signup = obj.userena_signup
            except:
                userena_signup = None
            
            if userena_signup and userena_signup.activation_key == userena_settings.USERENA_PENDING_MODERATION:
                action_func(obj)
                obj.userena_signup.save()
                obj.save()
                count += 1
        if count == 1:
            msg = "1 user was %s." % action_string
        else:
            msg = "%s users were %s." % (count, action_string)
            if count == 0:
                msg += " Were the users already rejected, or have they failed to activate their accounts?"
        self.message_user(request, msg)
    
    
    def accept_signup(self, request, queryset):
        def _accept(obj):
            obj.userena_signup.activation_key = userena_settings.USERENA_ACTIVATED
            obj.userena_signup.send_approval_email()
            obj.is_active = True
        
        action_string = "enabled"
        self._loop_signup(request, queryset, _accept, action_string)
    accept_signup.short_description = _("Accept selected user signups.")
    
    def reject_signup(self, request, queryset):
        def _reject(obj):
            obj.userena_signup.activation_key = userena_settings.USERENA_ACTIVATION_REJECTED
            obj.userena_signup.send_rejection_email()
            obj.is_active = False
        
        action_string = "rejected"
        self._loop_signup(request, queryset, _reject, action_string)
    reject_signup.short_description = _("Reject selected user signups.")
   

    
admin.site.unregister(User)
admin.site.register(User, UserenaAdmin)
admin.site.register(get_profile_model())
