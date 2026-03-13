from django import forms
from .models import SupportTicket


class SupportRequestForm(forms.Form):
    issue_type = forms.ChoiceField(choices=SupportTicket.ISSUE_CHOICES)
    subject = forms.CharField(max_length=200)
    message = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your issue clearly...'})
    )
    escalate_to_human = forms.BooleanField(required=False)


class SupportReplyForm(forms.Form):
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your reply...'})
    )
    attachment = forms.FileField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        message = cleaned_data.get('message')
        attachment = cleaned_data.get('attachment')

        if not message and not attachment:
            raise forms.ValidationError("Enter a message or attach a file.")
        return cleaned_data


class TicketStatusForm(forms.Form):
    status = forms.ChoiceField(choices=SupportTicket.STATUS_CHOICES)