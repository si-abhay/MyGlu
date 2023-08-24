from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from user.models import Profile, Post, Tag, Category
from .models import Grievance
from phonenumber_field.formfields import PhoneNumberField

class GrievanceForm(forms.ModelForm):
    complain_doctor = forms.ModelChoiceField(queryset=Profile.objects.filter(is_accepted=True))
    class Meta:
        model = Grievance
        fields = ['username', 'email', 'phone', 'complain_type', 'complain_doctor', 'complain']


class ProfileCreationForm(UserCreationForm):
    startup_idea = forms.CharField(widget=forms.TextInput)
    email = forms.CharField(widget=forms.TextInput)
    username = forms.CharField(widget=forms.TextInput)
    class Meta:
        model = Profile
        fields = ['username', 'email','startup_idea', 'password1', 'password2']

class RegistrationForm(forms.ModelForm):
    
    registered_address = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '1234 Main St'}))
    area_of_operation = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Locality'}))
    license_no = forms.CharField(widget=forms.TextInput)
    name = forms.CharField(widget=forms.TextInput)
    phone = PhoneNumberField(region='IN')
    service_tax_no = forms.CharField(widget=forms.TextInput)
    hospital = forms.CharField(widget=forms.TextInput)
    state = forms.CharField(widget=forms.Select(choices=[]))
    designation = forms.CharField(widget=forms.Select(choices=[]))
    district = forms.CharField(widget=forms.Select(choices=[]))
    

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['state'].widget.attrs['onchange'] = 'updateDistricts()'
        
        for field_name, field in self.fields.items():
            field.required = True

    class Meta:
        model = Profile
        fields = ['state','district','name','registered_address','area_of_operation', 'license_no', 'designation','phone', 'service_tax_no','hospital']   


class AccountUpdateForm(forms.ModelForm):
    designation = forms.CharField(widget=forms.Select(choices=[]))
    phone = PhoneNumberField(region='IN', widget=forms.TextInput(attrs={'placeholder': 'Phone Number'}))

    class Meta:
        model = Profile
        fields = ['email', 'designation','phone','hospital']

    def __init__(self, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)


    def clean_email(self):
        if self.is_valid():
            email = self.cleaned_data['email']
            try:
                account = Profile.objects.exclude(pk=self.instance.pk).get(email=email)
            except Profile.DoesNotExist:
                return email
            raise forms.ValidationError('Email "%s" is already in use.' % account.email) 
        
class BlogForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'tags']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['tags'].queryset = Tag.objects.all()
