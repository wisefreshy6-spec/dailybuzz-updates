from django import forms
from .models import UserSubmission


class UserSubmissionForm(forms.ModelForm):
    class Meta:
        model = UserSubmission
        fields = [
            'submission_type',
            'category',
            'title',
            'summary',
            'content',
            'cover_image',
            'video_file',
        ]
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 4}),
            'content': forms.Textarea(attrs={'rows': 8}),
        }

    def clean(self):
        cleaned_data = super().clean()
        submission_type = cleaned_data.get('submission_type')
        content = cleaned_data.get('content')
        video_file = cleaned_data.get('video_file')

        if submission_type == 'news' and not content:
            raise forms.ValidationError("News article content is required.")

        if submission_type == 'video' and not video_file:
            raise forms.ValidationError("Video file is required for video submissions.")

        return cleaned_data