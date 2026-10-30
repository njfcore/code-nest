from django import forms


class CommentForm(forms.Form):
    body = forms.CharField(
        max_length=1000,
        label='Comment',
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'placeholder': 'Write a comment...',
                'maxlength': '1000',
            }
        ),
    )

    def clean_body(self):
        body = self.cleaned_data['body'].strip()

        if not body:
            raise forms.ValidationError('Comment cannot be empty.')

        return body