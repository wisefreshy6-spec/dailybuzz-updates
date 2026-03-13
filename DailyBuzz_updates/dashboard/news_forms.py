from django import forms
from .models import NewsPost


class NewsPostForm(forms.ModelForm):
    class Meta:
        model = NewsPost
        fields = [
            'title',
            'category',
            'editor_name',
            'summary',
            'content',
            'image',
            'is_published',
            'is_featured',
            'is_breaking',
            'show_in_carousel',
            'show_as_popup',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Enter news title'}),
            'editor_name': forms.TextInput(attrs={'placeholder': 'Editor / Author name'}),
            'summary': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Short summary'}),
            'content': forms.Textarea(attrs={'rows': 12, 'placeholder': 'Full news content'}),
        }